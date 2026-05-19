import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Cache lưu tại thư mục app/ai/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(BASE_DIR, "model_cache.pkl")


def _build_product_text(product):
    """Ghép các trường đặc trưng của 1 sản phẩm thành 1 chuỗi văn bản."""
    huongs = " ".join([h.TenNhomHuong for h in product.nhom_huongs.all()])
    parts = [
        product.TenSanPham or "",
        product.MoTa_SanPham or "",
        product.PhongCach or "",
        product.MuaPhuHop or "",
        product.ThoiDiemSuDung or "",
        product.NongDo or "",
        product.DoTuoiPhuHop or "",
        huongs,
        product.id_ThuongHieu.TenThuongHieu if product.id_ThuongHieu else "",
        product.id_LoaiSanPham.TenLoaiSanPham if product.id_LoaiSanPham else "",
    ]
    return " ".join(filter(None, parts))


def build_and_cache():
    """
    Đọc toàn bộ sản phẩm từ DB, build ma trận TF-IDF cosine,
    lưu cache vào file pkl. Gọi 1 lần khi khởi động hoặc khi DB thay đổi.
    """
    # Import model ở đây để tránh circular import
    from app.models import SanPham

    products = list(
        SanPham.objects
        .select_related("id_ThuongHieu", "id_LoaiSanPham")
        .prefetch_related("nhom_huongs")
        .all()
    )

    if not products:
        return [], np.array([])

    ids = [p.id_SanPham for p in products]
    texts = [_build_product_text(p) for p in products]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(texts)
    sim_matrix = cosine_similarity(matrix)

    with open(CACHE_PATH, "wb") as f:
        pickle.dump({"ids": ids, "sim": sim_matrix}, f)

    print(f"[AI] Đã build cache: {len(ids)} sản phẩm → {CACHE_PATH}")
    return ids, sim_matrix


def _load_cache():
    """Đọc cache từ file pkl. Tự rebuild nếu chưa có."""
    if not os.path.exists(CACHE_PATH):
        return build_and_cache()
    with open(CACHE_PATH, "rb") as f:
        data = pickle.load(f)
    return data["ids"], data["sim"]


def get_similar_products(product_id, top_n=8):
    """
    Trả về danh sách id sản phẩm tương tự nhất với product_id.
    Không bao gồm chính sản phẩm đó.
    """
    ids, sim_matrix = _load_cache()

    if not ids or product_id not in ids:
        return []

    idx = ids.index(product_id)
    scores = list(enumerate(sim_matrix[idx]))
    # Sắp xếp giảm dần, bỏ chính nó (score = 1.0 với chính nó)
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    scores = [(i, s) for i, s in scores if ids[i] != product_id]
    top = scores[:top_n]

    return [ids[i] for i, _ in top]


def invalidate_cache():
    """Xóa cache để force rebuild lần sau. Gọi khi admin thêm/sửa sản phẩm."""
    if os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
        print("[AI] Cache đã được xóa, sẽ rebuild lần sau.")