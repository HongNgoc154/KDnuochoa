from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request,'app/home.html')

def category(request, segment='tat-ca'):
    category_map = {
        'tat-ca': {
            'page_title': 'Ami Perfumery – Tất cả nước hoa',
            'segment': 'all',
            'eyebrow': 'Ami Selection',
            'title': 'Tất cả nước hoa',
            'subtitle': 'Khám phá toàn bộ bộ sưu tập niche cao cấp cho Nam, Nữ và Unisex.',
            'breadcrumb': 'Tất cả',
        },
        'nam': {
            'page_title': 'Ami Perfumery – Nước hoa Nam',
            'segment': 'men',
            'eyebrow': 'For Him',
            'title': 'Nước hoa Nam',
            'subtitle': 'Tuyển chọn các tầng hương woody, leathery, citrus hiện đại dành cho quý ông thanh lịch.',
            'breadcrumb': 'Nam',
        },
        'nu': {
            'page_title': 'Ami Perfumery – Nước hoa Nữ',
            'segment': 'women',
            'eyebrow': 'For Her',
            'title': 'Nước hoa Nữ',
            'subtitle': 'Những hương floral, musky và gourmand thanh lịch tôn lên vẻ nữ tính tinh tế.',
            'breadcrumb': 'Nữ',
        },
        'unisex': {
            'page_title': 'Ami Perfumery – Nước hoa Unisex',
            'segment': 'unisex',
            'eyebrow': 'For All',
            'title': 'Nước hoa Unisex',
            'subtitle': 'Mùi hương cân bằng giữa hiện đại và cảm xúc, phù hợp cho mọi phong cách.',
            'breadcrumb': 'Unisex',
        },
    }
    context = category_map.get(segment, category_map['tat-ca'])
    return render(request, 'app/category.html', context)


def product_detail(request, id):
    return render(request, 'app/product.html')
