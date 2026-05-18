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
    fields = ('id_GiaTriThuocTinh',)
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
    change_form_template = "admin/sanpham_change_form.html"
    add_form_template    = "admin/sanpham_change_form.html"
 
    list_display       = ('product_card', 'TrangThai_badge', 'NongDo', 'DoLuuHuong',
                          'DoToaHuong', 'ten_thuong_hieu', 'ten_loai_san_pham',
                          'get_nhom_huong', 'so_bien_the')
    list_display_links = ('product_card',)
    search_fields      = ('TenSanPham',)
    list_filter        = ('TrangThai_SanPham', 'id_ThuongHieu', 'id_LoaiSanPham', 'nhom_huongs')
    list_per_page      = 20
    inlines            = []
 
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['nhom_huong_list'] = NhomHuong.objects.all().order_by('TenNhomHuong')
 
        # Truyền thuoc_tinh_options dưới dạng list dict để dùng trong template HTML và json_script
        tt_list = ThuocTinh.objects.all().order_by('TenThuocTinh')
        extra_context['thuoc_tinh_list'] = tt_list
        extra_context['thuoc_tinh_options'] = [
            {'id': tt.pk, 'name': tt.TenThuocTinh or ''}
            for tt in tt_list
        ]
 
        # Validate object_id — phải là số nguyên hợp lệ
        valid_id = None
        if object_id:
            try:
                valid_id = int(object_id)
            except (ValueError, TypeError):
                valid_id = None  # object_id không hợp lệ (VD: 'styles.css.map')
 
        if valid_id:
            extra_context['existing_nhom_huong'] = (
                SanPhamNhomHuong.objects.filter(id_SanPham_id=valid_id).select_related('id_NhomHuong')
            )
            bienthe_qs = BienThe.objects.filter(id_SanPham_id=valid_id)
            bt_list = []
            for bt in bienthe_qs:
                btt = (BienTheThuocTinh.objects.filter(id_BienThe=bt)
                       .select_related('id_GiaTriThuocTinh__id_ThuocTinh').first())
                bt.thuoc_tinh_id   = btt.id_GiaTriThuocTinh.id_ThuocTinh.pk   if btt else ''
                bt.thuoc_tinh_name = btt.id_GiaTriThuocTinh.id_ThuocTinh.TenThuocTinh if btt else ''
                bt.gia_tri_id      = btt.id_GiaTriThuocTinh.pk                if btt else ''
                bt.gia_tri_name    = btt.id_GiaTriThuocTinh.GiaTri            if btt else ''
                bt_list.append(bt)
            extra_context['existing_bienthe'] = bt_list
            extra_context['existing_images']  = HinhAnh.objects.filter(id_SanPham_id=valid_id)
        else:
            extra_context['existing_nhom_huong'] = []
            extra_context['existing_bienthe']    = []
            extra_context['existing_images']     = []
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._save_nhom_huong(request, obj)
        self._save_bienthe(request, obj)
        self._save_images(request, obj)
 
    def _save_nhom_huong(self, request, obj):
        try:
            total = int(request.POST.get('sanphamnhomhuong_set-TOTAL_FORMS', 0))
        except (ValueError, TypeError):
            return
        SanPhamNhomHuong.objects.filter(id_SanPham=obj).delete()
        for i in range(total):
            nh_id   = request.POST.get(f'sanphamnhomhuong_set-{i}-id_NhomHuong', '').strip()
            vai_tro = request.POST.get(f'sanphamnhomhuong_set-{i}-VaiTroHuong', '').strip()
            if nh_id:
                try:
                    SanPhamNhomHuong.objects.create(
                        id_SanPham=obj,
                        id_NhomHuong_id=int(nh_id),
                        VaiTroHuong=vai_tro or None,
                    )
                except Exception:
                    pass
 
    def _save_bienthe(self, request, obj):
        try:
            total = int(request.POST.get('bienthe_set-TOTAL_FORMS', 0))
        except (ValueError, TypeError):
            total = 0
 
        if total == 0:
            return
 
        def safe_float(val):
            """Chuyển '200000,00' hoặc '200000.00' → float an toàn."""
            try:
                return float(str(val).replace(',', '.').strip())
            except (ValueError, TypeError):
                return 0.0
 
        def safe_int(val):
            try:
                return int(str(val).strip())
            except (ValueError, TypeError):
                return 0
 
        old_bts = BienThe.objects.filter(id_SanPham=obj)
        for bt in old_bts:
            BienTheThuocTinh.objects.filter(id_BienThe=bt).delete()
        old_bts.delete()
 
        for i in range(total):
            gt_id    = request.POST.get(f'bienthe_set-{i}-giaTriId', '').strip()
            sku      = request.POST.get(f'bienthe_set-{i}-sku',      '').strip()
            gia_nhap = request.POST.get(f'bienthe_set-{i}-giaNhap',  '0')
            gia_ban  = request.POST.get(f'bienthe_set-{i}-giaBan',   '0')
            so_luong = request.POST.get(f'bienthe_set-{i}-soLuong',  '0')
 
            if not gt_id:
                continue
            try:
                bt = BienThe.objects.create(
                    id_SanPham=obj,
                    Sku=sku or f'SP{obj.pk}-BT{i+1}',
                    GiaNhap=safe_float(gia_nhap),
                    GiaBan=safe_float(gia_ban),
                    SoLuong=safe_int(so_luong),
                )
                BienTheThuocTinh.objects.create(
                    id_BienThe=bt,
                    id_GiaTriThuocTinh_id=int(gt_id),
                )
            except Exception as e:
                import logging, traceback
                logging.getLogger(__name__).error(f'_save_bienthe error row {i}: {e}')
                traceback.print_exc()
 
    def _save_images(self, request, obj):
        for key in request.POST:
            if key.startswith('delete_image_'):
                try:
                    HinhAnh.objects.filter(pk=int(key.replace('delete_image_', '')),
                                           id_SanPham=obj).delete()
                except Exception:
                    pass
        for f in request.FILES.getlist('hinh_anh_files'):
            try:
                HinhAnh.objects.create(id_SanPham=obj, url=f)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'_save_images error: {e}')
 
    # ── List display ──
    def product_card(self, obj):
        img_tag = ""
        first_img = HinhAnh.objects.filter(id_SanPham=obj).first()
        if first_img and first_img.url:
            img_tag = format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;'
                'border-radius:8px;vertical-align:middle;margin-right:10px;border:1px solid #e0d9cc;"/>',
                first_img.url.url)
        return format_html('{}<strong style="vertical-align:middle;">{}</strong>', img_tag, obj.TenSanPham)
    product_card.short_description = "Sản phẩm"
 
    def TrangThai_badge(self, obj):
        colors = {'active':('#e8f5e9','#2e7d32','● Đang bán'),'inactive':('#fce4ec','#c62828','● Ngừng bán'),'draft':('#fff8e1','#f57f17','● Nháp')}
        bg,fg,label = colors.get(obj.TrangThai_SanPham,('#f5f5f5','#616161',f'● {obj.TrangThai_SanPham or "—"}'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;">{}</span>',bg,fg,label)
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
        return mark_safe("".join([f'<span style="padding:3px 8px;background:#e8f5e9;border-radius:6px;margin-right:4px;font-size:11px;">{h.id_NhomHuong.TenNhomHuong}</span>' for h in huongs]))
    get_nhom_huong.short_description = "Nhóm hương"
 
    def so_bien_the(self, obj):
        count = BienThe.objects.filter(id_SanPham=obj).count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html('<span style="color:{};font-weight:600;">{} biến thể</span>',color,count)
    so_bien_the.short_description = "Biến thể"
 
 


# ═══════════════════════════════════════
#  BienThe
# ═══════════════════════════════════════
@admin.register(BienThe, site=admin_site)
class BienTheAdmin(admin.ModelAdmin):
    inlines       = [BienTheThuocTinhInline]
    list_display  = ('id_BienThe', 'id_SanPham', 'Sku', 'gia_ban_fmt', 'SoLuong', 'ton_kho_badge')
    search_fields = ('Sku', 'id_SanPham__TenSanPham')
    list_filter   = ('id_SanPham__id_ThuongHieu', 'id_SanPham__id_LoaiSanPham')
    autocomplete_fields = ('id_SanPham',)
 
    def get_model_perms(self, request):
        """Ẩn Biến thể khỏi sidebar — quản lý qua form Sản phẩm."""
        return {}
 
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
    change_form_template = "admin/thuoctinh_change_form.html"
    add_form_template    = "admin/thuoctinh_change_form.html"
 
    list_display   = ('tt_card', 'so_gia_tri', 'danh_sach_gia_tri')
    search_fields  = ('TenThuocTinh',)
    list_per_page  = 20
 
    # ── Context cho template ──
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            try:
                extra_context['existing_values'] = GiaTriThuocTinh.objects.filter(
                    id_ThuocTinh_id=int(object_id)
                ).order_by('GiaTri')
            except (ValueError, TypeError):
                extra_context['existing_values'] = []
        else:
            extra_context['existing_values'] = []
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    # ── Save ──
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._save_gia_tri(request, obj)
 
    def _save_gia_tri(self, request, obj):
        """Xử lý toàn bộ thêm/sửa/xóa GiaTriThuocTinh từ POST."""
 
        # 1. Cập nhật / xóa existing values
        for key in request.POST:
            if key.startswith('gt_value_'):
                pk_str = key.replace('gt_value_', '')
                try:
                    pk = int(pk_str)
                except ValueError:
                    continue
 
                # Kiểm tra checkbox xóa
                delete_key = f'gt_delete_{pk}'
                if request.POST.get(delete_key):
                    GiaTriThuocTinh.objects.filter(
                        pk=pk, id_ThuocTinh=obj
                    ).delete()
                else:
                    new_val = request.POST.get(key, '').strip()
                    if new_val:
                        GiaTriThuocTinh.objects.filter(
                            pk=pk, id_ThuocTinh=obj
                        ).update(GiaTri=new_val)
 
        # 2. Thêm giá trị mới
        try:
            new_count = int(request.POST.get('gt_new_count', 0))
        except (ValueError, TypeError):
            new_count = 0
 
        for i in range(1, new_count + 100):  # scan tất cả key gt_new_N
            val = request.POST.get(f'gt_new_{i}', '').strip()
            if val:
                GiaTriThuocTinh.objects.create(
                    id_ThuocTinh=obj,
                    GiaTri=val,
                )
            # Dừng khi không còn key nào nữa (tránh infinite scan)
            if i > new_count + 20:
                break
 
    # ── Delete — xóa GiaTriThuocTinh trước để tránh FK constraint ──
    def delete_model(self, request, obj):
        """Xóa tất cả giá trị thuộc tính trước, sau đó xóa thuộc tính."""
        # Xóa BienThe_ThuocTinh liên quan trước
        from .models import BienTheThuocTinh
        gt_ids = GiaTriThuocTinh.objects.filter(id_ThuocTinh=obj).values_list('pk', flat=True)
        BienTheThuocTinh.objects.filter(id_GiaTriThuocTinh_id__in=gt_ids).delete()
        # Xóa GiaTriThuocTinh
        GiaTriThuocTinh.objects.filter(id_ThuocTinh=obj).delete()
        # Xóa ThuocTinh
        obj.delete()
 
    def delete_queryset(self, request, queryset):
        """Xóa hàng loạt — xóa FK children trước."""
        from .models import BienTheThuocTinh
        for obj in queryset:
            gt_ids = GiaTriThuocTinh.objects.filter(id_ThuocTinh=obj).values_list('pk', flat=True)
            BienTheThuocTinh.objects.filter(id_GiaTriThuocTinh_id__in=gt_ids).delete()
            GiaTriThuocTinh.objects.filter(id_ThuocTinh=obj).delete()
        queryset.delete()
 
    # ── List display ──
    def tt_card(self, obj):
        return format_html(
            '<strong style="color:var(--olive,#4B672D);font-size:13px;">{}</strong>',
            obj.TenThuocTinh
        )
    tt_card.short_description = "Tên thuộc tính"
 
    def so_gia_tri(self, obj):
        count = GiaTriThuocTinh.objects.filter(id_ThuocTinh=obj).count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html(
            '<span style="color:{};font-weight:600;">{} giá trị</span>',
            color, count
        )
    so_gia_tri.short_description = "Số giá trị"
 
    def danh_sach_gia_tri(self, obj):
        vals = GiaTriThuocTinh.objects.filter(id_ThuocTinh=obj).order_by('GiaTri')[:8]
        if not vals:
            return mark_safe('<span style="color:#9e9e9e;font-style:italic;">Chưa có</span>')
        tags = ''.join([
            f'<span style="padding:2px 8px;background:rgba(75,103,45,.1);'
            f'border-radius:20px;font-size:11px;margin-right:4px;color:#4B672D;">'
            f'{v.GiaTri}</span>'
            for v in vals
        ])
        return mark_safe(tags)
    danh_sach_gia_tri.short_description = "Giá trị"


@admin.register(GiaTriThuocTinh, site=admin_site)
class GiaTriThuocTinhAdmin(admin.ModelAdmin):
    list_display  = ('id_GiaTriThuocTinh', 'GiaTri', 'id_ThuocTinh')
    list_filter   = ('id_ThuocTinh',)
    search_fields = ('GiaTri', 'id_ThuocTinh__TenThuocTinh')
    def get_model_perms(self, request):
        """Ẩn khỏi sidebar — vẫn registered để autocomplete hoạt động."""
        return {}


@admin.register(BienTheThuocTinh, site=admin_site)
class BienTheThuocTinhAdmin(admin.ModelAdmin):
    list_display  = ('id_BienThe', 'id_GiaTriThuocTinh')
    list_filter   = ('id_GiaTriThuocTinh__id_ThuocTinh',)
    raw_id_fields = ('id_BienThe', 'id_GiaTriThuocTinh')
 
    def get_model_perms(self, request):
        """Ẩn BienTheThuocTinh khỏi sidebar — quản lý qua SanPham."""
        return {}


@admin.register(ThuongHieu, site=admin_site)
class ThuongHieuAdmin(admin.ModelAdmin):
    change_form_template = "admin/thuonghieu_change_form.html"
    add_form_template    = "admin/thuonghieu_change_form.html"
 
    list_display   = ('logo_preview', 'TenThuongHieu', 'so_san_pham')
    search_fields  = ('TenThuongHieu',)
    list_per_page  = 20
 
    def logo_preview(self, obj):
        if obj.LogoUrl:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:contain;'
                'border-radius:8px;border:1px solid #e0d9cc;background:#fafaf8;padding:2px;">',
                obj.LogoUrl.url
            )
        return format_html('<span style="color:#bbb;font-size:20px;">🏪</span>')
    logo_preview.short_description = "Logo"
 
    def so_san_pham(self, obj):
        from .models import SanPham
        count = SanPham.objects.filter(id_ThuongHieu=obj).count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html('<span style="color:{};font-weight:600;">{} sản phẩm</span>', color, count)
    so_san_pham.short_description = "Sản phẩm"
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}


