from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django import forms
from django.utils.safestring import mark_safe
from django.utils import timezone
import nested_admin
from django.db import connection
from django import forms as django_forms
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone as tz
from django.http import Http404
from django.urls import reverse
from django.utils.html import strip_tags

from .models import (
    BienThe, BienTheThuocTinh, GiaTriThuocTinh,
    LoaiSanPham, NhomHuong, SanPham, ThuocTinh,
    ThuongHieu, HinhAnh, SanPhamNhomHuong, BaiViet, HoiDap, TaiKhoan, DanhGia,
    KhuyenMai, KhuyenMaiTaiKhoan, KhachHang, NhaCungCap, PhieuNhap, ChiTietNhap,
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
        # Chặn object_id không phải số
        if object_id and not str(object_id).isdigit():
            raise Http404("object_id không hợp lệ")
        
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
 
        old_bts = list(BienThe.objects.filter(id_SanPham=obj).order_by('id_BienThe'))

        for bt in old_bts:
            BienTheThuocTinh.objects.filter(id_BienThe=bt).delete()
 
        for i in range(total):
            gt_id    = request.POST.get(f'bienthe_set-{i}-giaTriId', '').strip()
            sku      = request.POST.get(f'bienthe_set-{i}-sku',      '').strip()
            gia_nhap = request.POST.get(f'bienthe_set-{i}-giaNhap',  '0')
            gia_ban  = request.POST.get(f'bienthe_set-{i}-giaBan',   '0')
            so_luong = request.POST.get(f'bienthe_set-{i}-soLuong',  '0')

            if not gt_id:
                continue

            try:
                if i < len(old_bts):
                    bt = old_bts[i]
                    bt.Sku = sku or f'SP{obj.pk}-BT{i+1}'
                    bt.GiaNhap = safe_float(gia_nhap)
                    bt.GiaBan = safe_float(gia_ban)
                    bt.SoLuong = safe_int(so_luong)
                    bt.save(update_fields=['Sku', 'GiaNhap', 'GiaBan', 'SoLuong'])
                else:
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
        first_img = HinhAnh.objects.filter(
            id_SanPham=obj
        ).first()

        img_url = ""
        if first_img and first_img.url:
            img_url = first_img.url.url

        # Link tên sản phẩm không gạch chân
        obj_link = format_html(
            '<a href="{}" style="text-decoration:none;color:#2d2d2d;">{}</a>',
            reverse(
                'admin:app_sanpham_change',
                args=[obj.pk]
            ),
            obj.TenSanPham
        )

        return format_html("""
            <div style="
                display:flex;
                align-items:center;
                gap:12px;
                min-width:240px;
            ">

                <div style="
                    width:54px;
                    height:54px;
                    border-radius:10px;
                    overflow:hidden;
                    border:1px solid #e5dfd4;
                    background:#fff;
                    flex-shrink:0;
                ">
                    {}
                </div>

                <div style="
                    display:flex;
                    flex-direction:column;
                    justify-content:center;
                    min-width:0;
                ">
                    <div style="
                        font-size:14px;
                        font-weight:600;
                        line-height:1.4;
                    ">
                        {}
                    </div>

                    <div style="
                        margin-top:4px;
                        font-size:11px;
                        color:#888;
                    ">
                        {}
                    </div>
                </div>
            </div>
        """,

        format_html(
            '<img src="{}" style="width:100%;height:100%;object-fit:cover;">',
            img_url
        ) if img_url else "",

        obj_link,

        obj.id_ThuongHieu.TenThuongHieu
        if obj.id_ThuongHieu else "—"
    )

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
    list_display_links = None
 
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
        url = reverse('myadmin:app_thuoctinh_change', args=[obj.pk])

        return format_html(
            '''
            <a href="{}" style="
                text-decoration:none;
                color:#2d2d2d;
                font-size:14px;
                font-weight:600;
                display:inline-block;
                text-align:left;
            ">
                {}
            </a>
            ''',
            url,
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
 
    list_display   = ('logo_preview', 'TenThuongHieu', 'so_san_pham', 'MoTa')
    list_display_links = None
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
    list_display_links = None
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
    list_display_links = None
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

    list_display = (
        'anh_preview',
        'tieude_card',
        'noidung_preview',
        'tacgia_card',
        'NgayTao'
    )

    # bỏ link mặc định của Django
    list_display_links = None

    search_fields = ('TieuDe', 'TacGia', 'NoiDung')
    list_filter = ('NgayTao', 'TacGia')
    ordering = ('-NgayTao',)
    list_per_page = 20


    def anh_preview(self, obj):
        if obj.AnhDaiDien:
            return format_html(
                '''
                <img src="{}"
                style="
                    width:70px;
                    height:50px;
                    object-fit:cover;
                    border-radius:8px;
                    border:1px solid #e0d9cc;
                ">
                ''',
                obj.AnhDaiDien.url
            )

        return "📰"

    anh_preview.short_description = "Ảnh"


    def tieude_card(self, obj):
        from django.urls import reverse

        url = reverse(
            'myadmin:app_baiviet_change',
            args=[obj.pk]
        )

        return format_html(
            '''
            <a href="{}"
               style="
                    text-decoration:none;
                    color:#2d2d2d;
                    font-size:14px;
                    font-weight:600;
               ">
               {}
            </a>
            ''',
            url,
            obj.TieuDe
        )

    tieude_card.short_description = "Tiêu đề"


    def noidung_preview(self, obj):
        if not obj.NoiDung:
            return "—"

        text = strip_tags(obj.NoiDung)

        if len(text) > 80:
            text = text[:80] + "..."

        return format_html(
            '''
            <div style="
                color:#666;
                font-size:12px;
                line-height:1.5;
                max-width:320px;
            ">
                {}
            </div>
            ''',
            text
        )

    noidung_preview.short_description = "Nội dung"


    def tacgia_card(self, obj):
        return format_html(
            '''
            <span style="
                font-size:13px;
                font-weight:500;
                color:#444;
            ">
                {}
            </span>
            ''',
            obj.TacGia or "—"
        )

    tacgia_card.short_description = "Tác giả"


    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}
        js = ('ckeditor/ckeditor/ckeditor.js',)


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
    list_display_links = None
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
    list_display_links = None
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
class KhuyenMaiForm(django_forms.ModelForm):
    """Form với datetime picker HTML5 thay vì nhập tay."""
    NgayBatDau = django_forms.DateTimeField(
        required=False,
        widget=django_forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'km-input'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        label='Ngày Bắt Đầu',
    )
    NgayKetThuc = django_forms.DateTimeField(
        required=False,
        widget=django_forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'km-input'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        label='Ngày Kết Thúc',
    )
 
    class Meta:
        model = KhuyenMai
        fields = '__all__'


@admin.register(KhuyenMai, site=admin_site)
class KhuyenMaiAdmin(admin.ModelAdmin):
    form = KhuyenMaiForm
    change_form_template = "admin/khuyenmai_change_form.html"
    add_form_template    = "admin/khuyenmai_change_form.html"
 
    list_display = (
        'ma_km_card',
        'ten_km_card',
        'LoaiKhuyenMai',
        'loai_giam_badge',
        'gia_tri_display',
        'SoLuong',
        'DaSuDung',
        'trang_thai_badge',
        'NgayBatDau',
        'NgayKetThuc'
    )

    list_display_links = None
    # list_display_links = ('MaKhuyenMai',)
    search_fields  = ('MaKhuyenMai', 'TenKhuyenMai', 'MoTa')
    list_filter    = ('TrangThai', 'LoaiKhuyenMai', 'LoaiGiam')
    ordering       = ('-id_KhuyenMai',)
    list_per_page  = 20

    

    def ma_km_card(self, obj):
        url = reverse(
            'myadmin:app_khuyenmai_change',
            args=[obj.pk]
        )

        return format_html(
            '''
            <a href="{}"
            style="
                    text-decoration:none;
                    color:#2d2d2d;
                    font-size:13px;
                    font-weight:700;
            ">
                {}
            </a>
            ''',
            url,
            obj.MaKhuyenMai
        )

    ma_km_card.short_description = "Mã KM"


    def ten_km_card(self, obj):

        return format_html(
            '''
            <div style="
                font-size:13px;
                font-weight:500;
                color:#444;
            ">
                {}
            </div>
            ''',
            obj.TenKhuyenMai or "—"
        )

    ten_km_card.short_description = "Tên khuyến mãi"
 
    # ── Context ──
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        from .models import TaiKhoan as TK
        extra_context['total_accounts'] = TK.objects.filter(TrangThai_TaiKhoan='active').count()
        extra_context['count_member']   = TK.objects.filter(TrangThai_TaiKhoan='active', HangThanhVien='Member').count()
        extra_context['count_silver']   = TK.objects.filter(TrangThai_TaiKhoan='active', HangThanhVien='Silver').count()
        extra_context['count_gold']     = TK.objects.filter(TrangThai_TaiKhoan='active', HangThanhVien='Gold').count()
        extra_context['count_platinum'] = TK.objects.filter(TrangThai_TaiKhoan='active', HangThanhVien='Platinum').count()
        if object_id:
            try:
                extra_context['da_phat_so_luong'] = KhuyenMaiTaiKhoan.objects.filter(
                    id_KhuyenMai_id=int(object_id)
                ).count()
            except (ValueError, TypeError):
                extra_context['da_phat_so_luong'] = 0
        else:
            extra_context['da_phat_so_luong'] = 0
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    # ── Save + distribute ──
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
 
        action_type = request.POST.get('action_type', 'save')
        if action_type != 'send':
            return
 
        from .models import TaiKhoan as TK
        send_all   = request.POST.get('send_all') == '1'
        send_tiers = request.POST.getlist('send_tier')
 
        if send_all:
            accounts = list(TK.objects.filter(TrangThai_TaiKhoan='active'))
        elif send_tiers:
            accounts = list(TK.objects.filter(
                TrangThai_TaiKhoan='active',
                HangThanhVien__in=send_tiers
            ))
        else:
            from django.contrib import messages
            messages.warning(request, '⚠️ Chưa chọn đối tượng nhận voucher!')
            return
 
        sent = 0
        emails_to_notify = []
 
        for acc in accounts:
            exists = KhuyenMaiTaiKhoan.objects.filter(
                id_TaiKhoan=acc, id_KhuyenMai=obj
            ).exists()
            if not exists:
                KhuyenMaiTaiKhoan.objects.create(
                    id_TaiKhoan=acc,
                    id_KhuyenMai=obj,
                    DaSuDung=False,
                    NgayNhan=timezone.now(),
                )
                sent += 1
                if acc.Email:
                    emails_to_notify.append((acc.TenDangNhap or acc.Username or 'Khách hàng', acc.Email))
 
        # Gửi email thông báo
        email_sent = 0
        for ten, email_addr in emails_to_notify:
            try:
                subject = f'🎁 Ami Perfumery — Voucher ưu đãi dành cho bạn: {obj.MaKhuyenMai}'
 
                if obj.LoaiGiam == 'percent':
                    discount_text = f'Giảm {int(obj.GiaTriGiam or 0)}%'
                elif obj.LoaiGiam == 'fixed':
                    discount_text = f'Giảm {int(obj.GiaTriGiam or 0):,}₫'.replace(',', '.')
                else:
                    discount_text = 'Miễn phí vận chuyển'
 
                han_su_dung = obj.NgayKetThuc.strftime('%d/%m/%Y %H:%M') if obj.NgayKetThuc else 'Không giới hạn'
                don_toi_thieu = f'{int(obj.DonHangToiThieu or 0):,}₫'.replace(',', '.') if obj.DonHangToiThieu else 'Không yêu cầu'
 
                body = f"""Xin chào {ten},
 
Ami Perfumery gửi tặng bạn voucher ưu đãi đặc biệt:
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MÃ VOUCHER:  {obj.MaKhuyenMai}
  ƯU ĐÃI:      {discount_text}
  ĐƠN TỐI THIỂU: {don_toi_thieu}
  HẠN SỬ DỤNG: {han_su_dung}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
{obj.MoTa or ''}
 
Voucher đã được thêm vào tài khoản của bạn.
Đăng nhập tại http://localhost:8000 để sử dụng ngay!
 
Trân trọng,
Ami Perfumery Team 🌸
"""
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@ami.com'),
                    recipient_list=[email_addr],
                    fail_silently=True,
                )
                email_sent += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'Email error to {email_addr}: {e}')
 
        from django.contrib import messages
        messages.success(
            request,
            f'✅ Đã phân phối voucher "{obj.MaKhuyenMai}" cho {sent} tài khoản. '
            f'Đã gửi {email_sent} email thông báo.'
        )
 
    # ── List display ──
    def loai_giam_badge(self, obj):
        icons = {'percent': '% Phần trăm', 'fixed': '₫ Cố định', 'free_ship': '🚚 Miễn ship'}
        return icons.get(obj.LoaiGiam or '', obj.LoaiGiam or '—')
    loai_giam_badge.short_description = "Loại giảm"
 
    def gia_tri_display(self, obj):
        if not obj.GiaTriGiam:
            return '—'
        if obj.LoaiGiam == 'percent':
            return format_html('<strong>{}%</strong>', int(obj.GiaTriGiam))
        elif obj.LoaiGiam == 'fixed':
            val = f'{int(obj.GiaTriGiam):,}'.replace(',', '.')
            return format_html('<strong>{}₫</strong>', val)
        return '—'
    gia_tri_display.short_description = "Giá trị giảm"
 
    def trang_thai_badge(self, obj):
        if (obj.TrangThai or '').lower() == 'active':
            return mark_safe('<span style="color:#2e7d32;font-weight:600;">● Hoạt động</span>')
        return mark_safe('<span style="color:#9e9e9e;font-weight:600;">● Tạm dừng</span>')
    trang_thai_badge.short_description = "Trạng thái"

