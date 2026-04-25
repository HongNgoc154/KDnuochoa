from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.utils.text import slugify

from .models import BaiViet, BienThe, HinhAnh, SanPham, ThuongHieu


# Create your views here.
FALLBACK_IMAGES = {
    "default": "https://images.unsplash.com/photo-1541643600914-78b084683702?auto=format&fit=crop&w=900&q=80",
    "brand_hero": "https://images.unsplash.com/photo-1610461888750-10bfc601b874?auto=format&fit=crop&w=1800&q=80",
    "brand_poster": "https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?auto=format&fit=crop&w=900&q=80",
    "brand_about": "https://images.unsplash.com/photo-1615634260167-c8cdede054de?auto=format&fit=crop&w=1200&q=80",
    "article_cover": "https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=1600&q=80",
}


def _format_currency(value):
    if value is None:
        return "Liên hệ"
    return f"{int(value):,}".replace(",", ".") + "₫"


def _product_image_map(product_ids):
    image_rows = (
        HinhAnh.objects.filter(id_SanPham_id__in=product_ids)
        .order_by("id_HinhAnh")
        .values("id_SanPham_id", "url")
    )
    image_map = {}
    for row in image_rows:
        product_id = row["id_SanPham_id"]
        image_map.setdefault(product_id, row["url"])
    return image_map


def _build_product_cards(products):
    product_ids = [item.id_SanPham for item in products]
    image_map = _product_image_map(product_ids)

    variant_prices = {}
    for row in BienThe.objects.filter(id_SanPham_id__in=product_ids).values("id_SanPham_id", "GiaBan", "SoLuong"):
        product_id = row["id_SanPham_id"]
        current = variant_prices.get(product_id)
        if current is None or row["GiaBan"] < current["price"]:
            variant_prices[product_id] = {"price": row["GiaBan"], "stock": row["SoLuong"]}

    cards = []
    for product in products:
        variant_info = variant_prices.get(product.id_SanPham, {"price": None, "stock": 0})
        cards.append(
            {
                "id": product.id_SanPham,
                "name": product.TenSanPham,
                "brand": product.id_ThuongHieu.TenThuongHieu,
                "brand_slug": slugify(product.id_ThuongHieu.TenThuongHieu),
                "group": product.id_NhomHuong.TenNhomHuong,
                "price": _format_currency(variant_info["price"]),
                "price_raw": int(variant_info["price"] or 0),
                "stock": variant_info["stock"] or 0,
                "is_new": product.TrangThai_SanPham.lower() == "active",
                "image": image_map.get(product.id_SanPham, FALLBACK_IMAGES["default"]),
            }
        )
    return cards




def home(request):
    return render(request, "app/home.html")