@admin.register(LoaiSanPham, site=admin_site)
class LoaiSanPhamAdmin(admin.ModelAdmin):
    change_form_template = "admin/loaisanpham_change_form.html"
    add_form_template    = "admin/loaisanpham_change_form.html"
 
    # Đầy đủ tất cả cột trong DB
    list_display   = ('hinhanh_preview', 'TenLoaiSanPham', 'mo_ta_short', 'GhiChu', 'so_san_pham')
    search_fields  = ('TenLoaiSanPham', 'MoTa', 'GhiChu')
    list_per_page  = 20
 
    def hinhanh_preview(self, obj):
        if obj.HinhanhUrl:
            return format_html(
                '<img src="{}" style="width:56px;height:56px;object-fit:cover;'
                'border-radius:8px;border:1px solid #e0d9cc;">',
                obj.HinhanhUrl.url
            )
        return format_html('<span style="font-size:24px;">📂</span>')
    hinhanh_preview.short_description = "Ảnh"
 
    def mo_ta_short(self, obj):
        if not obj.MoTa:
            return format_html('<span style="color:#bbb;font-style:italic;">Chưa có</span>')
        # Strip HTML tags for display
        import re
        text = re.sub(r'<[^>]+>', '', str(obj.MoTa))
        return text[:60] + '…' if len(text) > 60 else text
    mo_ta_short.short_description = "Mô tả"
 
    def so_san_pham(self, obj):
        from .models import SanPham
        count = SanPham.objects.filter(id_LoaiSanPham=obj).count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html('<span style="color:{};font-weight:600;">{} sản phẩm</span>', color, count)
    so_san_pham.short_description = "Sản phẩm"
 
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}
        js  = ('ckeditor/ckeditor/ckeditor.js',)


