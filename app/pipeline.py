# app/pipeline.py
from .models import TaiKhoan, KhachHang
from django.utils import timezone


def save_ami_session(backend, user, response, request, *args, **kwargs):
    """
    Sau khi social login thành công:
    - Tìm hoặc tạo TaiKhoan tương ứng với Django User
    - Lưu session để hệ thống Ami nhận ra
    - Kích hoạt AI Personalization
    """
    email     = user.email or ''
    full_name = user.get_full_name() or user.username or ''

    # Tìm TaiKhoan theo email
    account = TaiKhoan.objects.filter(Email__iexact=email).first()

    if not account:
        # Tạo mới TaiKhoan
        account = TaiKhoan.objects.create(
            Username         = user.username or email.split('@')[0],
            MatKhau          = None,
            TenDangNhap      = full_name,
            Email            = email,
            SDT              = '',
            LoaiTaiKhoan     = 'customer',
            TrangThai_TaiKhoan = 'active',
            NgayTao          = timezone.now(),
        )
        # Tạo KhachHang
        KhachHang.objects.create(
            id_TaiKhoan  = account,
            TenKhachHang = full_name,
            DiaChi       = '',
            GioiTinh     = '',
        )

    # Cập nhật avatar nếu là Google
    if backend.name == 'google-oauth2':
        avatar_url = response.get('picture', '')
        if avatar_url and not account.AnhDaiDien:
            account.AnhDaiDien = avatar_url
            account.save(update_fields=['AnhDaiDien'])

    # Lưu session Ami
    request.session['account_id']   = account.id_TaiKhoan
    request.session['account_name'] = account.TenDangNhap

    # Kích hoạt AI Personalization
    _trigger_ai_personalization(account.id_TaiKhoan)


def _trigger_ai_personalization(account_id):
    """Cập nhật cache AI sau khi đăng nhập."""
    import threading
    def _bg(acc_id):
        try:
            from app.ai.personalize import get_personalized_recommendations
            get_personalized_recommendations(account_id, top_n=8)
        except Exception as e:
            print(f'[AI] Personalization trigger failed: {e}')
    threading.Thread(target=_bg, args=(account_id,), daemon=True).start()