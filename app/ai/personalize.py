"""
app/ai/personalize.py  (NÂNG CẤP)
====================================
Module cá nhân hóa gợi ý sản phẩm — Hybrid AI.

┌─────────────────┬────────────────────────────────────────────────┐
│ Guest User      │ Session-based + Content-based + Trending       │
│ Registered User │ Hybrid (Collaborative + Content + Behavioral)  │
└─────────────────┴────────────────────────────────────────────────┘
"""
from __future__ import annotations
import os
import pickle
import numpy as np

# ── Trọng số hành vi ──────────────────────────────────────────────
WEIGHT_PURCHASE     = 5.0
WEIGHT_FAVORITE     = 3.0
WEIGHT_RATING_5     = 4.0
WEIGHT_RATING_4     = 2.0
WEIGHT_RATING_LOW   = -1.0
WEIGHT_VIEW_LONG    = 1.5    # xem > 60 giây
WEIGHT_VIEW_SHORT   = 0.5    # xem < 60 giây
WEIGHT_VIEW_REPEAT  = 0.8    # xem nhiều lần


# ════════════════════════════════════════════════════════════════
# A. GUEST RECOMMENDATION — Session-based
# ════════════════════════════════════════════════════════════════

def get_guest_recommendations(request, current_product_id=None, top_n=8):
    from app.ai.recently_viewed import guest_get_viewed

    viewed_ids = guest_get_viewed(request, exclude_id=current_product_id)

    if not viewed_ids and not current_product_id:
        result = _get_trending_products(top_n)
    else:
        seed_ids = []
        if current_product_id:
            seed_ids.append(current_product_id)
        seed_ids.extend(viewed_ids[:4])

        similar = _get_content_similar(seed_ids, top_n=top_n * 2)

        exclude = set(viewed_ids)
        if current_product_id:
            exclude.add(current_product_id)

        result = [pid for pid in sorted(similar, key=similar.get, reverse=True)
                  if pid not in exclude][:top_n]

        # Bổ sung từ trending nếu thiếu
        if len(result) < top_n:
            trending = _get_trending_products(top_n)
            for pid in trending:
                if pid not in exclude and pid not in result:
                    result.append(pid)
                    if len(result) >= top_n:
                        break

        # ✅ ĐÚNG — fallback cuối, sau tất cả các bước
        if not result:
            from app.models import SanPham
            result = list(
                SanPham.objects
                .exclude(id_SanPham=current_product_id or 0)
                .values_list('id_SanPham', flat=True)[:top_n]
            )

    # ── MỚI: Lọc theo gender trong session profile (nếu có) ──
    gender_pref = request.session.get('guest_ai_profile', {}).get('gender')
    if gender_pref and result:
        result = _filter_products_by_gender(result, gender_pref, top_n)

    return result


# ════════════════════════════════════════════════════════════════
# B. REGISTERED USER — Hybrid Recommendation
# ════════════════════════════════════════════════════════════════

def get_personalized_recommendations(account_id: int, top_n: int = 8,
                                      request=None) -> list[int]:
    """
    Hàm chính — Hybrid AI cho Registered User.
    Kết hợp: behavior score + content similarity + AI profile
    """
    behavior_scores = _get_user_behavior_extended(account_id)

    if not behavior_scores:
        # Fallback: dùng AI profile nếu có
        profile_recs = _recommend_from_profile(account_id, top_n)
        if profile_recs:
            return profile_recs
        return _get_popular_products(top_n)

    interacted_ids = list(behavior_scores.keys())

    # Content-based similarity từ FAISS
    similarity_scores = _get_content_similar(interacted_ids, top_n=top_n * 3)

    # Hybrid score
    max_b = max(behavior_scores.values()) if behavior_scores else 1
    max_s = max(similarity_scores.values()) if similarity_scores else 1

    hybrid: dict[int, float] = {}
    for pid in set(similarity_scores.keys()):
        b = behavior_scores.get(pid, 0) / max_b
        s = similarity_scores.get(pid, 0) / max_s
        hybrid[pid] = b * 0.4 + s * 0.6

    # Boost theo AI profile
    profile = _load_ai_profile(account_id)
    if profile:
        hybrid = _apply_profile_boost(hybrid, profile, account_id)

    # Loại sản phẩm đã mua nhiều
    purchased = {pid for pid, sc in behavior_scores.items()
                 if sc >= WEIGHT_PURCHASE}
    filtered = {pid: sc for pid, sc in hybrid.items()
                if pid not in purchased}

    sorted_pids = sorted(filtered, key=lambda x: filtered[x], reverse=True)

    # Cập nhật profile ngầm sau mỗi lần recommend
    _async_update_profile(account_id, behavior_scores, interacted_ids)

    return sorted_pids[:top_n]


