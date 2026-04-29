from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django import forms
from django.utils.safestring import mark_safe
import nested_admin

from .models import (
    BienThe, BienTheThuocTinh, GiaTriThuocTinh,
    LoaiSanPham, NhomHuong, SanPham, ThuocTinh,
    ThuongHieu, HinhAnh, SanPhamNhomHuong, BaiViet
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
        extra_context = extra_context or {}
        extra_context.update({
            "total_orders": 120,
            "total_users": 45,
            "revenue": "25.000.000₫",
        })
        return super().index(request, extra_context)


admin_site = MyAdminSite(name='myadmin')
admin_site.register(User)
admin_site.register(Group)


# ═══════════════════════════════════════
#  FORM tùy chỉnh cho SanPham
# ═══════════════════════════════════════
# class SanPhamForm(forms.ModelForm):
#     """
#     Thêm widget checkbox đẹp cho nhom_huongs thay vì
#     SelectMultiple mặc định.
#     """
#     nhom_huongs = forms.ModelMultipleChoiceField(
#         queryset=NhomHuong.objects.all(),
#         required=False,
#         widget=forms.CheckboxSelectMultiple(attrs={'class': 'nhom-huong-checks'}),
#         label="Nhóm hương",
#     )

#     class Meta:
#         model  = SanPham
#         fields = '__all__'
#         # exclude = ('nhom_huongs',)
#         widgets = {
#             'TenSanPham': forms.TextInput(attrs={
#                 'class': 'ami-input',
#                 'placeholder': 'Nhập tên sản phẩm...',
#             }),
#             'MoTa_SanPham': forms.Textarea(attrs={
#                 'class': 'ami-textarea',
#                 'rows': 5,
#                 'placeholder': 'Mô tả chi tiết về sản phẩm...',
#             }),
#             'TrangThai_SanPham': forms.Select(
#                 choices=[
#                     ('', '— Chọn trạng thái —'),
#                     ('active',   'Đang bán'),
#                     ('inactive', 'Ngừng bán'),
#                     ('draft',    'Nháp'),
#                 ],
#                 attrs={'class': 'ami-select'},
#             ),
#             'id_ThuongHieu': forms.Select(attrs={'class': 'ami-select'}),
#             'id_LoaiSanPham': forms.Select(attrs={'class': 'ami-select'}),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         if self.instance and self.instance.pk:
#             self.fields['nhom_huongs'].initial = self.instance.nhom_huongs.all()

#     def save(self, commit=True):
#         instance = super().save(commit=commit)

#         if commit and instance.pk:
#             instance.nhom_huongs.set(self.cleaned_data.get('nhom_huongs'))

#         return instance




# ═══════════════════════════════════════
#  INLINES
# ═══════════════════════════════════════
class HinhAnhInline(nested_admin.NestedTabularInline):
    model       = HinhAnh
    extra       = 3
    fields      = ('url', 'image_thumb', 'id_BienThe')
    readonly_fields = ('image_thumb',)
    verbose_name        = "Hình ảnh"
    verbose_name_plural = "📷  Hình ảnh sản phẩm (có thể thêm nhiều ảnh)"

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
                formset.form.base_fields['id_BienThe'].help_text = (
                    "Vui lòng lưu sản phẩm và thêm biến thể trước để gán ảnh cho biến thể."
                )
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
    """
    Dùng StackedInline để mỗi biến thể hiển thị rộng rãi hơn,
    dễ nhìn hơn TabularInline khi có nhiều trường.
    """
    model               = BienThe
    extra               = 1
    inlines = [BienTheThuocTinhInline]
    fieldsets = (
        ("Thông tin biến thể", {
            "fields": ("Sku", "GiaBan", "SoLuong"),
        }),
    )
    verbose_name        = "Biến thể"
    verbose_name_plural = "📦  Biến thể sản phẩm (kích thước / nồng độ)"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field_name, widget_class, placeholder in [
            ('Sku',     forms.TextInput,   'VD: CHANEL-NO5-50ML'),
            ('GiaNhap', forms.NumberInput, 'Giá nhập'),
            ('GiaBan',  forms.NumberInput, 'Giá bán'),
            ('SoLuong', forms.NumberInput, 'Số lượng tồn'),
        ]:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].widget = widget_class(attrs={
                    'class': 'ami-input',
                    'placeholder': placeholder,
                })
        return formset


class SanPhamNhomHuongInline(nested_admin.NestedStackedInline):
    model = SanPhamNhomHuong
    extra = 1
    autocomplete_fields = ('id_NhomHuong',)
    verbose_name = "Nhóm hương"
    verbose_name_plural = "🌿  Nhóm hương sản phẩm (chọn 1 hoặc nhiều)"