@admin.register(NhomHuong, site=admin_site)
class NhomHuongAdmin(admin.ModelAdmin):
    change_form_template = "admin/nhomhuong_change_form.html"
    add_form_template    = "admin/nhomhuong_change_form.html"
 
    list_display   = ('icon_preview', 'TenNhomHuong', 'LoaiHuong',
                      'mau_sac_display', 'mo_ta_short', 'so_san_pham')
    search_fields  = ('TenNhomHuong', 'LoaiHuong')
    list_filter    = ('LoaiHuong',)
    list_per_page  = 20
 
    LOAI_HUONG_CHOICES = [
        'Floral', 'Woody', 'Citrus', 'Oriental', 'Fresh',
        'Gourmand', 'Fruity', 'Aquatic', 'Spicy', 'Leather',
        'Top Notes', 'Heart Notes', 'Base Notes',
    ]
 
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['loai_huong_choices'] = self.LOAI_HUONG_CHOICES
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    def icon_preview(self, obj):
        if obj.IconUrl:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:contain;'
                'border-radius:8px;background:#fafaf8;border:1px solid #e8e2d8;padding:2px;">',
                obj.IconUrl.url
            )
        return format_html('<span style="font-size:22px;">🌸</span>')
    icon_preview.short_description = "Icon"
 
    def mau_sac_display(self, obj):
        mau = getattr(obj, 'MauSac', None)
        if not mau:
            return mark_safe('<span style="color:#bbb;">—</span>')
        color = mau if mau.startswith('#') else '#4B672D'
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:6px;">'
            '<span style="width:14px;height:14px;border-radius:50%;background:{};">'
            '</span><span style="font-size:11px;">{}</span></span>',
            color, mau
        )
    mau_sac_display.short_description = "Màu sắc"
 
    def mo_ta_short(self, obj):
        mota = getattr(obj, 'MoTa_NhomHuong', None)
        if not mota:
            return mark_safe('<span style="color:#bbb;font-style:italic;">Chưa có</span>')
        import re
        text = re.sub(r'<[^>]+>', '', str(mota))
        return text[:50] + '…' if len(text) > 50 else text
    mo_ta_short.short_description = "Mô tả"
 
    def so_san_pham(self, obj):
        count = SanPhamNhomHuong.objects.filter(
            id_NhomHuong=obj
        ).values('id_SanPham').distinct().count()
        color = "#2e7d32" if count > 0 else "#9e9e9e"
        return format_html(
            '<span style="color:{};font-weight:600;">{} sản phẩm</span>', color, count
        )
    so_san_pham.short_description = "Sản phẩm"
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}


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
    change_form_template = "admin/baiviet_change_form.html"
    add_form_template    = "admin/baiviet_change_form.html"
 
    # Đầy đủ cột DB: id_BaiViet, TieuDe, NoiDung, NgayTao, TacGia, AnhDaiDien
    list_display   = ('anh_preview', 'TieuDe', 'TacGia', 'NgayTao')
    list_display_links = ('TieuDe',)
    search_fields  = ('TieuDe', 'TacGia', 'NoiDung')
    list_filter    = ('NgayTao', 'TacGia')
    ordering       = ('-NgayTao',)
    list_per_page  = 20
 
    def anh_preview(self, obj):
        if obj.AnhDaiDien:
            return format_html(
                '<img src="{}" style="width:56px;height:40px;object-fit:cover;'
                'border-radius:6px;border:1px solid #e0d9cc;">',
                obj.AnhDaiDien.url
            )
        return format_html('<span style="font-size:20px;">📰</span>')
    anh_preview.short_description = "Ảnh"
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}
        js  = ('ckeditor/ckeditor/ckeditor.js',)


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
    change_form_template = "admin/hoidap_change_form.html"
    # KHÔNG có add_form_template — ẩn nút "Thêm mới" bằng has_add_permission
 
    list_display   = ('id_HoiDap', 'ten_san_pham', 'ten_khach_hang',
                      'noi_dung_short', 'trang_thai_badge', 'NgayTao')
    list_display_links = ('id_HoiDap', 'noi_dung_short')
    list_filter    = ('TrangThai', 'NgayTao')
    search_fields  = ('NoiDung', 'id_TaiKhoan__TenDangNhap', 'id_SanPham__TenSanPham')
    ordering       = ('-NgayTao',)
    list_per_page  = 20
 
    def has_add_permission(self, request):
        """Ẩn nút Thêm mới — câu hỏi đến từ khách hàng."""
        return False
 
    def ten_san_pham(self, obj):
        if obj.id_SanPham:
            return format_html(
                '<a href="/admin/app/sanpham/{}/change/" style="color:var(--olive,#4B672D);">{}</a>',
                obj.id_SanPham.pk,
                obj.id_SanPham.TenSanPham[:30]
            )
        return "—"
    ten_san_pham.short_description = "Sản phẩm"
 
    def ten_khach_hang(self, obj):
        return obj.id_TaiKhoan.TenDangNhap if obj.id_TaiKhoan else "—"
    ten_khach_hang.short_description = "Khách hàng"
 
    def noi_dung_short(self, obj):
        return (obj.NoiDung or "")[:60] + "…" if obj.NoiDung and len(obj.NoiDung) > 60 else obj.NoiDung or "—"
    noi_dung_short.short_description = "Nội dung"
 
    def trang_thai_badge(self, obj):
        colors = {
            'pending':  ('#fff8e1', '#f57f17', '⏳ Đang chờ'),
            'answered': ('#e8f5e9', '#2e7d32', '✅ Đã trả lời'),
            'hidden':   ('#fce4ec', '#c62828', '🚫 Ẩn'),
        }
        bg, fg, label = colors.get(obj.TrangThai or 'pending', ('#f5f5f5', '#616161', obj.TrangThai or '—'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, label
        )
    trang_thai_badge.short_description = "Trạng thái"
 
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}


