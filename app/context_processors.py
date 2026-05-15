from .models import KhachHang, LoaiSanPham, TaiKhoan, ThuongHieu, YeuThich


def _normalize_vietnamese_text(value):
    if not isinstance(value, str) or not value:
        return value
    for source_enc in ("latin-1", "cp1252"):
        try:
            repaired = value.encode(source_enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if repaired != value:
            return repaired
    return value

def global_data(request):
    account_id = request.session.get("account_id")
    account = None

    if account_id:
        account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
        if account and account.TenDangNhap:
            account.TenDangNhap = _normalize_vietnamese_text(account.TenDangNhap)
    wishlist_count = 0
    if account:
        customer = KhachHang.objects.filter(id_TaiKhoan=account).first()
        if customer:
            wishlist_count = YeuThich.objects.filter(
                id_TaiKhoan=account
            ).count()
    return {
        "nav_categories": LoaiSanPham.objects.all(),
        "nav_brands": ThuongHieu.objects.all()[:6],
        "current_account": account,
        "is_logged_in": bool(account),
        "wishlist_count": wishlist_count,
    }