# ════════════════════════════════════════════════════════════════
# C. SIMILAR PRODUCTS — cho trang chi tiết sản phẩm
# ════════════════════════════════════════════════════════════════

def get_similar_products_personalized(product_id: int, account_id: int | None,
                                       top_n: int = 8) -> list[int]:
    """
    Sản phẩm tương tự — cá nhân hóa nếu có account.
    Guest: chỉ dùng content similarity
    Registered: kết hợp similarity + preference profile
    """
    from app.ai.recommender import get_similar_products as content_similar

    # Base: content-based similar
    base = content_similar(product_id, top_n=top_n * 2)

    if not account_id:
        return base[:top_n]

    # Registered: boost theo profile
    profile = _load_ai_profile(account_id)
    if not profile:
        return base[:top_n]

    scored = {}
    for i, pid in enumerate(base):
        # Điểm mặc định theo thứ tự (cao hơn = giống hơn)
        scored[pid] = 1.0 - (i / len(base))

    scored = _apply_profile_boost(scored, profile, account_id)
    return sorted(scored, key=scored.get, reverse=True)[:top_n]


# ════════════════════════════════════════════════════════════════
# D. AI USER PROFILE — học & cập nhật
# ════════════════════════════════════════════════════════════════

def _load_ai_profile(account_id: int):
    """Load AIUserProfile từ DB."""
    try:
        from app.models import AIUserProfile
        return AIUserProfile.objects.filter(
            id_TaiKhoan_id=account_id
        ).first()
    except Exception:
        return None


def _apply_profile_boost(scored: dict, profile, account_id: int) -> dict:
    """
    Boost điểm sản phẩm phù hợp với AI profile của user.
    """
    from app.models import SanPham, SanPhamNhomHuong

    if not scored:
        return scored

    fav_brands  = profile.get_thuong_hieu() if profile else []
    fav_scents  = profile.get_nhom_mua()    if profile else []
    pref_gender = profile.GioiTinhUuTien or ''
    price_min   = float(profile.GiaMin or 0)
    price_max   = float(profile.GiaMax or 99_999_999)

    pids = list(scored.keys())
    products = SanPham.objects.filter(id_SanPham__in=pids).select_related(
        'id_ThuongHieu', 'id_LoaiSanPham'
    ).prefetch_related('nhom_huongs')

    product_map = {p.id_SanPham: p for p in products}

    for pid, score in list(scored.items()):
        p = product_map.get(pid)
        if not p:
            continue

        boost = 0.0

        # Thương hiệu yêu thích
        brand = p.id_ThuongHieu.TenThuongHieu if p.id_ThuongHieu else ''
        if brand and brand in fav_brands:
            boost += 0.3

        # Nhóm mùi yêu thích
        sp_scents = [h.TenNhomHuong for h in p.nhom_huongs.all()]
        for sc in sp_scents:
            if sc in fav_scents:
                boost += 0.2
                break

        scored[pid] = score + boost * profile.ConfidenceScore

    return scored


def _async_update_profile(account_id: int, behavior_scores: dict,
                           interacted_ids: list) -> None:
    """
    Cập nhật AI profile trong background dựa trên hành vi mới nhất.
    Được gọi sau mỗi lần recommend — không block response.
    """
    try:
        from app.models import AIUserProfile, SanPham, SanPhamNhomHuong, BienThe
        import collections

        products = SanPham.objects.filter(
            id_SanPham__in=interacted_ids
        ).select_related('id_ThuongHieu').prefetch_related('nhom_huongs')

        brand_count: dict[str, float] = collections.defaultdict(float)
        scent_count: dict[str, float] = collections.defaultdict(float)
        prices = []

        for p in products:
            w = behavior_scores.get(p.id_SanPham, 1.0)
            brand = p.id_ThuongHieu.TenThuongHieu if p.id_ThuongHieu else None
            if brand:
                brand_count[brand] += w

            for h in p.nhom_huongs.all():
                scent_count[h.TenNhomHuong] += w

            # Lấy giá từ biến thể đầu tiên
            bt = BienThe.objects.filter(id_SanPham=p).first()
            if bt and bt.GiaBan:
                prices.append(float(bt.GiaBan) * w)

        # Top brands + scents
        top_brands = [k for k, _ in sorted(
            brand_count.items(), key=lambda x: x[1], reverse=True)[:5]]
        top_scents = [k for k, _ in sorted(
            scent_count.items(), key=lambda x: x[1], reverse=True)[:5]]

        # Weighted average price range
        total_w = sum(behavior_scores.values()) or 1
        if prices:
            avg_price = sum(prices) / total_w
            price_min = avg_price * 0.7
            price_max = avg_price * 1.5
        else:
            price_min = price_max = None

        # Confidence tăng theo số lần cập nhật (max 1.0)
        profile, created = AIUserProfile.objects.get_or_create(
            id_TaiKhoan_id=account_id
        )

        profile.set_thuong_hieu(top_brands)
        profile.set_nhom_mua(top_scents)
        if price_min:
            profile.GiaMin = price_min
            profile.GiaMax = price_max
        profile.SoLanCapNhat += 1
        profile.ConfidenceScore = min(
            1.0, profile.SoLanCapNhat / 20.0
        )
        profile.save()

    except Exception as e:
        # Không crash main flow
        import traceback
        traceback.print_exc()


