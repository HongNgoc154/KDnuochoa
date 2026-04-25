from django.contrib import admin
from django.template.response import TemplateResponse
from django.contrib.auth.models import User, Group
from .models import *
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

# 👇 QUAN TRỌNG
admin_site.register(User)
admin_site.register(Group)


# 
class BienTheThuocTinhInline(admin.TabularInline):
    model = BienTheThuocTinh
    extra = 1

class BienTheInline(admin.TabularInline):
    model = BienThe
    extra = 1
    fields = ('id_DungTich', 'GiaBan', 'SoLuong')

@admin.register(SanPham, site=admin_site)
class SanPhamAdmin(admin.ModelAdmin):
    list_display = ('TenSanPham', 'TrangThai_SanPham', 'id_ThuongHieu')
    inlines = [BienTheInline]
    search_fields = ('TenSanPham',)
    list_filter = ('TrangThai_SanPham',)

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