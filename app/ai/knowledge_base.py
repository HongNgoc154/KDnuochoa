import os
import pickle
import numpy as np

import django
from django.conf import settings as django_settings

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))

# Dùng đường dẫn ASCII thuần để tránh lỗi FAISS với ký tự tiếng Việt
_AI_DIR     = os.path.join(os.path.dirname(BASE_DIR), "ai_data")
os.makedirs(_AI_DIR, exist_ok=True)

INDEX_PATH  = os.path.join(_AI_DIR, "faiss.index")
CHUNKS_PATH = os.path.join(_AI_DIR, "chunks.pkl")

# Model đa ngôn ngữ, hiểu tiếng Việt tốt, nhẹ (~120MB)
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model = None   # lazy-load: chỉ load khi cần, tránh chiếm RAM khi start server


def _get_model():
    """Load model 1 lần duy nhất, tái sử dụng cho mọi request."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("[KB] Đang load embedding model lần đầu...")
        _model = SentenceTransformer(MODEL_NAME)
        print("[KB] Model sẵn sàng.")
    return _model


def _build_chunks():
    """
    Đọc toàn bộ sản phẩm + bài viết từ DB,
    chuyển thành danh sách các đoạn văn bản (chunks).
    Mỗi chunk = 1 đơn vị kiến thức mà chatbot có thể dùng.
    """
    import re
    from app.models import SanPham, BaiViet, SanPhamNhomHuong

    chunks = []

    # ── Sản phẩm ──────────────────────────────────────────────
    products = SanPham.objects.select_related(
        "id_ThuongHieu", "id_LoaiSanPham"
    ).prefetch_related("nhom_huongs").all()

    for p in products:
        # Ghép nhóm hương kèm vai trò (Top/Heart/Base Notes)
        huong_parts = []
        for snh in SanPhamNhomHuong.objects.select_related(
            "id_NhomHuong"
        ).filter(id_SanPham=p):
            ten = snh.id_NhomHuong.TenNhomHuong
            vai = snh.VaiTroHuong
            huong_parts.append(f"{ten} ({vai})" if vai else ten)

        text = (
            f"Tên sản phẩm: {p.TenSanPham}. "
            f"Thương hiệu: {p.id_ThuongHieu.TenThuongHieu if p.id_ThuongHieu else ''}. "
            f"Danh mục: {p.id_LoaiSanPham.TenLoaiSanPham if p.id_LoaiSanPham else ''}. "
            f"Nhóm hương: {', '.join(huong_parts) or 'Chưa cập nhật'}. "
            f"Nồng độ: {p.NongDo or 'Chưa cập nhật'}. "
            f"Phong cách: {p.PhongCach or 'Chưa cập nhật'}. "
            f"Mùa phù hợp: {p.MuaPhuHop or 'Chưa cập nhật'}. "
            f"Thời điểm dùng: {p.ThoiDiemSuDung or 'Chưa cập nhật'}. "
            f"Độ tuổi: {p.DoTuoiPhuHop or 'Chưa cập nhật'}. "
            f"Xuất xứ: {p.XuatXu or 'Chưa cập nhật'}. "
            f"Mô tả: {(p.MoTa_SanPham or '')[:300]}"
        )
        chunks.append({
            "type":  "product",
            "id":    p.id_SanPham,
            "name":  p.TenSanPham,
            "brand": p.id_ThuongHieu.TenThuongHieu if p.id_ThuongHieu else "",
            "text":  text,
        })

    # ── Bài viết ──────────────────────────────────────────────
    for b in BaiViet.objects.all():
        # Xóa HTML tags trong nội dung bài viết
        noi_dung = re.sub(r'<[^>]+>', ' ', b.NoiDung or '')
        noi_dung = ' '.join(noi_dung.split())[:500]
        chunks.append({
            "type":  "article",
            "id":    b.id_BaiViet,
            "name":  b.TieuDe,
            "brand": "",
            "text":  f"Bài viết: {b.TieuDe}. Nội dung: {noi_dung}",
        })

    return chunks


def rebuild_index():
    """
    Build FAISS index từ toàn bộ DB.
    Chạy 1 lần offline. Lưu 2 file: faiss.index + chunks.pkl
    """
    import faiss

    chunks = _build_chunks()
    if not chunks:
        print("[KB] Không có dữ liệu.")
        return 0

    model  = _get_model()
    texts  = [c["text"] for c in chunks]

    print(f"[KB] Đang encode {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=16,
        convert_to_numpy=True
    )
    embeddings = embeddings.astype("float32")

    # Normalize để dùng Inner Product = cosine similarity
    faiss.normalize_L2(embeddings)

    # IndexFlatIP = Flat index, Inner Product (cosine sau normalize)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print(f"[KB] Xong! {len(chunks)} chunks → {INDEX_PATH}")
    return len(chunks)


def retrieve(query: str, top_k: int = 5):
    """
    Nhận câu hỏi, trả về top_k chunks liên quan nhất.
    Đây là bước "Retrieve" trong kiến trúc RAG.
    """
    import faiss

    # Tự rebuild nếu chưa có index
    if not os.path.exists(INDEX_PATH):
        print("[KB] Chưa có index → đang rebuild...")
        rebuild_index()

    index  = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)

    model  = _get_model()
    q_vec  = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_vec)

    scores, indices = index.search(q_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(chunks):
            chunk = dict(chunks[idx])
            chunk["score"] = float(score)
            results.append(chunk)
    return results