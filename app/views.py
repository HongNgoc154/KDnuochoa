from django.contrib.auth import logout
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.text import slugify
from .models import LoaiSanPham, NhomHuong

from .models import (
    BaiViet,
    BienThe,
    ChiTietDonHang,
    DanhGia,
    DonHang,
    GiaoHang,
    HinhAnh,
    HoiDap,
    KhachHang,
    SanPham,
    TaiKhoan,
    ThuongHieu,
    YeuThich,
)


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


def _safe_list(queryset):
    try:
        return list(queryset)
    except DatabaseError:
        return []


def _safe_first(queryset):
    try:
        return queryset.first()
    except DatabaseError:
        return None


from django.conf import settings

from django.conf import settings

def _product_image_map(product_ids):
    images = HinhAnh.objects.filter(id_SanPham_id__in=product_ids)

    mapping = {}

    for img in images:
        pid = img.id_SanPham_id

        if img.url:
            # 👉 luôn ép về URL đúng
            url = str(img.url)

            if not url.startswith("http"):
                url = settings.MEDIA_URL + url  # 👈 FIX QUAN TRỌNG

            if pid not in mapping:
                mapping[pid] = []

            mapping[pid].append(url)

    return mapping


def _first_variant_map(product_ids):
    first_variant_map = {}
    variant_rows = BienThe.objects.filter(id_SanPham_id__in=product_ids).order_by("id_SanPham_id", "id_BienThe")
    for variant in variant_rows:
        first_variant_map.setdefault(variant.id_SanPham_id, variant)
    return first_variant_map

def _build_product_cards(products):
    product_ids = [item.id_SanPham for item in products]
    image_map = _product_image_map(product_ids)

    first_variant_map = _first_variant_map(product_ids)

    cards = []
    for product in products:
        default_variant = first_variant_map.get(product.id_SanPham)
        product_images = image_map.get(product.id_SanPham, [])
        primary_image = product_images[0] if product_images else FALLBACK_IMAGES["default"]
        hover_image = product_images[1] if len(product_images) > 1 else primary_image
        stock = int(default_variant.SoLuong) if default_variant else 0
        is_active = (product.TrangThai_SanPham or "").lower() == "active"
        cards.append(
            {
                "id": product.id_SanPham,
                "name": product.TenSanPham,
                "brand": product.id_ThuongHieu.TenThuongHieu,
                "brand_slug": slugify(product.id_ThuongHieu.TenThuongHieu),
                "group_list": [h.TenNhomHuong for h in product.nhom_huongs.all()],
                "price": _format_currency(default_variant.GiaBan if default_variant else None),
                "price_raw": int(default_variant.GiaBan or 0) if default_variant else 0,
                "stock": stock if is_active else 0,
                "is_new": is_active,
                "primary_image": primary_image,
                "hover_image": hover_image,
            }
        )
    return cards




def home(request):
    brands = _safe_list(ThuongHieu.objects.order_by("TenThuongHieu"))
    categories = _safe_list(LoaiSanPham.objects.all())

    featured_products = _build_product_cards(
        _safe_list(
            SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")
                            .prefetch_related("nhom_huongs")
            .order_by("-id_SanPham")[:8]
        )
    )

    total_products = SanPham.objects.count()
    total_brands = ThuongHieu.objects.count()
    total_customers = KhachHang.objects.count()

    def format_k(num):
        if num >= 1000:
            return f"{num//1000}K"
        return str(num)

    total_customers = format_k(total_customers)

    latest_articles = _safe_list(BaiViet.objects.order_by("-NgayTao")[:4])

    return render(
        request,
        "app/home.html",
        {
            "brands_home": brands,
            "categories": categories,
            "featured_products": featured_products,
            "latest_articles_home": latest_articles,
            "total_products": total_products,
            "total_brands": total_brands,
            "total_customers": total_customers,
        },
    )

