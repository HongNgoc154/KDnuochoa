"""
app/ai/recently_viewed.py
=========================
Quản lý "Sản phẩm đã xem gần đây" cho cả Guest và Registered User.

Guest   → lưu trong Django session (tạm thời, mất khi rời web)
Registered → lưu DB (lâu dài, đồng bộ đa thiết bị)
"""

from __future__ import annotations

MAX_GUEST_VIEWED   = 20   # số SP tối đa lưu trong session
MAX_DB_VIEWED      = 50   # số bản ghi tối đa lưu trong DB mỗi user
SESSION_KEY        = "recently_viewed"


# ════════════════════════════════════════════════════════════════
# GUEST — session-based
# ════════════════════════════════════════════════════════════════

def guest_track_view(request, product_id: int) -> None:
    """Ghi nhận sản phẩm vừa xem vào session (Guest)."""
    viewed: list = request.session.get(SESSION_KEY, [])

    # Đưa lên đầu danh sách (most-recent first), loại bỏ duplicate
    viewed = [pid for pid in viewed if pid != product_id]
    viewed.insert(0, product_id)
    viewed = viewed[:MAX_GUEST_VIEWED]

    request.session[SESSION_KEY] = viewed
    request.session.modified = True


def guest_get_viewed(request, exclude_id: int | None = None) -> list[int]:
    """Trả về danh sách product_id đã xem trong session (Guest)."""
    viewed: list = request.session.get(SESSION_KEY, [])
    if exclude_id:
        viewed = [pid for pid in viewed if pid != exclude_id]
    return viewed


# ════════════════════════════════════════════════════════════════
# REGISTERED USER — database
# ════════════════════════════════════════════════════════════════

def user_track_view(account_id: int, product_id: int,
                    time_spent: int | None = None) -> None:
    """
    Ghi nhận (hoặc cập nhật) lượt xem sản phẩm của Registered User vào DB.
    Nếu đã có bản ghi cùng user+SP trong 24h → cập nhật thay vì tạo mới.
    """
    from django.utils import timezone
    from datetime import timedelta
    from app.models import LichSuXemSanPham

    cutoff = timezone.now() - timedelta(hours=24)

    existing = LichSuXemSanPham.objects.filter(
        id_TaiKhoan_id=account_id,
        id_SanPham_id=product_id,
        NgayXem__gte=cutoff
    ).first()

    if existing:
        existing.SoLanXem += 1
        if time_spent:
            existing.ThoiGianXem = (existing.ThoiGianXem or 0) + time_spent
        existing.NgayXem = timezone.now()   # refresh timestamp
        existing.save(update_fields=['SoLanXem', 'ThoiGianXem', 'NgayXem'])
    else:
        LichSuXemSanPham.objects.create(
            id_TaiKhoan_id=account_id,
            id_SanPham_id=product_id,
            ThoiGianXem=time_spent,
        )
        _trim_old_records(account_id)


def user_get_viewed(account_id: int, limit: int = 12,
                    exclude_id: int | None = None) -> list[int]:
    """
    Trả về danh sách product_id đã xem gần đây nhất (Registered User).
    Sắp xếp theo NgayXem DESC.
    """
    from app.models import LichSuXemSanPham

    qs = LichSuXemSanPham.objects.filter(
        id_TaiKhoan_id=account_id
    ).order_by('-NgayXem')

    if exclude_id:
        qs = qs.exclude(id_SanPham_id=exclude_id)

    return list(qs.values_list('id_SanPham_id', flat=True)[:limit])


def _trim_old_records(account_id: int) -> None:
    """Giữ tối đa MAX_DB_VIEWED bản ghi mới nhất, xóa bản ghi cũ."""
    from app.models import LichSuXemSanPham

    ids = list(
        LichSuXemSanPham.objects
        .filter(id_TaiKhoan_id=account_id)
        .order_by('-NgayXem')
        .values_list('id_LichSu', flat=True)
    )
    if len(ids) > MAX_DB_VIEWED:
        delete_ids = ids[MAX_DB_VIEWED:]
        LichSuXemSanPham.objects.filter(id_LichSu__in=delete_ids).delete()


# ════════════════════════════════════════════════════════════════
# UNIVERSAL — gọi từ view, tự phân loại guest/user
# ════════════════════════════════════════════════════════════════

def track_view(request, product_id: int, time_spent: int | None = None) -> None:
    """Hàm duy nhất gọi từ view — tự xử lý guest vs registered."""
    account_id = request.session.get("account_id")
    if account_id:
        user_track_view(account_id, product_id, time_spent)
    else:
        guest_track_view(request, product_id)


def get_viewed_products(request, limit: int = 12,
                        exclude_id: int | None = None) -> list[int]:
    """Trả về danh sách product_id đã xem — tự phân loại guest/user."""
    account_id = request.session.get("account_id")
    if account_id:
        return user_get_viewed(account_id, limit=limit, exclude_id=exclude_id)
    return guest_get_viewed(request, exclude_id=exclude_id)[:limit]