@admin.register(KhuyenMaiTaiKhoan, site=admin_site)
class KhuyenMaiTaiKhoanAdmin(admin.ModelAdmin):
    # Template chỉ xem — không có form chỉnh sửa
    change_form_template = "admin/khuyenmaitaikhoan_change_form.html"
 
    list_display   = ('ma_voucher', 'ten_khach_hang', 'hang_thanh_vien',
                      'da_su_dung_badge', 'NgayNhan', 'han_su_dung')
    list_display_links = ('ma_voucher', 'ten_khach_hang')
    list_display_links = None
    list_filter    = ('DaSuDung', 'id_KhuyenMai', 'id_TaiKhoan__HangThanhVien')
    search_fields  = ('id_TaiKhoan__TenDangNhap', 'id_TaiKhoan__Email',
                      'id_KhuyenMai__MaKhuyenMai', 'id_KhuyenMai__TenKhuyenMai')
    ordering       = ('-NgayNhan',)
    list_per_page  = 30
 
    # Không cho thêm mới — chỉ phân phối qua form KhuyenMai
    def has_add_permission(self, request):
        return False
 
    # Không cho chỉnh sửa — chỉ xem + xóa
    def has_change_permission(self, request, obj=None):
        # Vẫn trả về True để Django cho phép truy cập URL change
        # nhưng template sẽ hiển thị read-only
        return True
 
    def get_readonly_fields(self, request, obj=None):
        # Tất cả field đều read-only
        if obj:
            return [f.name for f in obj._meta.fields]
        return []
 
    # ── List display ──
    def ma_voucher(self, obj):
        if not obj.id_KhuyenMai:
            return '—'
        return format_html(
            '<span style="font-family:monospace;font-weight:700;color:var(--olive,#4B672D);'
            'background:rgba(75,103,45,.08);padding:3px 10px;border-radius:20px;">{}</span>',
            obj.id_KhuyenMai.MaKhuyenMai
        )
    ma_voucher.short_description = "Mã voucher"
 
    def ten_khach_hang(self, obj):
        if not obj.id_TaiKhoan:
            return '—'
        ten = obj.id_TaiKhoan.TenDangNhap or obj.id_TaiKhoan.Username or '—'
        email = obj.id_TaiKhoan.Email or ''
        return format_html(
            '<div style="line-height:1.4;">'
            '<strong style="font-size:13px;">{}</strong>'
            '<div style="font-size:11px;color:#9e9e9e;">{}</div>'
            '</div>',
            ten, email
        )
    ten_khach_hang.short_description = "Khách hàng"
 
    def hang_thanh_vien(self, obj):
        if not obj.id_TaiKhoan:
            return '—'
        hang = obj.id_TaiKhoan.HangThanhVien or 'Member'
        colors = {
            'Member':   ('#eceff1', '#546e7a', '🥉'),
            'Silver':   ('#e3f2fd', '#1565c0', '🥈'),
            'Gold':     ('#fff8e1', '#f57f17', '🥇'),
            'Platinum': ('#f3e5f5', '#6a1b9a', '💎'),
        }
        bg, fg, icon = colors.get(hang, ('#f5f5f5', '#616161', ''))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:20px;'
            'font-size:11px;font-weight:600;">{} {}</span>',
            bg, fg, icon, hang
        )
    hang_thanh_vien.short_description = "Hạng"
 
    def da_su_dung_badge(self, obj):
        if obj.DaSuDung:
            return mark_safe('<span style="background:#fce4ec;color:#c62828;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">✗ Đã sử dụng</span>')
        return mark_safe('<span style="background:#e8f5e9;color:#2e7d32;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">✓ Chưa dùng</span>')
    da_su_dung_badge.short_description = "Tình trạng"
 
    def han_su_dung(self, obj):
        if not obj.id_KhuyenMai:
            return '—'
        ngay = obj.id_KhuyenMai.NgayKetThuc
        if not ngay:
            return mark_safe('<span style="color:#9e9e9e;">Không giới hạn</span>')
        from django.utils import timezone
        if ngay < timezone.now():
            return format_html(
                '<span style="color:#c62828;">{}</span>',
                ngay.strftime('%d/%m/%Y')
            )
        return format_html(
            '<span style="color:#2e7d32;">{}</span>',
            ngay.strftime('%d/%m/%Y')
        )
    han_su_dung.short_description = "Hạn dùng"
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}