def _recommend_from_profile(account_id: int, top_n: int) -> list[int]:
    """
    Gợi ý dựa thuần túy vào AI profile (khi chưa có behavior).
    Dùng khi user mới đăng ký nhưng đã có profile từ chatbot.
    """
    profile = _load_ai_profile(account_id)
    if not profile or profile.ConfidenceScore < 0.1:
        return []

    from app.models import SanPham, SanPhamNhomHuong, BienThe
    from django.db.models import Q

    fav_scents  = profile.get_nhom_mua()
    fav_brands  = profile.get_thuong_hieu()

    qs = SanPham.objects.all()
    filters = Q()

    if fav_brands:
        filters |= Q(id_ThuongHieu__TenThuongHieu__in=fav_brands)
    if fav_scents:
        filters |= Q(nhom_huongs__TenNhomHuong__in=fav_scents)

    if filters:
        qs = qs.filter(filters).distinct()

    return list(qs.values_list('id_SanPham', flat=True)[:top_n])


# ════════════════════════════════════════════════════════════════
# E. INTERNAL HELPERS
# ════════════════════════════════════════════════════════════════

def _get_user_behavior_extended(account_id: int) -> dict:
    """
    Hành vi đầy đủ: mua + yêu thích + đánh giá + lịch sử xem.
    Nâng cấp so với version cũ (thêm viewed history).
    """
    from app.models import (
        ChiTietDonHang, YeuThich, DanhGia,
        DonHang, KhachHang, BienThe, LichSuXemSanPham
    )

    scores: dict[int, float] = {}

    # ── 1. Mua hàng ───────────────────────────────────────────
    customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
    if customer:
        orders = DonHang.objects.filter(
            id_KhachHang=customer,
            TrangThai__in=['Hoàn tất', 'Đang giao', 'Đã xác nhận',
                           'Khách đã nhận hàng']
        ).values_list('id_DonHang', flat=True)
        if orders:
            for d in ChiTietDonHang.objects.filter(
                id_DonHang_id__in=list(orders)
            ).select_related('id_BienThe__id_SanPham'):
                if d.id_BienThe and d.id_BienThe.id_SanPham_id:
                    pid = d.id_BienThe.id_SanPham_id
                    qty = int(d.SoLuong or 1)
                    scores[pid] = scores.get(pid, 0) + WEIGHT_PURCHASE * min(qty, 3)

    # ── 2. Yêu thích ──────────────────────────────────────────
    for pid in YeuThich.objects.filter(
        id_TaiKhoan_id=account_id
    ).values_list('id_SanPham_id', flat=True):
        scores[pid] = scores.get(pid, 0) + WEIGHT_FAVORITE

    # ── 3. Đánh giá ───────────────────────────────────────────
    for rv in DanhGia.objects.filter(
        id_TaiKhoan_id=account_id,
        parent_id__isnull=True,
        SoSao__isnull=False,
    ).values('id_SanPham_id', 'SoSao'):
        pid   = rv['id_SanPham_id']
        stars = int(rv['SoSao'] or 0)
        w = (WEIGHT_RATING_5 if stars >= 5
             else WEIGHT_RATING_4 if stars >= 4
             else WEIGHT_RATING_LOW if stars <= 2
             else 0)
        scores[pid] = scores.get(pid, 0) + w

    # ── 4. Lịch sử xem (MỚI) ─────────────────────────────────
    for ls in LichSuXemSanPham.objects.filter(
        id_TaiKhoan_id=account_id
    ).values('id_SanPham_id', 'ThoiGianXem', 'SoLanXem'):
        pid     = ls['id_SanPham_id']
        sec     = ls['ThoiGianXem'] or 0
        repeats = ls['SoLanXem'] or 1

        w = WEIGHT_VIEW_LONG if sec >= 60 else WEIGHT_VIEW_SHORT
        w += (repeats - 1) * WEIGHT_VIEW_REPEAT

        # Không tính nếu đã mua (tránh double boost)
        if pid not in scores or scores[pid] < WEIGHT_PURCHASE:
            scores[pid] = scores.get(pid, 0) + w

    return scores


# ── Cache toàn cục, chỉ load 1 lần ──
_FAISS_INDEX = None
_CHUNKS = None
_CHUNK_IDS = None

