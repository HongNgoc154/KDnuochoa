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


def _infer_gender(product) -> str:
    """
    Heuristic xác định giới tính phù hợp của sản phẩm dựa trên PhongCach
    (vì model SanPham/ThuocTinh không có field giới tính riêng).
    Trả về: 'nam' | 'nu' | 'unisex'
    """
    phong_cach = (product.PhongCach or '').lower()
    ten_sp = (product.TenSanPham or '').lower()
    combined = f"{ten_sp} {phong_cach}"

    if 'nam tính' in phong_cach or 'pour homme' in combined or ' for men' in combined:
        return 'nam'
    if 'nữ tính' in phong_cach:
        return 'nu'
    # Các từ mô tả thường gặp ở dòng nữ
    _FEMALE_HINTS = ['ngọt ngào', 'quyến rũ', 'dịu dàng', 'sang trọng', 'trẻ trung']
    if any(hint in phong_cach for hint in _FEMALE_HINTS):
        return 'nu'
    return 'unisex'

def _build_chunks():
    """
    Đọc toàn bộ sản phẩm + bài viết từ DB,
    chuyển thành danh sách các đoạn văn bản (chunks).
    Mỗi chunk = 1 đơn vị kiến thức mà chatbot có thể dùng.
    """
    import re
    from app.models import SanPham, BaiViet, SanPhamNhomHuong

    chunks = []

    # ── Sản phẩm ──
    products = SanPham.objects.select_related(
        "id_ThuongHieu", "id_LoaiSanPham"
    ).prefetch_related("nhom_huongs").all()

    sp_count = products.count()
    print(f"[KB] Đọc được {sp_count} sản phẩm từ DB")  # ← thêm dòng này

    for p in products:
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

        gender = _infer_gender(p)
        gender_label = {'nam': 'Nam', 'nu': 'Nữ', 'unisex': 'Unisex'}[gender]
        text = text + f" Dành cho: {gender_label}."
        chunks.append({
            "type":  "product",
            "id":    p.id_SanPham,
            "name":  p.TenSanPham,
            "brand": p.id_ThuongHieu.TenThuongHieu if p.id_ThuongHieu else "",
            "gender": gender,
            "text":  text,
        })

    # ── Bài viết ──
    bv_list = BaiViet.objects.all()
    bv_count = bv_list.count()
    print(f"[KB] Đọc được {bv_count} bài viết từ DB")  # ← thêm dòng này

    for b in bv_list:
        noi_dung = re.sub(r'<[^>]+>', ' ', b.NoiDung or '')
        noi_dung = ' '.join(noi_dung.split())[:500]
        chunks.append({
            "type":  "article",
            "id":    b.id_BaiViet,
            "name":  b.TieuDe,
            "brand": "",
            "text":  f"Bài viết: {b.TieuDe}. Nội dung: {noi_dung}",
        })

    print(f"[KB] Tổng chunks: {len(chunks)} ({sp_count} SP + {bv_count} BV)")
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


def retrieve(query: str, top_k: int = 5, gender: str | None = None):
    """
    Nhận câu hỏi, trả về top_k chunks liên quan nhất.
    Nếu gender được chỉ định ('nam'/'nu'), ưu tiên lọc sản phẩm
    có chunk['gender'] khớp ('nam'/'nu') hoặc 'unisex'.
    Nếu sau lọc không đủ kết quả, bổ sung từ kết quả gốc (không lọc).
    """
    import faiss

    if not os.path.exists(INDEX_PATH):
        print("[KB] Chưa có index → đang rebuild...")
        rebuild_index()

    index  = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)

    model  = _get_model()
    q_vec  = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_vec)

    # Lấy nhiều hơn nếu cần filter theo gender, để có đủ ứng viên
    search_k = top_k * 4 if gender else top_k
    search_k = min(search_k, len(chunks))

    scores, indices = index.search(q_vec, search_k)

    all_results = []
    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(chunks):
            chunk = dict(chunks[idx])
            chunk["score"] = float(score)
            all_results.append(chunk)

    if not gender:
        return all_results[:top_k]

    # Lọc theo gender (giữ unisex cho mọi giới tính)
    filtered = [
        c for c in all_results
        if c["type"] != "product" or c.get("gender") in (gender, "unisex")
    ]

    if len(filtered) >= top_k:
        return filtered[:top_k]

    # Không đủ -> bổ sung từ kết quả gốc (chưa lọc), tránh thiếu
    for c in all_results:
        if c not in filtered:
            filtered.append(c)
            if len(filtered) >= top_k:
                break

    return filtered[:top_k]

def get_chunks_by_ids(product_ids: list[int]) -> list[dict]:
    """
    Lấy chunk text cho danh sách product_id cụ thể.
    Dùng cho Personalized Recommendation Tool — khi đã biết
    chính xác ID sản phẩm cần gợi ý (từ personalize.py),
    cần lấy lại nội dung mô tả để AI giải thích.
    """
    if not os.path.exists(CHUNKS_PATH):
        return []
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)
    id_set = set(product_ids)
    return [c for c in chunks if c["type"] == "product" and c["id"] in id_set]