# ═══════════════════════════════════════
#  TaiKhoan
# ═══════════════════════════════════════
@admin.register(TaiKhoan, site=admin_site)
class TaiKhoanAdmin(admin.ModelAdmin):
    change_form_template = "admin/taikhoan_change_form.html"
    add_form_template    = "admin/taikhoan_change_form.html"

    list_display       = ('email_with_avatar', 'ten_dang_nhap', 'SDT', 'hang_badge', 'trang_thai_toggle', 'NgayTao')
    # list_display_links = ('email_with_avatar', 'ten_dang_nhap')
    list_display_links = None
    search_fields      = ('TenDangNhap', 'Username', 'Email', 'SDT')
    list_filter        = ('TrangThai_TaiKhoan', 'LoaiTaiKhoan', 'HangThanhVien')
    ordering           = ('-NgayTao',)
    list_per_page      = 25
    actions            = ['action_lock', 'action_unlock']

    # ── Actions ──────────────────────────────────────────────────
    def action_lock(self, request, queryset):
        queryset.update(TrangThai_TaiKhoan='locked')
        self.message_user(request, f'Đã khóa {queryset.count()} tài khoản.')
    action_lock.short_description = 'Khóa tài khoản đã chọn'

    def action_unlock(self, request, queryset):
        queryset.update(TrangThai_TaiKhoan='active')
        self.message_user(request, f'Đã mở khóa {queryset.count()} tài khoản.')
    action_unlock.short_description = 'Mở khóa tài khoản đã chọn'

    # ── Context cho form chi tiết ─────────────────────────────────
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            try:
                oid = int(object_id)
                from .models import KhachHang, DonHang, KhuyenMaiTaiKhoan as KMTK
                customer = KhachHang.objects.filter(id_TaiKhoan_id=oid).first()
                so_don   = DonHang.objects.filter(id_KhachHang=customer).count() if customer else 0
                extra_context['so_don_hang'] = so_don
                extra_context['vouchers']    = KMTK.objects.filter(
                    id_TaiKhoan_id=oid
                ).select_related('id_KhuyenMai').order_by('-NgayNhan')[:10]
                extra_context['lock_reason'] = ''
            except (ValueError, TypeError):
                extra_context['so_don_hang'] = 0
                extra_context['vouchers']    = []
        else:
            extra_context['so_don_hang'] = 0
            extra_context['vouchers']    = []
        return super().changeform_view(request, object_id, form_url, extra_context)

    # ── Save — ghi LogEntry ───────────────────────────────────────
    def save_model(self, request, obj, form, change):
        old_status = None
        if change and obj.pk:
            try:
                old_status = TaiKhoan.objects.filter(pk=obj.pk).values_list(
                    'TrangThai_TaiKhoan', flat=True
                ).first()
            except Exception:
                pass

        super().save_model(request, obj, form, change)

        new_status = obj.TrangThai_TaiKhoan
        if old_status and old_status != new_status:
            from django.contrib.admin.models import LogEntry, CHANGE
            from django.contrib.contenttypes.models import ContentType
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(obj).pk,
                object_id       = obj.pk,
                object_repr     = str(obj),
                action_flag     = CHANGE,
                change_message  = f'Đổi trạng thái: {old_status} → {new_status}',
            )
            from django.contrib import messages as dj_msg
            lbl = 'Đã khóa' if new_status == 'locked' else 'Đã mở khóa'
            dj_msg.success(request, f'{lbl} tài khoản {obj.TenDangNhap}.')

    # ── Xóa ──────────────────────────────────────────────────────
    def delete_model(self, request, obj):
        self._do_delete(obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self._do_delete(obj)

    def response_delete(self, request, obj_display, obj_id):
        from django.contrib import messages as dj_msg
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        dj_msg.success(request, f'Đã xóa tài khoản "{obj_display}" thành công.')
        return HttpResponseRedirect(reverse('myadmin:app_taikhoan_changelist'))

    def _do_delete(self, obj):
        from django.db import connection
        pk = obj.pk

        # ── 1. Bảng độc lập ──────────────────────────────────────
        for table in ('BinhLuan', 'NhanVien', 'PhieuNhap',
                      'LichSuDiem', 'YeuThich', 'KhuyenMai_TaiKhoan'):
            with connection.cursor() as c:
                c.execute(f"DELETE FROM {table} WHERE id_TaiKhoan = %s", [pk])

        # ── 2. HoiDap — self-ref parent_id ───────────────────────
        # 2a. NULL hoá parent_id của reply do chính user này viết
        with connection.cursor() as c:
            c.execute(
                "UPDATE HoiDap SET parent_id = NULL "
                "WHERE id_TaiKhoan = %s AND parent_id IS NOT NULL", [pk]
            )
        # 2b. Xóa reply (con) của các câu hỏi do user này đặt
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM HoiDap WHERE parent_id IN "
                "(SELECT id_HoiDap FROM HoiDap WHERE id_TaiKhoan = %s)", [pk]
            )
        # 2c. Xóa toàn bộ HoiDap còn lại của user
        with connection.cursor() as c:
            c.execute("DELETE FROM HoiDap WHERE id_TaiKhoan = %s", [pk])

        # ── 3. DanhGia — self-ref parent_id ──────────────────────
        with connection.cursor() as c:
            c.execute(
                "UPDATE DanhGia SET parent_id = NULL "
                "WHERE id_TaiKhoan = %s AND parent_id IS NOT NULL", [pk]
            )
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM DanhGia WHERE parent_id IN "
                "(SELECT id_DanhGia FROM DanhGia WHERE id_TaiKhoan = %s)", [pk]
            )
        with connection.cursor() as c:
            c.execute("DELETE FROM DanhGia WHERE id_TaiKhoan = %s", [pk])

        # ── 4. Thu thập id_GiaoHang của user (trực tiếp) ─────────
        giao_hang_ids = set()
        with connection.cursor() as c:
            c.execute(
                "SELECT id_GiaoHang FROM GiaoHang WHERE id_TaiKhoan = %s", [pk]
            )
            for r in c.fetchall():
                giao_hang_ids.add(r[0])

        # ── 5. Lấy id_KhachHang ──────────────────────────────────
        id_kh = None
        with connection.cursor() as c:
            c.execute(
                "SELECT id_KhachHang FROM KhachHang WHERE id_TaiKhoan = %s", [pk]
            )
            row = c.fetchone()
            if row:
                id_kh = row[0]

        if id_kh:
            # 5a. Thu thập thêm id_GiaoHang từ DonHang của khách
            with connection.cursor() as c:
                c.execute(
                    "SELECT DISTINCT id_GiaoHang FROM DonHang "
                    "WHERE id_KhachHang = %s AND id_GiaoHang IS NOT NULL", [id_kh]
                )
                for r in c.fetchall():
                    giao_hang_ids.add(r[0])

            # 5b. Xóa ChiTietDonHang
            with connection.cursor() as c:
                c.execute(
                    "DELETE FROM ChiTietDonHang WHERE id_DonHang IN "
                    "(SELECT id_DonHang FROM DonHang WHERE id_KhachHang = %s)", [id_kh]
                )

            # 5c. Xóa DonHang (chưa xóa GiaoHang)
            with connection.cursor() as c:
                c.execute("DELETE FROM DonHang WHERE id_KhachHang = %s", [id_kh])

            # 5d. Xóa KhachHang
            with connection.cursor() as c:
                c.execute("DELETE FROM KhachHang WHERE id_KhachHang = %s", [id_kh])

        # ── 6. NULL hoá MỌI DonHang còn lại trỏ vào GiaoHang ────
        #    (DonHang của KhachHang khác nhưng dùng GiaoHang của user này)
        if giao_hang_ids:
            placeholders = ','.join(['%s'] * len(giao_hang_ids))
            ids = list(giao_hang_ids)
            with connection.cursor() as c:
                c.execute(
                    f"UPDATE DonHang SET id_GiaoHang = NULL "
                    f"WHERE id_GiaoHang IN ({placeholders})",
                    ids
                )
            # 6b. Bây giờ mới an toàn xóa GiaoHang
            with connection.cursor() as c:
                c.execute(
                    f"DELETE FROM GiaoHang WHERE id_GiaoHang IN ({placeholders})",
                    ids
                )

        # ── 7. Xóa TaiKhoan sau cùng ─────────────────────────────
        obj.delete()

    # ── List display ─────────────────────────────────────────────
    def ten_dang_nhap(self, obj):
        return format_html(
            '<div style="line-height:1.4;">'
            '<strong style="font-size:13px;">{}</strong>'
            '<div style="font-size:11px;color:#9e9e9e;">@{}</div>'
            '</div>',
            obj.TenDangNhap or '—', obj.Username or '—'
        )
    ten_dang_nhap.short_description = "Họ tên"

    def email_with_avatar(self, obj):
        import hashlib
        email = (obj.Email or '').strip().lower()
        initials = (obj.TenDangNhap or email or '?')[0].upper()

        mono_style = (
            "width:36px;height:36px;border-radius:50%;"
            "background:linear-gradient(135deg,#4B672D,#7a9e50);"
            "color:#EBF6C4;font-size:13px;font-weight:700;"
            "display:inline-flex;align-items:center;justify-content:center;"
            "flex-shrink:0;font-family:sans-serif;vertical-align:middle;"
            "border:2px solid rgba(75,103,45,.25);"
        )
        wrap_style = (
            "display:inline-flex;align-items:center;justify-content:center;"
            "width:36px;height:36px;border-radius:50%;flex-shrink:0;"
            "overflow:hidden;border:2px solid rgba(75,103,45,.25);"
            "vertical-align:middle;background:#f0f0f0;"
        )
        img_style = (
            "width:36px;height:36px;object-fit:cover;"
            "border-radius:50%;display:block;"
        )

        if email:
            if email.endswith('@gmail.com'):
                username = email.split('@')[0]
                avatar_src = f"https://unavatar.io/gmail/{username}"
            else:
                md5 = hashlib.md5(email.encode()).hexdigest()
                avatar_src = f"https://www.gravatar.com/avatar/{md5}?s=40&d=mp"

            # onerror: thay toàn bộ wrap bằng monogram span
            onerror = (
                f"this.parentNode.outerHTML="
                f"'<span style=&quot;{mono_style}&quot;>{initials}</span>'"
            )
            avatar_html = (
                f'<span style="{wrap_style}" id="av-{hash(email)}">'
                f'<img src="{avatar_src}" style="{img_style}" onerror="{onerror}">'
                f'</span>'
            )
        else:
            avatar_html = f'<span style="{mono_style}">?</span>'

        return format_html(
            '<div style="display:flex;align-items:center;gap:10px;padding:2px 0;">'
            '{}'
            '<span style="font-size:13px;color:#1a1c14;">{}</span>'
            '</div>',
            mark_safe(avatar_html),
            email or '—'
        )
    email_with_avatar.short_description = "E-Mail"

    def hang_badge(self, obj):
        hang = obj.HangThanhVien or 'Member'
        cfg  = {
            'Member':   ('#eceff1', '#546e7a', '🥉'),
            'Silver':   ('#e3f2fd', '#1565c0', '🥈'),
            'Gold':     ('#fff8e1', '#f57f17', '🥇'),
            'Platinum': ('#f3e5f5', '#6a1b9a', '💎'),
        }
        bg, fg, icon = cfg.get(hang, ('#f5f5f5', '#616161', ''))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">{} {}</span>',
            bg, fg, icon, hang
        )
    hang_badge.short_description = "Hạng"

    def trang_thai_toggle(self, obj):
        tt  = (obj.TrangThai_TaiKhoan or 'active').lower()
        url = f'/admin/app/taikhoan/{obj.pk}/change/'
        if tt == 'active':
            return mark_safe(
                f'<a href="{url}" title="Đang hoạt động — click để vào form quản lý" '
                f'style="display:inline-flex;align-items:center;gap:7px;text-decoration:none;">'
                f'<span style="width:38px;height:22px;background:#2e7d32;border-radius:20px;'
                f'display:inline-flex;align-items:center;padding:3px;flex-shrink:0;">'
                f'<span style="width:16px;height:16px;background:#fff;border-radius:50%;'
                f'margin-left:16px;box-shadow:0 1px 3px rgba(0,0,0,.25);"></span></span>'
                f'<span style="font-size:11px;color:#2e7d32;font-weight:600;">Hoạt động</span>'
                f'</a>'
            )
        return mark_safe(
            f'<a href="{url}" title="Đã khóa — click để vào form quản lý" '
            f'style="display:inline-flex;align-items:center;gap:7px;text-decoration:none;">'
            f'<span style="width:38px;height:22px;background:#c62828;border-radius:20px;'
            f'display:inline-flex;align-items:center;padding:3px;flex-shrink:0;">'
            f'<span style="width:16px;height:16px;background:#fff;border-radius:50%;'
            f'margin-left:2px;box-shadow:0 1px 3px rgba(0,0,0,.25);"></span></span>'
            f'<span style="font-size:11px;color:#c62828;font-weight:600;">Đã khóa</span>'
            f'</a>'
        )
    trang_thai_toggle.short_description = "Trạng thái"

    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}