# ═══════════════════════════════════════
#  DanhGia
# ═══════════════════════════════════════
@admin.register(DanhGia, site=admin_site)
class DanhGiaAdmin(admin.ModelAdmin):
    change_form_template = "admin/danhgia_change_form.html"
    # KHÔNG có add_form_template — ẩn nút "Thêm mới"
 
    list_display   = ('id_DanhGia', 'ten_san_pham', 'ten_khach_hang',
                      'sao_display', 'noi_dung_short', 'phan_hoi_badge', 'NgayDanhGia')
    list_display_links = ('id_DanhGia', 'noi_dung_short')
    list_filter    = ('SoSao', 'NgayDanhGia')
    search_fields  = ('NoiDung', 'id_TaiKhoan__TenDangNhap', 'id_SanPham__TenSanPham')
    ordering       = ('-NgayDanhGia',)
    list_per_page  = 20
 
    def has_add_permission(self, request):
        """Ẩn nút Thêm mới — đánh giá đến từ khách hàng."""
        return False
 
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            try:
                oid = int(object_id)
                # Lấy phản hồi của admin (SoSao=None, parent_id=oid)
                admin_replies = DanhGia.objects.filter(
                    parent_id=oid,
                    id_TaiKhoan__LoaiTaiKhoan__in=['admin', 'staff']
                ).order_by('NgayDanhGia')
                extra_context['admin_replies'] = list(admin_replies)
                extra_context['current_admin_reply'] = admin_replies.last()
            except (ValueError, TypeError):
                extra_context['admin_replies'] = []
                extra_context['current_admin_reply'] = None
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Lưu phản hồi admin nếu có
        reply_content = request.POST.get('admin_reply', '').strip()
        if reply_content:
            existing = DanhGia.objects.filter(
                parent_id=obj.pk,
                id_TaiKhoan__LoaiTaiKhoan__in=['admin', 'staff']
            ).first()
            account = request.user
            # Tìm TaiKhoan tương ứng với user Django
            try:
                from .models import TaiKhoan as TK
                tk = TK.objects.filter(Username=account.username).first()
            except Exception:
                tk = None
 
            if existing:
                existing.NoiDung = reply_content
                existing.save(update_fields=['NoiDung'])
            elif tk:
                DanhGia.objects.create(
                    id_SanPham=obj.id_SanPham,
                    id_TaiKhoan=tk,
                    parent_id=obj.pk,
                    SoSao=None,
                    NoiDung=reply_content,
                    NgayDanhGia=timezone.now(),
                )
 
    def ten_san_pham(self, obj):
        return obj.id_SanPham.TenSanPham[:30] if obj.id_SanPham else "—"
    ten_san_pham.short_description = "Sản phẩm"
 
    def ten_khach_hang(self, obj):
        return obj.id_TaiKhoan.TenDangNhap if obj.id_TaiKhoan else "—"
    ten_khach_hang.short_description = "Khách hàng"
 
    def sao_display(self, obj):
        stars = '⭐' * (obj.SoSao or 0)
        return format_html('<span title="{}/5">{}</span>', obj.SoSao or 0, stars or '—')
    sao_display.short_description = "Sao"
 
    def noi_dung_short(self, obj):
        if not obj.NoiDung: return "—"
        return (obj.NoiDung[:55] + '…') if len(obj.NoiDung) > 55 else obj.NoiDung
    noi_dung_short.short_description = "Nội dung"
 
    def phan_hoi_badge(self, obj):
        has_reply = DanhGia.objects.filter(parent_id=obj.pk).exists()
        if has_reply:
            return mark_safe('<span style="background:#e8f5e9;color:#2e7d32;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">✅ Đã phản hồi</span>')
        return mark_safe('<span style="background:#fff8e1;color:#f57f17;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">⏳ Chưa</span>')
    phan_hoi_badge.short_description = "Phản hồi"
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}


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