def _load_faiss_cache():
    global _FAISS_INDEX, _CHUNKS, _CHUNK_IDS
    if _FAISS_INDEX is not None:
        return _FAISS_INDEX, _CHUNKS, _CHUNK_IDS

    from app.ai.knowledge_base import INDEX_PATH, CHUNKS_PATH
    import faiss
    import pickle

    if not os.path.exists(INDEX_PATH):
        return None, None, None

    _FAISS_INDEX = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, 'rb') as f:
        _CHUNKS = pickle.load(f)
    _CHUNK_IDS = [c['id'] for c in _CHUNKS if c['type'] == 'product']
    return _FAISS_INDEX, _CHUNKS, _CHUNK_IDS

def invalidate_faiss_cache():
    """Xóa cache để lần gọi tiếp theo load lại FAISS index mới."""
    global _FAISS_INDEX, _CHUNKS, _CHUNK_IDS
    _FAISS_INDEX = None
    _CHUNKS = None
    _CHUNK_IDS = None

def _get_content_similar(seed_product_ids: list, top_n: int = 20) -> dict:
    """Dùng FAISS index (đã cache RAM) tìm SP tương tự với seed list."""
    from app.ai.knowledge_base import _get_model

    index, chunks, chunk_ids = _load_faiss_cache()
    if index is None:
        return {}

    product_chunks = [c for c in chunks if c['type'] == 'product']

    if not chunk_ids:
        return {}

    model          = _get_model()
    similar_scores: dict[int, float] = {}

    for seed_id in seed_product_ids[:5]:
        if seed_id not in chunk_ids:
            continue
        idx = chunk_ids.index(seed_id)

        seed_vec = np.zeros((1, index.d), dtype='float32')
        index.reconstruct(idx, seed_vec[0])

        scores_arr, indices = index.search(seed_vec, top_n + 1)

        for score, i in zip(scores_arr[0], indices[0]):
            if 0 <= i < len(product_chunks):
                pid = product_chunks[i]['id']
                if pid != seed_id:
                    similar_scores[pid] = max(
                        similar_scores.get(pid, 0), float(score)
                    )

    return similar_scores


def _get_popular_products(top_n: int = 8) -> list[int]:
    """Fallback: sản phẩm phổ biến nhất theo lượt mua."""
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


def _get_trending_products(top_n: int = 8) -> list[int]:
    """
    Trending: sản phẩm được xem nhiều nhất trong 7 ngày.
    Fallback về popular nếu không có dữ liệu.
    """
    from django.utils import timezone
    from django.db.models import Count
    from datetime import timedelta
    from app.models import LichSuXemSanPham, AIRecommendClick

    since = timezone.now() - timedelta(days=7)

    # Trending theo lượt xem
    trending = list(
        LichSuXemSanPham.objects
        .filter(NgayXem__gte=since)
        .values('id_SanPham_id')
        .annotate(views=Count('id_LichSu'))
        .order_by('-views')
        .values_list('id_SanPham_id', flat=True)[:top_n]
    )

    if len(trending) >= top_n:
        return trending

    # Bổ sung từ AI click tracking
    clicked = list(
        AIRecommendClick.objects
        .filter(NgayClick__gte=since)
        .values('id_SanPham_id')
        .annotate(clicks=Count('id_Click'))
        .order_by('-clicks')
        .values_list('id_SanPham_id', flat=True)[:top_n]
    )

    result = list(dict.fromkeys(trending + clicked))[:top_n]

    if len(result) < top_n:
        result += [p for p in _get_popular_products(top_n)
                   if p not in result]

    return result[:top_n]


# ════════════════════════════════════════════════════════════════
# F. GENDER FILTER — hỗ trợ lọc gợi ý theo giới tính ưa thích
# ════════════════════════════════════════════════════════════════

def _filter_products_by_gender(product_ids: list, gender: str, top_n: int) -> list:
    """
    Lọc product_id theo gender, dùng field 'gender' đã được tính sẵn
    trong chunks (xem _infer_gender trong knowledge_base.py).

    gender: 'nam' | 'nu' | 'unisex'
    Nếu lọc ra rỗng -> trả về danh sách gốc (tránh mất gợi ý hoàn toàn).
    """
    if gender == 'unisex':
        return product_ids[:top_n]

    _, chunks, _ = _load_faiss_cache()
    if not chunks:
        return product_ids[:top_n]

    gender_map = {
        c['id']: c.get('gender', 'unisex')
        for c in chunks if c['type'] == 'product'
    }

    filtered = [pid for pid in product_ids
                 if gender_map.get(pid, 'unisex') in (gender, 'unisex')]

    if filtered:
        return filtered[:top_n]
    return product_ids[:top_n]