def category(request, segment='tat-ca'):

    # lấy tất cả danh mục
    categories = LoaiSanPham.objects.all()

    # tìm danh mục theo slug
    current_category = None
    for c in categories:
        if slugify(c.TenLoaiSanPham) == segment:
            current_category = c
            break

    # query sản phẩm
    products = SanPham.objects.select_related(
        "id_ThuongHieu",
        "id_LoaiSanPham"
    ).prefetch_related("nhom_huongs")

    # nếu không phải "tất cả" thì filter
    if segment != "tat-ca" and current_category:
        products = products.filter(id_LoaiSanPham=current_category)

    products = products.order_by("-id_SanPham")

    # 👉 context động theo DB
    context = {
        "page_title": f"Ami – {current_category.TenLoaiSanPham}" if current_category else "Ami – Tất cả nước hoa",
        "title": current_category.TenLoaiSanPham if current_category else "Tất cả nước hoa",
        "subtitle": current_category.MoTa if current_category else "Khám phá toàn bộ bộ sưu tập nước hoa.",
        "breadcrumb": current_category.TenLoaiSanPham if current_category else "Tất cả",
        "products": _build_product_cards(products),
    }

    context["product_count"] = len(context["products"])

    return render(request, "app/category.html", context)


def product_detail(request, product_id=None):
    product_queryset = SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")\
                                        .prefetch_related("nhom_huongs")
    if product_id:
        product_obj = _safe_first(product_queryset.filter(id_SanPham=product_id))
    else:
        product_obj = _safe_first(product_queryset.order_by("id_SanPham"))
    if not product_obj:
        return render(request, "app/product.html", {"product_data": {}, "product_images": []})

    variants = _safe_list(BienThe.objects.filter(id_SanPham=product_obj).order_by("id_BienThe"))
    images = _safe_list(
        HinhAnh.objects.filter(
            Q(id_SanPham=product_obj) | Q(id_BienThe__id_SanPham=product_obj)
        ).order_by("id_HinhAnh")
    )
    root_reviews = _safe_list(
        DanhGia.objects.select_related("id_TaiKhoan")
        .filter(id_SanPham=product_obj, parent_id__isnull=True)
        .order_by("-NgayDanhGia")[:5]
    )
    questions = _safe_list(
        HoiDap.objects.select_related("id_TaiKhoan")
        .filter(id_SanPham=product_obj, parent_id__isnull=True)
        .order_by("-NgayTao")[:5]
    )
    top_variant = variants[0] if variants else None
    rating_values = [item.SoSao for item in root_reviews if item.SoSao]
    rating_avg = round(sum(rating_values) / len(rating_values), 1) if rating_values else 0
    product_data = {
        "name": product_obj.TenSanPham,
        "brand": product_obj.id_ThuongHieu.TenThuongHieu,
        "description": product_obj.MoTa_SanPham,
        "category": product_obj.id_LoaiSanPham.TenLoaiSanPham,
        "scent_group": ", ".join([
                h.TenNhomHuong for h in product_obj.nhom_huongs.all()
            ]),
        "price": _format_currency(top_variant.GiaBan if top_variant else None),
        "stock": top_variant.SoLuong if top_variant else 0,
        "status": product_obj.TrangThai_SanPham,
        "rating_avg": rating_avg,
        "rating_count": len(root_reviews),
        "questions": questions,
        "reviews": root_reviews,
    }
    product_images = [img.url.url if hasattr(img.url, "url") else str(img.url) for img in images]

    return render(request, "app/product.html", {"product_data": product_data, "product_images": product_images})