# ═══════════════════════════════════════
#  SanPham ADMIN
# ═══════════════════════════════════════
@admin.register(SanPham, site=admin_site)
class SanPhamAdmin(nested_admin.NestedModelAdmin):
    # form          = SanPhamForm
    change_form_template = "admin/sanpham_change_form.html"

    # Danh sách
    list_display  = (
        'product_card',         # custom HTML column
        'TrangThai_badge',
        'ten_thuong_hieu',
        'ten_loai_san_pham',
        'get_nhom_huong',
        'so_bien_the',
    )
    list_display_links = ('product_card',)
    search_fields = ('TenSanPham',)
    list_filter   = (
        'TrangThai_SanPham',
        'id_ThuongHieu',
        'id_LoaiSanPham',
        'nhom_huongs',
    )
    list_per_page = 20

    # Form thêm/sửa — một khối duy nhất, không chia tab
    fieldsets = (
        (None, {
            'fields': (
                'TenSanPham',
                ('id_ThuongHieu', 'id_LoaiSanPham'),
                'TrangThai_SanPham',
                # 'nhom_huongs',
                'MoTa_SanPham',
            ),
        }),
    )
    # filter_horizontal = ('nhom_huongs',)
    inlines = [
    SanPhamNhomHuongInline,   # 👈 QUAN TRỌNG NHẤT
    BienTheInline,
    HinhAnhInline
]

    # ── Custom list_display columns ──────────────────────────
    def product_card(self, obj):
        img = "—"
        first_img = HinhAnh.objects.filter(id_SanPham=obj).first()
        if first_img and first_img.url:
            img = format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;'
                'border-radius:8px;vertical-align:middle;margin-right:10px;'
                'border:1px solid #e0d9cc;"/>',
                first_img.url.url,
            )
        return format_html(
            '{}<strong style="vertical-align:middle;">{}</strong>',
            img, obj.TenSanPham,
        )
    product_card.short_description = "Sản phẩm"
    product_card.allow_tags = True

    def TrangThai_badge(self, obj):
        colors = {
            'active':   ('#e8f5e9', '#2e7d32', '●  Đang bán'),
            'inactive': ('#fce4ec', '#c62828', '● Ngừng bán'),
            'draft':    ('#fff8e1', '#f57f17', '●  Nháp'),
        }
        bg, fg, label = colors.get(
            obj.TrangThai_SanPham,
            ('#f5f5f5', '#616161', f'● {obj.TrangThai_SanPham or "—"}'),
        )
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:20px;'
            'font-size:11px;font-weight:600;white-space:nowrap;">{}</span>',
            bg, fg, label,
        )
    TrangThai_badge.short_description = "Trạng thái"

    def ten_thuong_hieu(self, obj):
        try:
            return obj.id_ThuongHieu.TenThuongHieu
        except Exception:
            return "—"
    ten_thuong_hieu.short_description = "Thương hiệu"

    def ten_loai_san_pham(self, obj):
        try:
            return obj.id_LoaiSanPham.TenLoaiSanPham
        except Exception:
            return "—"
    ten_loai_san_pham.short_description = "Loại"

    def get_nhom_huong(self, obj):
        huongs = obj.nhom_huongs.all()

        if not huongs.exists():
            return "-"

        return mark_safe("".join([
            f'<span style="padding:4px 8px;background:#e8f5e9;border-radius:6px;margin-right:4px;">{h.TenNhomHuong}</span>'
            for h in huongs
        ]))
    get_nhom_huong.short_description = "Nhóm hương"

    def so_bien_the(self, obj):
        count = BienThe.objects.filter(id_SanPham=obj).count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html(
            '<span style="color:{};font-weight:600;">{} biến thể</span>',
            color, count,
        )
    so_bien_the.short_description = "Biến thể"

    class Media:
        css  = {'all': ('admin/css/ami_admin.css',)}
        js   = ('admin/js/ami_admin.js',)


# ═══════════════════════════════════════
#  Các model khác
# ═══════════════════════════════════════
@admin.register(BienThe, site=admin_site)
class BienTheAdmin(admin.ModelAdmin):
    inlines       = [BienTheThuocTinhInline]
    list_display  = ('id_BienThe', 'id_SanPham', 'Sku', 'gia_ban_fmt', 'SoLuong', 'ton_kho_badge')
    search_fields = ('Sku', 'id_SanPham__TenSanPham')
    list_filter   = ('id_SanPham__id_ThuongHieu', 'id_SanPham__id_LoaiSanPham')
    autocomplete_fields = ('id_SanPham',)

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

    class Media:
        css = {'all': ('admin/css/ami_admin.css',)}


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
            return format_html(
                '<img src="{}" style="height:32px;object-fit:contain;"/>',
                obj.LogoUrl.url if hasattr(obj.LogoUrl, 'url') else obj.LogoUrl,
            )
        return "—"
    logo_preview.short_description = "Logo"

    class Media:
        css = {'all': ('admin/css/ami_admin.css',)}


@admin.register(LoaiSanPham, site=admin_site)
class LoaiSanPhamAdmin(admin.ModelAdmin):
    list_display  = ('image_preview', 'TenLoaiSanPham', 'MoTa')
    search_fields = ('TenLoaiSanPham',)

    def image_preview(self, obj):
        if obj.HinhanhUrl:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;"/>',
                obj.HinhanhUrl.url,
            )
        return "—"
    image_preview.short_description = "Ảnh"

    class Media:
        css = {'all': ('admin/css/ami_admin.css',)}


@admin.register(NhomHuong, site=admin_site)
class NhomHuongAdmin(admin.ModelAdmin):
    list_display  = ('icon_preview', 'TenNhomHuong')
    search_fields = ('TenNhomHuong',)

    def icon_preview(self, obj):
        if obj.IconUrl:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:50%;"/>',
                obj.IconUrl.url,
            )
        return "🌸"
    icon_preview.short_description = "Icon"

    class Media:
        css = {'all': ('admin/css/ami_admin.css',)}


admin_site.register(HinhAnh)


# ================================BÀI VIẾT========================

@admin.register(BaiViet, site=admin_site)
class BaiVietAdmin(admin.ModelAdmin):
    list_display = ("id_BaiViet", "TieuDe", "TacGia", "NgayTao")
    search_fields = ("TieuDe", "TacGia")
    list_filter = ("NgayTao",)

    def preview_image(self, obj):
        if obj.AnhDaiDien:
            return format_html('<img src="{}" width="60"/>', obj.AnhDaiDien.url)
        return "-"