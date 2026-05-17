from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django import forms
from django.utils.safestring import mark_safe
from django.utils import timezone
import nested_admin

from .models import (
    BienThe, BienTheThuocTinh, GiaTriThuocTinh,
    LoaiSanPham, NhomHuong, SanPham, ThuocTinh,
    ThuongHieu, HinhAnh, SanPhamNhomHuong, BaiViet, HoiDap, TaiKhoan, DanhGia,
    KhuyenMai, KhuyenMaiTaiKhoan, KhachHang
)


# ═══════════════════════════════════════
#  CUSTOM ADMIN SITE
# ═══════════════════════════════════════
class MyAdminSite(admin.AdminSite):
    site_header  = "Ami Perfumery · Quản trị"
    site_title   = "Ami Admin"
    index_title  = "Tổng quan hệ thống"
    index_template = "admin/index.html"

    def index(self, request, extra_context=None):
        from .models import DonHang
        extra_context = extra_context or {}
        try:
            total_orders   = DonHang.objects.count()
            total_users    = TaiKhoan.objects.filter(LoaiTaiKhoan='customer').count()
            total_products = SanPham.objects.filter(TrangThai_SanPham='active').count()
            revenue_val    = DonHang.objects.filter(
                TrangThai__in=['Hoàn tất', 'Đã thanh toán']
            ).aggregate(s=__import__('django.db.models', fromlist=['Sum']).Sum('TongTien'))['s'] or 0
            revenue = f"{int(revenue_val):,}".replace(",", ".") + "₫"
        except Exception:
            total_orders = total_users = total_products = "—"
            revenue = "—"

        extra_context.update({
            "total_orders":   total_orders,
            "total_users":    total_users,
            "total_products": total_products,
            "revenue":        revenue,
        })
        return super().index(request, extra_context)


admin_site = MyAdminSite(name='myadmin')
admin_site.register(User)
admin_site.register(Group)


# ═══════════════════════════════════════
#  INLINES
# ═══════════════════════════════════════
class HinhAnhInline(nested_admin.NestedTabularInline):
    model       = HinhAnh
    extra       = 3
    fields      = ('url', 'image_thumb', 'id_BienThe')
    readonly_fields = ('image_thumb',)
    verbose_name        = "Hình ảnh"
    verbose_name_plural = "📷  Hình ảnh sản phẩm"

    def image_thumb(self, obj):
        if obj.url:
            return format_html(
                '<img src="{}" style="width:64px;height:64px;object-fit:cover;'
                'border-radius:8px;border:1px solid #e0d9cc;" />',
                obj.url.url,
            )
        return "—"
    image_thumb.short_description = "Xem trước"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if 'id_BienThe' in formset.form.base_fields:
            if obj is None:
                formset.form.base_fields['id_BienThe'].queryset = BienThe.objects.none()
                formset.form.base_fields['id_BienThe'].help_text = "Lưu sản phẩm trước khi gán ảnh cho biến thể."
            else:
                formset.form.base_fields['id_BienThe'].queryset = BienThe.objects.filter(id_SanPham=obj)
        return formset


class BienTheThuocTinhInline(nested_admin.NestedTabularInline):
    model               = BienTheThuocTinh
    extra               = 1
    autocomplete_fields = ('id_GiaTriThuocTinh',)
    verbose_name        = "Thuộc tính"
    verbose_name_plural = "Thuộc tính biến thể"


class BienTheInline(nested_admin.NestedStackedInline):
    model   = BienThe
    extra   = 1
    inlines = [BienTheThuocTinhInline]
    fieldsets = (
        ("Thông tin biến thể", {
            "fields": ("Sku", "GiaBan", "SoLuong"),
        }),
    )
    verbose_name        = "Biến thể"
    verbose_name_plural = "📦  Biến thể sản phẩm"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field_name, widget_class, placeholder in [
            ('Sku',     forms.TextInput,   'VD: CHANEL-NO5-50ML'),
            ('GiaBan',  forms.NumberInput, 'Giá bán'),
            ('SoLuong', forms.NumberInput, 'Số lượng tồn'),
        ]:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].widget = widget_class(attrs={
                    'placeholder': placeholder,
                })
        return formset


