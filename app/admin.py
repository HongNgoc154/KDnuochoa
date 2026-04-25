from django.contrib import admin
# from django.template.response import TemplateResponse
from django.contrib.auth.models import User, Group
from .models import BienThe, BienTheThuocTinh, GiaTriThuocTinh, LoaiSanPham, NhomHuong, SanPham, ThuocTinh, ThuongHieu
# from app.admin import admin_site 

class MyAdminSite(admin.AdminSite):
    site_header = "Ami Admin"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            "total_orders": 120,
            "total_users": 45,
            "revenue": 25000000,
        })
        return super().index(request, extra_context)

admin_site = MyAdminSite(name='myadmin')
admin_site.register(User)
admin_site.register(Group)


# 
class BienTheThuocTinhInline(admin.TabularInline):
    model = BienTheThuocTinh
    extra = 1
    autocomplete_fields = ('id_GiaTriThuocTinh',)

# class BienTheInline(admin.TabularInline):
#     model = BienThe
#     extra = 1
#     fields = ('id_DungTich', 'GiaBan', 'SoLuong')

@admin.register(SanPham, site=admin_site)
class SanPhamAdmin(admin.ModelAdmin):
    # list_display = ('TenSanPham', 'TrangThai_SanPham', 'id_ThuongHieu')
    # inlines = [BienTheInline]
    list_display = ('TenSanPham', 'TrangThai_SanPham', 'id_ThuongHieu', 'id_LoaiSanPham', 'id_NhomHuong')
    search_fields = ('TenSanPham',)
    list_filter = ('TrangThai_SanPham', 'id_ThuongHieu', 'id_LoaiSanPham', 'id_NhomHuong')

    # 👇 QUAN TRỌNG
    fieldsets = (
        ('Thông tin sản phẩm', {
            'fields': (
                'TenSanPham',
                'MoTa_SanPham',
                'TrangThai_SanPham',
                'id_ThuongHieu',
                'id_LoaiSanPham',
                'id_NhomHuong',
            )
        }),
    )

@admin.register(BienThe, site=admin_site)
class BienTheAdmin(admin.ModelAdmin):
    inlines = [BienTheThuocTinhInline]
    list_display = ('id_BienThe', 'id_SanPham', 'Sku', 'GiaNhap', 'GiaBan', 'SoLuong')
    search_fields = ('Sku', 'id_SanPham__TenSanPham')
    list_filter = ('id_SanPham__id_ThuongHieu', 'id_SanPham__id_LoaiSanPham')
    autocomplete_fields = ('id_SanPham',)


@admin.register(ThuocTinh, site=admin_site)
class ThuocTinhAdmin(admin.ModelAdmin):
    list_display = ('id_ThuocTinh', 'TenThuocTinh')
    search_fields = ('TenThuocTinh',)


@admin.register(GiaTriThuocTinh, site=admin_site)
class GiaTriThuocTinhAdmin(admin.ModelAdmin):
    list_display = ('id_GiaTriThuocTinh', 'GiaTri', 'id_ThuocTinh')
    list_filter = ('id_ThuocTinh',)
    search_fields = ('GiaTri', 'id_ThuocTinh__TenThuocTinh')
    autocomplete_fields = ('id_ThuocTinh',)


@admin.register(BienTheThuocTinh, site=admin_site)
class BienTheThuocTinhAdmin(admin.ModelAdmin):
    list_display = ('id_BienThe', 'id_GiaTriThuocTinh')
    list_filter = ('id_GiaTriThuocTinh__id_ThuocTinh',)
    autocomplete_fields = ('id_BienThe', 'id_GiaTriThuocTinh')


admin_site.register(ThuongHieu)
admin_site.register(LoaiSanPham)
admin_site.register(NhomHuong)