def brand_list(request):
    brand_rows = list(ThuongHieu.objects.values("TenThuongHieu", "LogoUrl"))
    brands = []
    for row in brand_rows:
        name = row["TenThuongHieu"]
        slug = slugify(name)
        brands.append(
            {
                "slug": slug,
                "name": name,
                "tagline": "Tinh hoa mùi hương đẳng cấp",
                "palette": "#6f7d62",
                "poster_image": row["LogoUrl"] or FALLBACK_IMAGES["brand_poster"],
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

    brand_products = SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")\
                                    .prefetch_related("nhom_huongs").filter(
        id_ThuongHieu=brand_obj
    )
    products = _build_product_cards(brand_products)

    brand = {
        "slug": slugify(brand_obj.TenThuongHieu),
        "name": brand_obj.TenThuongHieu,
        "tagline": "Di sản mùi hương tinh tế",
        "palette": "#6f7d62",
        "hero_image": brand_obj.LogoUrl or FALLBACK_IMAGES["brand_hero"],
        "about_image": brand_obj.LogoUrl or FALLBACK_IMAGES["brand_about"],
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
        SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")\
                        .prefetch_related("nhom_huongs").all()[:5]
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
    reviews = []
    recent_reviews = _safe_list(
        DanhGia.objects.select_related("id_TaiKhoan").filter(parent_id__isnull=True).order_by("-NgayDanhGia")[:6]
    )
    for row in recent_reviews:
        reviews.append(
            {
                "name": row.id_TaiKhoan.TenDangNhap or row.id_TaiKhoan.Username or "Khách hàng",
                "comment": row.NoiDung or "Trải nghiệm tốt.",
            }
        )
    if not reviews:
        reviews = [{"name": "Ami", "comment": "Đội ngũ luôn sẵn sàng hỗ trợ bạn qua hotline và email."}]
    return render(request, 'app/contact.html', {'faq_items': faq_items, 'reviews': reviews})


def cart_page(request):
    cart_items = []
    order = _safe_first(DonHang.objects.select_related("id_KhachHang").order_by("-ThoiGian"))
    if order:
        details = _safe_list(
            ChiTietDonHang.objects.select_related("id_BienThe__id_SanPham").filter(id_DonHang=order)
        )
        product_ids = [row.id_BienThe.id_SanPham_id for row in details]
        image_map = _product_image_map(product_ids)
        for row in details:
            product = row.id_BienThe.id_SanPham
            cart_items.append(
                {
                    "name": product.TenSanPham,
                    "price": row.GiaBan or row.id_BienThe.GiaBan,
                    "quantity": row.SoLuong,
                    "image": image_map.get(product.id_SanPham, FALLBACK_IMAGES["default"]),
                }
            )

    suggestions = _build_product_cards(
        _safe_list(
            SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")
                            .prefetch_related("nhom_huongs")
            .order_by("-id_SanPham")[:8]
        )
    )[:4]
    return render(request, 'app/cart.html', {'cart_items': cart_items, 'suggestions': suggestions})

def auth_page(request):
    return render(request, 'app/auth.html')

def profile_page(request):
    account = _safe_first(TaiKhoan.objects.order_by("id_TaiKhoan"))
    customer = _safe_first(
        KhachHang.objects.select_related("id_TaiKhoan").filter(id_TaiKhoan=account) if account else KhachHang.objects.none()
    )
    profile = {
        "full_name": (customer.TenKhachHang if customer else None) or (account.TenDangNhap if account else "") or "Khách hàng",
        "username": (account.Username if account else "") or "guest",
        "email": (account.Email if account else "") or "",
        "phone": (account.SDT if account else "") or "",
        "address": (customer.DiaChi if customer else "") or "",
        "gender": (customer.GioiTinh if customer else "") or "",
    }
    return render(request, 'app/profile.html', {"profile": profile})


def checkout_page(request):
    delivery = _safe_first(GiaoHang.objects.select_related("id_TaiKhoan").order_by("-id_GiaoHang"))
    form_data = {
        "name": delivery.TenNguoiNhan if delivery else "",
        "phone": delivery.SDT if delivery else "",
        "email": delivery.id_TaiKhoan.Email if delivery and delivery.id_TaiKhoan else "",
        "address": delivery.DiaChi if delivery else "",
        "note": delivery.GhiChu if delivery else "",
    }
    return render(request, 'app/checkout.html', {"checkout": form_data})

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