# ═══════════════════════════════════════
#  KhachHang
# ═══════════════════════════════════════
@admin.register(KhachHang, site=admin_site)
class KhachHangAdmin(admin.ModelAdmin):
    list_display  = ('id_KhachHang', 'TenKhachHang', 'get_email', 'DiaChi', 'GioiTinh')
    list_display_links = None
    search_fields = ('TenKhachHang', 'id_TaiKhoan__Email', 'id_TaiKhoan__Username')
    list_filter   = ('GioiTinh',)
    list_per_page = 25

    def get_email(self, obj):
        try: return obj.id_TaiKhoan.Email
        except: return "—"
    get_email.short_description = "Email"


# ─── NHÀ CUNG CẤP ────────────────────────────────────────────
@admin.register(NhaCungCap, site=admin_site)
class NhaCungCapAdmin(admin.ModelAdmin):
    list_display  = ('id_NCC', 'Ten_NCC', 'SDT', 'Email', 'DiChi')
    search_fields = ('Ten_NCC', 'SDT', 'Email')
    list_per_page = 20
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}
 
 
# ─── PHIẾU NHẬP ──────────────────────────────────────────────
@admin.register(PhieuNhap, site=admin_site)
class PhieuNhapAdmin(admin.ModelAdmin):
    change_list_template = "admin/app/phieunhap/change_list.html"
    change_form_template = "admin/phieunhap_change_form.html"
    add_form_template    = "admin/phieunhap_change_form.html"
 
    list_display  = (
        'ma_phieu_display', 'ThoiGian', 'ten_nguoi_nhap',
        'ten_ncc', 'tong_tien_display', 'trang_thai_badge', 'so_san_pham'
    )
    list_display_links = None
    list_filter   = ('TrangThai', 'ThoiGian')
    search_fields = ('MaPhieu', 'id_TaiKhoan__TenDangNhap', 'id_NCC__Ten_NCC')
    ordering      = ('-ThoiGian',)
    list_per_page = 20
 
    # ── List display helpers ──────────────────────────────────
    def ma_phieu_display(self, obj):

        url = reverse('myadmin:app_phieunhap_change', args=[obj.pk])

        return format_html(
            '''
            <a href="{}" style="
                text-decoration:none;
                color:#2d2d2d;
                font-size:14px;
                font-weight:600;
            ">
                {}
            </a>
            ''',
            url,
            obj.MaPhieu or f'PN-{obj.id_PhieuNhap}'
        )

    ma_phieu_display.short_description = "Mã phiếu"
    
    def ten_nguoi_nhap(self, obj):
        if obj.id_TaiKhoan:
            return format_html(
                '<span>{}</span><br><small style="color:#888;">{}</small>',
                obj.id_TaiKhoan.TenDangNhap or '—',
                obj.id_TaiKhoan.LoaiTaiKhoan or ''
            )
        return '—'
    ten_nguoi_nhap.short_description = "Người nhập"
 
    def ten_ncc(self, obj):
        return obj.id_NCC.Ten_NCC if obj.id_NCC else '—'
    ten_ncc.short_description = "Nhà cung cấp"
 
    def tong_tien_display(self, obj):
        if obj.TongTien:
            return format_html(
                '<strong style="color:#4B672D;">{}</strong>',
                f"{int(obj.TongTien):,}".replace(",", ".") + "₫"
            )
        return '—'
    tong_tien_display.short_description = "Tổng tiền"
 
    def trang_thai_badge(self, obj):
        colors = {
            'draft':     ('#fff8e1', '#f57f17', '📝 Nháp'),
            'confirmed': ('#e3f2fd', '#1565c0', '✅ Xác nhận'),
            'done':      ('#e8f5e9', '#2e7d32', '✔ Hoàn tất'),
            'cancelled': ('#fce4ec', '#c62828', '✖ Huỷ'),
        }
        bg, fg, label = colors.get(
            obj.TrangThai or 'draft',
            ('#f5f5f5', '#616161', obj.TrangThai or 'Nháp')
        )
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, label
        )
    trang_thai_badge.short_description = "Trạng thái"
 
    def so_san_pham(self, obj):
        count = obj.chi_tiet.count()
        return format_html('<span style="font-weight:600;">{} dòng</span>', count)
    so_san_pham.short_description = "Chi tiết"


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            from django.urls import reverse
            extra_context['xuat_excel_url'] = reverse('admin-api-xuat-excel') + '?tat_ca=1'
        except Exception:
            extra_context['xuat_excel_url'] = '/admin/api/xuat-excel/?tat_ca=1'
        return super().changelist_view(request, extra_context=extra_context)
 
    # ── Change form context ───────────────────────────────────
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id and not str(object_id).isdigit():
         raise Http404("object_id không hợp lệ")
        extra_context = extra_context or {}
 
        # Danh sách NCC + sản phẩm + tài khoản cho dropdowns
        extra_context['ncc_list']    = list(NhaCungCap.objects.values('id_NCC', 'Ten_NCC', 'SDT', 'Email'))
        extra_context['san_pham_list'] = [
            {
                'id_SanPham': sp.pk,
                'TenSanPham': sp.TenSanPham or '',
                'id_ThuongHieu__TenThuongHieu': sp.id_ThuongHieu.TenThuongHieu if sp.id_ThuongHieu else '',
            }
            for sp in SanPham.objects.select_related('id_ThuongHieu').order_by('TenSanPham')
        ]
        extra_context['tk_info'] = {
            'username': request.user.username,
            'role':     'Admin' if request.user.is_superuser else 'Staff',
        }
        extra_context['now'] = tz.now().strftime('%d/%m/%Y %H:%M')
 
        # Nếu đang xem phiếu cũ, lấy chi tiết
        if object_id:
            try:
                phieu = PhieuNhap.objects.get(pk=object_id)
                chi_tiet_qs = phieu.chi_tiet.select_related(
                    'id_BienThe__id_SanPham',
                    'id_BienThe__id_SanPham__id_ThuongHieu'
                ).all()
 
                chi_tiet_list = []
                for ct in chi_tiet_qs:
                    bt = ct.id_BienThe
                    sp = bt.id_SanPham if bt else None
                    chi_tiet_list.append({
                        'id':         ct.id_ChiTietNhap,
                        'san_pham':   sp.TenSanPham if sp else '—',
                        'thuong_hieu': sp.id_ThuongHieu.TenThuongHieu if sp and sp.id_ThuongHieu else '—',
                        'sku':        bt.Sku if bt else '—',
                        'gia_nhap':   float(ct.GiaNhap or 0),
                        'so_luong':   ct.SoLuongNhap or 0,
                        'thanh_tien': float((ct.GiaNhap or 0) * (ct.SoLuongNhap or 0)),
                        'bien_the_id': bt.id_BienThe if bt else None,
                        'is_new_product': False,
                    })
                extra_context['chi_tiet_list'] = chi_tiet_list
                extra_context['phieu'] = phieu
            except PhieuNhap.DoesNotExist:
                pass
 
        return super().changeform_view(request, object_id, form_url, extra_context)
 
    # ── Save ──────────────────────────────────────────────────
    def save_model(self, request, obj, form, change):
        # Gán ngày + người nhập nếu tạo mới
        if not change:
            obj.ThoiGian = tz.now()
            try:
                from .models import TaiKhoan as TK
                tk = TK.objects.filter(Username=request.user.username).first()
                if tk:
                    obj.id_TaiKhoan = tk
            except Exception:
                pass
        super().save_model(request, obj, form, change)
 
    class Media:
        css = {'all': ('admin/css/ami_luxury.css',)}
        js  = ('admin/js/phieunhap.js',)
 
 

 
