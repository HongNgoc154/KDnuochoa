from .models import LoaiSanPham, ThuongHieu

def global_data(request):
    return {
        "nav_categories": LoaiSanPham.objects.all(),
        "nav_brands": ThuongHieu.objects.all()[:6],
    }