class SanPhamNhomHuongInline(nested_admin.NestedStackedInline):
    model               = SanPhamNhomHuong
    extra               = 1
    autocomplete_fields = ('id_NhomHuong',)
    fields              = ('id_NhomHuong', 'VaiTroHuong')
    verbose_name        = "Nhóm hương"
    verbose_name_plural = "🌿  Nhóm hương sản phẩm"


# ═══════════════════════════════════════
#  SanPham
# ═══════════════════════════════════════
@admin.register(SanPham, site=admin_site)
class SanPhamAdmin(nested_admin.NestedModelAdmin):
    list_display  = ('product_card', 'TrangThai_badge', 'NongDo', 'DoLuuHuong', 'DoToaHuong', 'ten_thuong_hieu', 'ten_loai_san_pham', 'get_nhom_huong', 'so_bien_the')
    list_display_links = ('product_card',)
    search_fields = ('TenSanPham',)
    list_filter   = ('TrangThai_SanPham', 'id_ThuongHieu', 'id_LoaiSanPham', 'nhom_huongs')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': (
                'TenSanPham',
                ('id_ThuongHieu', 'id_LoaiSanPham'),
                'TrangThai_SanPham',
                ('NongDo', 'NamPhatHanh', 'XuatXu'),
                ('DoLuuHuong', 'DoToaHuong'),
                ('MuaPhuHop', 'ThoiDiemSuDung'),
                ('PhongCach', 'DoTuoiPhuHop'),
                'MoTa_SanPham',
            ),
        }),
    )
    inlines = [SanPhamNhomHuongInline, BienTheInline, HinhAnhInline]

    def product_card(self, obj):
        img_tag = ""
        first_img = HinhAnh.objects.filter(id_SanPham=obj).first()
        if first_img and first_img.url:
            img_tag = format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;vertical-align:middle;margin-right:10px;border:1px solid #e0d9cc;"/>',
                first_img.url.url,
            )
        return format_html('{}<strong style="vertical-align:middle;">{}</strong>', img_tag, obj.TenSanPham)
    product_card.short_description = "Sản phẩm"

    def TrangThai_badge(self, obj):
        colors = {
            'active':   ('#e8f5e9', '#2e7d32', '● Đang bán'),
            'inactive': ('#fce4ec', '#c62828', '● Ngừng bán'),
            'draft':    ('#fff8e1', '#f57f17', '● Nháp'),
        }
        bg, fg, label = colors.get(obj.TrangThai_SanPham, ('#f5f5f5', '#616161', f'● {obj.TrangThai_SanPham or "—"}'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;">{}</span>', bg, fg, label)
    TrangThai_badge.short_description = "Trạng thái"

    def ten_thuong_hieu(self, obj):
        try: return obj.id_ThuongHieu.TenThuongHieu
        except: return "—"
    ten_thuong_hieu.short_description = "Thương hiệu"

    def ten_loai_san_pham(self, obj):
        try: return obj.id_LoaiSanPham.TenLoaiSanPham
        except: return "—"
    ten_loai_san_pham.short_description = "Loại"

    def get_nhom_huong(self, obj):
        huongs = SanPhamNhomHuong.objects.select_related('id_NhomHuong').filter(id_SanPham=obj)
        if not huongs.exists(): return "-"
        return mark_safe("".join([
            f'<span style="padding:3px 8px;background:#e8f5e9;border-radius:6px;margin-right:4px;font-size:11px;">'
            f'{h.id_NhomHuong.TenNhomHuong}</span>' for h in huongs
        ]))
    get_nhom_huong.short_description = "Nhóm hương"

    def so_bien_the(self, obj):
        count = BienThe.objects.filter(id_SanPham=obj).count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html('<span style="color:{};font-weight:600;">{} biến thể</span>', color, count)
    so_bien_the.short_description = "Biến thể"

    class Media:
        css = {'all': ('admin/css/ami_admin.css',)}
        js  = ('admin/js/ami_admin.js',)


# ═══════════════════════════════════════
#  BienThe
# ═══════════════════════════════════════
@admin.register(BienThe, site=admin_site)
class BienTheAdmin(admin.ModelAdmin):
    inlines       = [BienTheThuocTinhInline]
    list_display  = ('id_BienThe', 'ten_san_pham', 'Sku', 'gia_ban_fmt', 'SoLuong', 'ton_kho_badge')
    search_fields = ('Sku', 'id_SanPham__TenSanPham')
    list_filter   = ('id_SanPham__id_ThuongHieu', 'id_SanPham__id_LoaiSanPham')
    autocomplete_fields = ('id_SanPham',)

    def ten_san_pham(self, obj):
        try: return obj.id_SanPham.TenSanPham
        except: return "—"
    ten_san_pham.short_description = "Sản phẩm"

    def gia_ban_fmt(self, obj):
        return f"{int(obj.GiaBan):,}".replace(",", ".") + "₫" if obj.GiaBan else "—"
    gia_ban_fmt.short_description = "Giá bán"

    def ton_kho_badge(self, obj):
        if obj.SoLuong <= 0:
            return format_html('<span style="color:#c62828;font-weight:600;">Hết hàng</span>')
        if obj.SoLuong < 10:
            return format_html('<span style="color:#f57f17;font-weight:600;">Sắp hết ({})</span>', obj.SoLuong)
        return format_html('<span style="color:#2e7d32;font-weight:600;">Còn hàng ({})</span>', obj.SoLuong)
    ton_kho_badge.short_description = "Tồn kho"


@admin.register(ThuocTinh, site=admin_site)
class ThuocTinhAdmin(admin.ModelAdmin):
    list_display  = ('id_ThuocTinh', 'TenThuocTinh')
    search_fields = ('TenThuocTinh',)


@admin.register(GiaTriThuocTinh, site=admin_site)
class GiaTriThuocTinhAdmin(admin.ModelAdmin):
    list_display  = ('id_GiaTriThuocTinh', 'GiaTri', 'id_ThuocTinh')
    list_filter   = ('id_ThuocTinh',)
    search_fields = ('GiaTri', 'id_ThuocTinh__TenThuocTinh')
    autocomplete_fields = ('id_ThuocTinh',)


@admin.register(BienTheThuocTinh, site=admin_site)
class BienTheThuocTinhAdmin(admin.ModelAdmin):
    list_display  = ('id_BienThe', 'id_GiaTriThuocTinh')
    list_filter   = ('id_GiaTriThuocTinh__id_ThuocTinh',)
    autocomplete_fields = ('id_BienThe', 'id_GiaTriThuocTinh')


@admin.register(ThuongHieu, site=admin_site)
class ThuongHieuAdmin(admin.ModelAdmin):
    list_display  = ('logo_preview', 'TenThuongHieu')
    search_fields = ('TenThuongHieu',)

    def logo_preview(self, obj):
        if obj.LogoUrl:
            return format_html('<img src="{}" style="height:32px;object-fit:contain;"/>', obj.LogoUrl.url if hasattr(obj.LogoUrl, 'url') else obj.LogoUrl)
        return "—"
    logo_preview.short_description = "Logo"


@admin.register(LoaiSanPham, site=admin_site)
class LoaiSanPhamAdmin(admin.ModelAdmin):
    list_display  = ('image_preview', 'TenLoaiSanPham', 'MoTa')
    search_fields = ('TenLoaiSanPham',)

    def image_preview(self, obj):
        if obj.HinhanhUrl:
            return format_html('<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;"/>', obj.HinhanhUrl.url)
        return "—"
    image_preview.short_description = "Ảnh"


@admin.register(NhomHuong, site=admin_site)
class NhomHuongAdmin(admin.ModelAdmin):
    list_display  = ('icon_preview', 'TenNhomHuong', 'LoaiHuong')
    search_fields = ('TenNhomHuong', 'LoaiHuong')
    list_filter   = ('LoaiHuong',)

    def icon_preview(self, obj):
        if obj.IconUrl:
            return format_html('<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:50%;"/>', obj.IconUrl.url)
        return "🌸"
    icon_preview.short_description = "Icon"


@admin.register(HinhAnh, site=admin_site)
class HinhAnhAdmin(admin.ModelAdmin):
    list_display  = ('id_HinhAnh', 'image_preview', 'id_SanPham', 'id_BienThe')
    list_filter   = ('id_SanPham',)
    search_fields = ('id_SanPham__TenSanPham',)

    def image_preview(self, obj):
        if obj.url:
            return format_html('<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;"/>', obj.url.url)
        return "—"
    image_preview.short_description = "Ảnh"


# ═══════════════════════════════════════
#  BaiViet
# ═══════════════════════════════════════
@admin.register(BaiViet, site=admin_site)
class BaiVietAdmin(admin.ModelAdmin):
    list_display  = ('preview_img', 'TieuDe', 'TacGia', 'NgayTao')
    search_fields = ('TieuDe', 'TacGia')
    list_filter   = ('NgayTao',)

    def preview_img(self, obj):
        if obj.AnhDaiDien:
            return format_html('<img src="{}" style="width:56px;height:40px;object-fit:cover;border-radius:6px;"/>', obj.AnhDaiDien.url)
        return "—"
    preview_img.short_description = "Ảnh"


# ═══════════════════════════════════════
#  HoiDap
# ═══════════════════════════════════════
class HoiDapAdminForm(forms.ModelForm):
    tra_loi_noi_dung = forms.CharField(
        required=False, label="Nội dung trả lời",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Nhập câu trả lời…"})
    )

    class Meta:
        model  = HoiDap
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        obj = self.instance
        if obj and obj.pk and not obj.parent_id:
            existing = HoiDap.objects.filter(
                parent_id=obj.id_HoiDap,
                id_TaiKhoan__LoaiTaiKhoan__in=['admin', 'staff']
            ).order_by('NgayTao').first()
            if existing:
                self.fields['tra_loi_noi_dung'].initial = existing.NoiDung
                self.fields['tra_loi_noi_dung'].help_text = '⚠️ Đã có câu trả lời. Sửa ở đây sẽ cập nhật.'


@admin.register(HoiDap, site=admin_site)
class HoiDapAdmin(admin.ModelAdmin):
    form = HoiDapAdminForm
    list_display  = ('id_HoiDap', 'san_pham', 'nguoi_gui', 'loai_hoi_dap', 'TrangThai', 'NgayTao')
    search_fields = ('NoiDung', 'id_SanPham__TenSanPham', 'id_TaiKhoan__TenDangNhap')
    list_filter   = ('TrangThai',)
    readonly_fields = ('NgayTao',)
    list_select_related = ('id_SanPham', 'id_TaiKhoan')
    fields = ('id_SanPham', 'id_TaiKhoan', 'NoiDung', 'parent_id', 'TrangThai', 'tra_loi_noi_dung', 'NgayTao')

    def san_pham(self, obj):
        try: return obj.id_SanPham.TenSanPham
        except: return "-"
    san_pham.short_description = "Sản phẩm"

    def nguoi_gui(self, obj):
        try: return obj.id_TaiKhoan.TenDangNhap
        except: return "-"
    nguoi_gui.short_description = "Người gửi"

    def loai_hoi_dap(self, obj):
        if obj.parent_id:
            return mark_safe('<span style="color:#2e7d32;font-weight:600;font-size:11px;">TRẢ LỜI</span>')
        return mark_safe('<span style="color:#8d6e63;font-weight:600;font-size:11px;">CÂU HỎI</span>')
    loai_hoi_dap.short_description = "Loại"

    def save_model(self, request, obj, form, change):
        if obj.parent_id:
            obj.TrangThai = 'answered'
            super().save_model(request, obj, form, change)
            try:
                q = HoiDap.objects.get(id_HoiDap=obj.parent_id)
                q.TrangThai = 'answered'
                q.save(update_fields=['TrangThai'])
            except HoiDap.DoesNotExist:
                pass
            return

        super().save_model(request, obj, form, change)
        reply_content = (form.cleaned_data.get('tra_loi_noi_dung') or '').strip()
        if not reply_content:
            return

        admin_account = (
            TaiKhoan.objects.filter(Username=request.user.username).first()
            or TaiKhoan.objects.filter(LoaiTaiKhoan__in=['admin', 'staff']).first()
        )

        existing = HoiDap.objects.filter(
            parent_id=obj.id_HoiDap,
            id_TaiKhoan__LoaiTaiKhoan__in=['admin', 'staff']
        ).first()

        if existing:
            existing.NoiDung = reply_content
            existing.NgayTao = timezone.now()
            existing.TrangThai = 'answered'
            existing.save(update_fields=['NoiDung', 'NgayTao', 'TrangThai'])
        elif admin_account:
            HoiDap.objects.create(
                id_SanPham=obj.id_SanPham, id_TaiKhoan=admin_account,
                NoiDung=reply_content, NgayTao=timezone.now(),
                parent_id=obj.id_HoiDap, TrangThai='answered',
            )

        obj.TrangThai = 'answered'
        obj.save(update_fields=['TrangThai'])


# ═══════════════════════════════════════
#  DanhGia
# ═══════════════════════════════════════
@admin.register(DanhGia, site=admin_site)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display  = ('id_DanhGia', 'get_product', 'get_user', 'stars_display', 'short_content', 'NgayDanhGia')
    search_fields = ('NoiDung', 'id_TaiKhoan__TenDangNhap', 'id_SanPham__TenSanPham')
    list_filter   = ('SoSao', 'NgayDanhGia')
    readonly_fields = ('NgayDanhGia',)
    ordering = ('-NgayDanhGia',)

    def get_product(self, obj):
        return obj.id_SanPham.TenSanPham if obj.id_SanPham else "-"
    get_product.short_description = "Sản phẩm"

    def get_user(self, obj):
        return obj.id_TaiKhoan.TenDangNhap if obj.id_TaiKhoan else "-"
    get_user.short_description = "Khách hàng"

    def stars_display(self, obj):
        stars = '★' * int(obj.SoSao or 0) + '☆' * (5 - int(obj.SoSao or 0))
        return format_html('<span style="color:#c9a96e;font-size:14px;">{}</span>', stars)
    stars_display.short_description = "Sao"

    def short_content(self, obj):
        return (obj.NoiDung or "")[:80] or "-"
    short_content.short_description = "Nội dung"


# ═══════════════════════════════════════
#  KhuyenMai
# ═══════════════════════════════════════
@admin.register(KhuyenMai, site=admin_site)
class KhuyenMaiAdmin(admin.ModelAdmin):
    list_display  = ('MaKhuyenMai', 'TenKhuyenMai', 'LoaiKhuyenMai', 'LoaiGiam', 'gia_tri_fmt', 'SoLuong', 'DaSuDung', 'trang_thai_badge', 'NgayBatDau', 'NgayKetThuc')
    search_fields = ('MaKhuyenMai', 'TenKhuyenMai')
    list_filter   = ('TrangThai', 'LoaiKhuyenMai', 'LoaiGiam')
    ordering = ('-id_KhuyenMai',)

    def gia_tri_fmt(self, obj):
        if not obj.GiaTriGiam: return "—"
        if obj.LoaiGiam == 'percent':
            return f"{obj.GiaTriGiam:.0f}%"
        return f"{int(obj.GiaTriGiam):,}".replace(",", ".") + "₫"
    gia_tri_fmt.short_description = "Giá trị giảm"

    def trang_thai_badge(self, obj):
        colors = {'active': ('#e8f5e9', '#2e7d32', 'Hoạt động'), 'inactive': ('#fce4ec', '#c62828', 'Tắt'), 'expired': ('#f5f5f5', '#9e9e9e', 'Hết hạn')}
        bg, fg, label = colors.get(obj.TrangThai or '', ('#f5f5f5', '#9e9e9e', obj.TrangThai or '—'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">{}</span>', bg, fg, label)
    trang_thai_badge.short_description = "Trạng thái"


@admin.register(KhuyenMaiTaiKhoan, site=admin_site)
class KhuyenMaiTaiKhoanAdmin(admin.ModelAdmin):
    list_display  = ('id', 'get_user', 'get_voucher', 'DaSuDung', 'NgayNhan')
    list_filter   = ('DaSuDung',)
    search_fields = ('id_TaiKhoan__TenDangNhap', 'id_KhuyenMai__MaKhuyenMai')

    def get_user(self, obj):
        try: return obj.id_TaiKhoan.TenDangNhap
        except: return "—"
    get_user.short_description = "Tài khoản"

    def get_voucher(self, obj):
        try: return obj.id_KhuyenMai.MaKhuyenMai
        except: return "—"
    get_voucher.short_description = "Voucher"


# ═══════════════════════════════════════
#  TaiKhoan
# ═══════════════════════════════════════
@admin.register(TaiKhoan, site=admin_site)
class TaiKhoanAdmin(admin.ModelAdmin):
    list_display  = ('id_TaiKhoan', 'avatar_chip', 'TenDangNhap', 'Username', 'Email', 'SDT', 'loai_badge', 'trang_thai_badge', 'diem_display', 'NgayTao')
    list_filter   = ('LoaiTaiKhoan', 'TrangThai_TaiKhoan')
    search_fields = ('Username', 'TenDangNhap', 'Email', 'SDT')
    readonly_fields = ('NgayTao',)
    ordering = ('-id_TaiKhoan',)
    list_per_page = 25
    fields = ('Username', 'TenDangNhap', 'Email', 'SDT', 'LoaiTaiKhoan', 'TrangThai_TaiKhoan', 'DiemTichLuy', 'HangThanhVien', 'NgayTao')

    def avatar_chip(self, obj):
        initials = (obj.TenDangNhap or obj.Username or '?')[0].upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#344e1f,#5a7b35);'
            'display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:15px;color:#EBF6C4;font-weight:600;">{}</div>',
            initials
        )
    avatar_chip.short_description = ""

    def loai_badge(self, obj):
        colors = {
            'admin':    ('#fce4ec', '#c62828', '🔐 Admin'),
            'staff':    ('#e3f2fd', '#1565c0', '👔 Staff'),
            'customer': ('#e8f5e9', '#2e7d32', '👤 KH'),
        }
        bg, fg, label = colors.get(obj.LoaiTaiKhoan or '', ('#f5f5f5', '#9e9e9e', obj.LoaiTaiKhoan or '—'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;">{}</span>', bg, fg, label)
    loai_badge.short_description = "Loại"

    def trang_thai_badge(self, obj):
        is_active = (obj.TrangThai_TaiKhoan or '').lower() == 'active'
        if is_active:
            return format_html('<span style="background:#e8f5e9;color:#2e7d32;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">● Hoạt động</span>')
        return format_html('<span style="background:#fce4ec;color:#c62828;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">● Khóa</span>')
    trang_thai_badge.short_description = "Trạng thái"

    def diem_display(self, obj):
        pts = int(obj.DiemTichLuy or 0)
        return format_html('<span style="font-weight:600;color:#4B672D;">{} 🌿</span>', f"{pts:,}".replace(",", "."))
    diem_display.short_description = "Điểm"


# ═══════════════════════════════════════
#  KhachHang
# ═══════════════════════════════════════
@admin.register(KhachHang, site=admin_site)
class KhachHangAdmin(admin.ModelAdmin):
    list_display  = ('id_KhachHang', 'TenKhachHang', 'get_email', 'DiaChi', 'GioiTinh')
    search_fields = ('TenKhachHang', 'id_TaiKhoan__Email', 'id_TaiKhoan__Username')
    list_filter   = ('GioiTinh',)
    list_per_page = 25

    def get_email(self, obj):
        try: return obj.id_TaiKhoan.Email
        except: return "—"
    get_email.short_description = "Email"