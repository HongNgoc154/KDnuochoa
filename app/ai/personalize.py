"""
Gợi ý cá nhân hóa dựa trên hành vi người dùng.
Kết hợp:
  - Content-based filtering (Giai đoạn 1 — cosine similarity)
  - Behavior-based scoring (mua, yêu thích, đánh giá)
"""
import os
import pickle
import numpy as np

# Trọng số hành vi — có thể điều chỉnh
WEIGHT_PURCHASE  = 5.0   # Đã mua → quan trọng nhất
WEIGHT_FAVORITE  = 3.0   # Đã yêu thích
WEIGHT_RATING_5  = 4.0   # Đánh giá 5 sao
WEIGHT_RATING_4  = 2.0   # Đánh giá 4 sao
WEIGHT_RATING_LOW = -1.0  # Đánh giá 1-2 sao → giảm ưu tiên


def _get_user_behavior(account_id: int) -> dict:
    """
    Đọc hành vi người dùng từ DB.
    Trả về dict: {product_id: score}
    """
    from app.models import (
        ChiTietDonHang, YeuThich, DanhGia,
        DonHang, KhachHang, BienThe
    )

    scores = {}  # {product_id: float}

    # ── 1. Lịch sử mua hàng ───────────────────────────────
    # Tìm KhachHang từ TaiKhoan
    customer = KhachHang.objects.filter(
        id_TaiKhoan_id=account_id
    ).first()

    if customer:
        orders = DonHang.objects.filter(
            id_KhachHang=customer,
            TrangThai__in=['Hoàn tất', 'Đang giao',
                           'Đã xác nhận', 'Khách đã nhận hàng']
        ).values_list('id_DonHang', flat=True)

        if orders:
            details = ChiTietDonHang.objects.filter(
                id_DonHang_id__in=list(orders)
            ).select_related('id_BienThe__id_SanPham')

            for d in details:
                if d.id_BienThe and d.id_BienThe.id_SanPham_id:
                    pid = d.id_BienThe.id_SanPham_id
                    qty = int(d.SoLuong or 1)
                    # Mua nhiều lần → score cao hơn (giới hạn tối đa x3)
                    scores[pid] = scores.get(pid, 0) + WEIGHT_PURCHASE * min(qty, 3)

    # ── 2. Danh sách yêu thích ────────────────────────────
    favorites = YeuThich.objects.filter(
        id_TaiKhoan_id=account_id
    ).values_list('id_SanPham_id', flat=True)

    for pid in favorites:
        scores[pid] = scores.get(pid, 0) + WEIGHT_FAVORITE

    # ── 3. Đánh giá sản phẩm ─────────────────────────────
    reviews = DanhGia.objects.filter(
        id_TaiKhoan_id=account_id,
        parent_id__isnull=True,
        SoSao__isnull=False,
    ).values('id_SanPham_id', 'SoSao')

    for rv in reviews:
        pid   = rv['id_SanPham_id']
        stars = int(rv['SoSao'] or 0)
        if stars >= 5:
            w = WEIGHT_RATING_5
        elif stars >= 4:
            w = WEIGHT_RATING_4
        elif stars <= 2:
            w = WEIGHT_RATING_LOW
        else:
            w = 0
        scores[pid] = scores.get(pid, 0) + w

    return scores


def _get_content_similar(seed_product_ids: list, top_n: int = 20) -> dict:
    """
    Dùng FAISS index từ Giai đoạn 1 để tìm sản phẩm tương tự
    với các sản phẩm mà user đã tương tác.
    Trả về {product_id: similarity_score}
    """
    from app.ai.knowledge_base import INDEX_PATH, CHUNKS_PATH, _get_model
    import faiss

    if not os.path.exists(INDEX_PATH):
        return {}

    index  = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, 'rb') as f:
        chunks = pickle.load(f)

    # Chỉ lấy chunks là sản phẩm
    product_chunks = [c for c in chunks if c['type'] == 'product']
    chunk_ids = [c['id'] for c in product_chunks]

    if not chunk_ids:
        return {}

    model = _get_model()
    similar_scores = {}  # {product_id: max_similarity}

    for seed_id in seed_product_ids[:5]:  # Chỉ lấy tối đa 5 seed
        if seed_id not in chunk_ids:
            continue
        idx = chunk_ids.index(seed_id)

        # Lấy vector của seed product
        seed_vec = np.zeros((1, index.d), dtype='float32')
        index.reconstruct(idx, seed_vec[0])

        # Tìm top_n sản phẩm tương tự
        scores, indices = index.search(seed_vec, top_n + 1)

        for score, i in zip(scores[0], indices[0]):
            if 0 <= i < len(product_chunks):
                pid = product_chunks[i]['id']
                if pid != seed_id:
                    # Giữ score cao nhất nếu xuất hiện nhiều lần
                    existing = similar_scores.get(pid, 0)
                    similar_scores[pid] = max(existing, float(score))

    return similar_scores


def get_personalized_recommendations(account_id: int, top_n: int = 8) -> list:
    """
    Hàm chính — trả về danh sách product_id được gợi ý cá nhân hóa.

    Thuật toán Hybrid:
    1. Lấy hành vi user (đã mua, yêu thích, đánh giá)
    2. Tìm sản phẩm tương tự với sản phẩm user đã tương tác (content-based)
    3. Kết hợp 2 điểm: hybrid_score = behavior_score * 0.4 + similarity * 0.6
    4. Loại bỏ sản phẩm user đã mua
    5. Trả về top_n sản phẩm điểm cao nhất
    """
    # Bước 1: Hành vi
    behavior_scores = _get_user_behavior(account_id)

    if not behavior_scores:
        # User chưa có hành vi → fallback về gợi ý phổ biến
        return _get_popular_products(top_n)

    interacted_ids = list(behavior_scores.keys())

    # Bước 2: Content-based similarity
    similarity_scores = _get_content_similar(interacted_ids, top_n=20)

    # Bước 3: Kết hợp hybrid score
    all_product_ids = set(similarity_scores.keys())

    # Normalize behavior scores về [0, 1]
    max_b = max(behavior_scores.values()) if behavior_scores else 1
    max_s = max(similarity_scores.values()) if similarity_scores else 1

    hybrid = {}
    for pid in all_product_ids:
        b_score = behavior_scores.get(pid, 0) / max_b  # normalize
        s_score = similarity_scores.get(pid, 0) / max_s  # normalize
        hybrid[pid] = b_score * 0.4 + s_score * 0.6

    # Bước 4: Loại bỏ sản phẩm đã mua (chỉ loại những gì score ≥ WEIGHT_PURCHASE)
    purchased = {
        pid for pid, sc in behavior_scores.items()
        if sc >= WEIGHT_PURCHASE
    }
    filtered = {
        pid: sc for pid, sc in hybrid.items()
        if pid not in purchased
    }

    # Bước 5: Sắp xếp và lấy top_n
    sorted_pids = sorted(filtered, key=lambda x: filtered[x], reverse=True)
    return sorted_pids[:top_n]


def _get_popular_products(top_n: int = 8) -> list:
    """
    Fallback: Gợi ý sản phẩm phổ biến nhất dựa trên số lượt mua.
    Dùng khi user chưa có hành vi.
    """
    from django.db.models import Count
    from app.models import ChiTietDonHang

    popular = (
        ChiTietDonHang.objects
        .filter(id_BienThe__id_SanPham__isnull=False)
        .values('id_BienThe__id_SanPham')
        .annotate(total=Count('id_ChiTietDon'))
        .order_by('-total')[:top_n]
    )
    return [p['id_BienThe__id_SanPham'] for p in popular]