def category(request, segment='tat-ca'):
    category_map = {
        "tat-ca": {
            "page_title": "Ami Perfumery – Tất cả nước hoa",
            "segment": "all",
            "eyebrow": "Ami Selection",
            "title": "Tất cả nước hoa",
            "subtitle": "Khám phá toàn bộ bộ sưu tập niche cao cấp cho Nam, Nữ và Unisex.",
            "breadcrumb": "Tất cả",
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
    context = category_map.get(segment, category_map["tat-ca"])

    products = SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham", "id_NhomHuong").all()
    if segment == "nam":
        products = products.filter(id_LoaiSanPham__TenLoaiSanPham__icontains="nam")
    elif segment == "nu":
        products = products.filter(id_LoaiSanPham__TenLoaiSanPham__icontains="nữ")
    elif segment == "unisex":
        products = products.filter(id_LoaiSanPham__TenLoaiSanPham__icontains="unisex")

    context["products"] = _build_product_cards(products)
    context["product_count"] = len(context["products"])

    return render(request, "app/category.html", context)


def product_detail(request):
    return render(request, "app/product.html")


def brand_list(request):
    brand_names = list(ThuongHieu.objects.values_list("TenThuongHieu", flat=True))
    brands = []
    for name in brand_names:
        slug = slugify(name)
        brands.append(
            {
                "slug": slug,
                "name": name,
                "tagline": "Tinh hoa mùi hương đẳng cấp",
                "palette": "#6f7d62",
                "poster_image": FALLBACK_IMAGES["brand_poster"],
            }
        )
    return render(request, "app/brand_list.html", {"brands": brands})


def brand_detail(request, slug):
    brand_obj = next((item for item in ThuongHieu.objects.all() if slugify(item.TenThuongHieu) == slug), None)
    if brand_obj is None:
        first_brand = ThuongHieu.objects.first()
        if not first_brand:
            return render(request, "app/brand_detail.html", {"brand": {}, "products": [], "pinned_products": []})
        brand_obj = first_brand

    brand_products = SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham", "id_NhomHuong").filter(
        id_ThuongHieu=brand_obj
    )
    products = _build_product_cards(brand_products)

    brand = {
        "slug": slugify(brand_obj.TenThuongHieu),
        "name": brand_obj.TenThuongHieu,
        "tagline": "Di sản mùi hương tinh tế",
        "palette": "#6f7d62",
        "hero_image": FALLBACK_IMAGES["brand_hero"],
        "about_image": FALLBACK_IMAGES["brand_about"],
        "story": f"{brand_obj.TenThuongHieu} là thương hiệu được yêu thích trong bộ sưu tập nước hoa tại Ami.",
        "philosophy": "Tập trung vào chiều sâu mùi hương, sự cân bằng và tính ứng dụng mỗi ngày.",
        "signature_notes": ["Citrus", "Floral", "Woody"],
    }

    return render(
        request,
        "app/brand_detail.html",
        {
            "brand": brand,
            "products": products,
            "pinned_products": products[:2],
        },
    )


def blog_list(request):
    articles_qs = BaiViet.objects.order_by("-NgayTao")
    articles = []
    for item in articles_qs:
        articles.append(
            {
                "slug": slugify(item.TieuDe),
                "title": item.TieuDe,
                "category": "Blog",
                "audience": "unisex",
                "author": item.TacGia,
                "published_at": item.NgayTao.strftime("%d/%m/%Y") if item.NgayTao else "",
                "cover": FALLBACK_IMAGES["article_cover"],
                "excerpt": (item.NoiDung or "")[:140],
                "body": [{"type": "p", "text": item.NoiDung or "Nội dung đang được cập nhật."}],
            }
        )

    featured_articles = articles[:2]
    bento_articles = articles[2:]
    popular_articles = articles[:5]
    return render(
        request,
        "app/blog.html",
        {
            "featured_articles": featured_articles,
            "bento_articles": bento_articles,
            "popular_articles": popular_articles,
        },
    )


def article_detail(request, slug):
    articles_qs = list(BaiViet.objects.order_by("-NgayTao"))
    if not articles_qs:
        return render(request, "app/article_detail.html", {"article": {}, "related_articles": [], "suggested_products": []})


    article_obj = next((item for item in articles_qs if slugify(item.TieuDe) == slug), articles_qs[0])

    article = {
        "slug": slugify(article_obj.TieuDe),
        "title": article_obj.TieuDe,
        "category": "Blog",
        "author": article_obj.TacGia,
        "published_at": article_obj.NgayTao.strftime("%d/%m/%Y") if article_obj.NgayTao else "",
        "cover": FALLBACK_IMAGES["article_cover"],
        "body": [{"type": "p", "text": article_obj.NoiDung or "Nội dung đang được cập nhật."}],
    }
    related_articles = [
        {
            "slug": slugify(item.TieuDe),
            "title": item.TieuDe,
            "category": "Blog",
            "cover": FALLBACK_IMAGES["article_cover"],
        }
        for item in articles_qs
        if item.id_BaiViet != article_obj.id_BaiViet
    ][:5]

    suggested_products = _build_product_cards(
        SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham", "id_NhomHuong").all()[:5]
    )

    return render(
        request,
        "app/article_detail.html",
        {
            "article": article,
            "related_articles": related_articles,
            "suggested_products": suggested_products,
        },
    )


def contact_page(request):
    faq_items = [
        {
            "question": "Ami có tư vấn chọn mùi theo cá tính không?",
            "answer": "Có. Đội ngũ tư vấn 1:1 theo nhu cầu đi làm, đi tiệc, du lịch và ngân sách của bạn.",
        },
        {
            "question": "Tôi có thể đặt lịch thử mùi riêng?",
            "answer": "Bạn có thể đặt lịch private appointment trong khung giờ 10:00–20:00 hằng ngày.",
        },
        {
            "question": "Ami hỗ trợ giao hàng toàn quốc?",
            "answer": "Có. Đơn hàng được đóng gói chống sốc, hỗ trợ COD và đổi trả theo chính sách.",
        },
    ]
    reviews = [
        {"name": "Minh Khang", "comment": "Tư vấn cực kỳ có tâm, chọn đúng mùi cho môi trường văn phòng."},
        {"name": "Ngọc Ánh", "comment": "Không gian boutique sang và dịch vụ hậu mãi rất tốt."},
        {"name": "Quốc Đạt", "comment": "Đặt lịch nhanh, được hướng dẫn layering rất chuyên nghiệp."},
    ]
    return render(request, 'app/contact.html', {'faq_items': faq_items, 'reviews': reviews})


def cart_page(request):
    cart_items = [
        {
            "name": "Dior Sauvage Elixir",
            "price": 4200000,
            "quantity": 1,
            "image": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=600&q=80",
        },
        {
            "name": "Bleu de Chanel EDP",
            "price": 3800000,
            "quantity": 2,
            "image": "https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=600&q=80",
        },
    ]
    suggestions = [
        {
            "name": "Y Eau de Parfum",
            "price": "3.400.000₫",
            "image": "https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=700&q=80",
        },
        {
            "name": "Gucci Guilty EDT",
            "price": "3.200.000₫",
            "image": "https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=700&q=80",
        },
        {
            "name": "Dior Homme Parfum",
            "price": "4.700.000₫",
            "image": "https://images.unsplash.com/photo-1563170351-be82bc888aa4?auto=format&fit=crop&w=700&q=80",
        },
        {
            "name": "Oud Wood Parfum",
            "price": "6.900.000₫",
            "image": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=700&q=80",
        },
    ]
    return render(request, 'app/cart.html', {'cart_items': cart_items, 'suggestions': suggestions})

def auth_page(request):
    return render(request, 'app/auth.html')

def profile_page(request):
    return render(request, 'app/profile.html')


def checkout_page(request):
    return render(request, 'app/checkout.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# ADMIN
def admin_dashboard(request):
    context = {
        "total_orders": 120,
        "total_users": 45,
        "revenue": 25000000,
    }
    return render(request, "admin/dashboard.html", context)

# def admin_redirect(request):
#     return redirect('admin-dashboard')
