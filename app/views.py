from django.contrib.auth import logout
from django.db import DatabaseError
from django.db import models
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.text import slugify
from .models import LoaiSanPham, NhomHuong
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.html import escape

from .models import (
    BaiViet,
    BienThe,
    BienTheThuocTinh,
    SanPhamNhomHuong,
    DanhGia,
    DonHang,
    ChiTietDonHang,
    GiaoHang,
    HinhAnh,
    HoiDap,
    KhachHang,
    SanPham,
    TaiKhoan,
    ThuongHieu,
    YeuThich,
)
from collections import defaultdict




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
        return "0đ"
    return f"{int(value):,}".replace(",", ".") + "đ"


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
    

def _account_display_name(account):
    return (account.TenDangNhap or account.Username or "Khách hàng").strip()


def _rating_label(star):
    return {5: "Tuyệt vời · Highly Recommended", 4: "Rất tốt", 3: "Tốt", 2: "Chưa phù hợp", 1: "Không hài lòng"}.get(star, "")


# def _normalize_vietnamese_text(value):
#     if not isinstance(value, str):
#         return value
#     if not value:
#         return value

#     # Fix common mojibake when UTF-8 bytes were interpreted as latin-1/cp1252.
#     for source_enc in ("latin-1", "cp1252"):
#         try:
#             repaired = value.encode(source_enc).decode("utf-8")
#         except (UnicodeEncodeError, UnicodeDecodeError):
#             continue
#         if repaired != value:
#             return repaired
#     return value



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

def _variant_value_map(product_ids):
    rows = _safe_list(
        BienTheThuocTinh.objects.select_related(
            "id_BienThe",
            "id_GiaTriThuocTinh",
            "id_GiaTriThuocTinh__id_ThuocTinh",
        ).filter(id_BienThe__id_SanPham_id__in=product_ids)
    )
    mapping = {}
    for row in rows:
        product_id = row.id_BienThe.id_SanPham_id
        value = row.id_GiaTriThuocTinh.GiaTri
        if not value:
            continue
        mapping.setdefault(product_id, set()).add(value)
    return {pid: sorted(values) for pid, values in mapping.items()}

def _build_product_cards(products):
    product_ids = [item.id_SanPham for item in products]
    image_map = _product_image_map(product_ids)

    first_variant_map = _first_variant_map(product_ids)
    variant_value_map = _variant_value_map(product_ids)
    variant_count_map = {
        row["id_SanPham_id"]: row["count"]
        for row in BienThe.objects.filter(id_SanPham_id__in=product_ids)
        .values("id_SanPham_id")
        .annotate(count=models.Count("id_BienThe"))
    }

    cards = []
    for product in products:
        default_variant = first_variant_map.get(product.id_SanPham)
        product_images = image_map.get(product.id_SanPham, [])
        primary_image = product_images[0] if product_images else FALLBACK_IMAGES["default"]
        hover_image = product_images[1] if len(product_images) > 1 else primary_image
        stock = int(default_variant.SoLuong) if default_variant else 0
        status_value = (product.TrangThai_SanPham or "").strip().lower()
        is_new = status_value in {"new", "moi", "mới"}
        cards.append(
            {
                "id": product.id_SanPham,
                "name": product.TenSanPham,
                "brand": product.id_ThuongHieu.TenThuongHieu,
                "brand_slug": slugify(product.id_ThuongHieu.TenThuongHieu),
                "group_list": [h.TenNhomHuong for h in product.nhom_huongs.all()],
                "price": _format_currency(default_variant.GiaBan if default_variant else None),
                "price_raw": int(default_variant.GiaBan or 0) if default_variant else 0,
                "stock": stock,
                "is_new": is_new,
                "primary_image": primary_image,
                "hover_image": hover_image,
                "variant_values": variant_value_map.get(product.id_SanPham, []),
                "variant_count": variant_count_map.get(product.id_SanPham, 0),
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

def _category_article_queryset(category=None):
    articles = BaiViet.objects.order_by("-NgayTao")
    if category and category.TenLoaiSanPham:
        keyword = category.TenLoaiSanPham
        articles = articles.filter(Q(TieuDe__icontains=keyword) | Q(NoiDung__icontains=keyword))
    return articles

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

    related_articles_qs = _category_article_queryset(current_category)
    related_articles = _safe_list(related_articles_qs[:6])

    if not related_articles and current_category:
        related_articles = _safe_list(BaiViet.objects.order_by("-NgayTao")[:6])

    recent_reviews = _safe_list(
        DanhGia.objects.select_related("id_TaiKhoan")
        .filter(id_SanPham__id_LoaiSanPham=current_category)
        .order_by("-NgayDanhGia", "-id_DanhGia")[:8]
    ) if current_category else _safe_list(
        DanhGia.objects.select_related("id_TaiKhoan")
        .order_by("-NgayDanhGia", "-id_DanhGia")[:8]
    )


    # 👉 context động theo DB
    context = {
        "page_title": f"Ami – {current_category.TenLoaiSanPham}" if current_category else "Ami – Tất cả nước hoa",
        "title": current_category.TenLoaiSanPham if current_category else "Tất cả nước hoa",
        "subtitle": current_category.MoTa if current_category else "Khám phá toàn bộ bộ sưu tập nước hoa.",
        "breadcrumb": current_category.TenLoaiSanPham if current_category else "Tất cả",
        "brands": _safe_list(ThuongHieu.objects.order_by("TenThuongHieu")),
        "segment": segment,
        "products": _build_product_cards(products),
        "related_articles": related_articles,
        "recent_reviews": recent_reviews,
    }

    context["product_count"] = len(context["products"])

    return render(request, "app/category.html", context)

def get_sillage_label(value):
    if value >= 8:
        return "Tỏa xa"
    elif value >= 5:
        return "Vừa phải"
    return "Nhẹ"

def get_longevity_label(value):
    if value >= 9:
        return "Trên 10 giờ"
    elif value >= 7:
        return "8-10 giờ"
    elif value >= 5:
        return "5-7 giờ"
    return "Dưới 5 giờ"

def product_detail(request, product_id=None):
    product_queryset = SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")\
                                        .prefetch_related("nhom_huongs")

    if product_id:
        product_obj = _safe_first(product_queryset.filter(id_SanPham=product_id))
    else:
        product_obj = _safe_first(product_queryset.order_by("id_SanPham"))
    if not product_obj:
        return render(request, "app/product.html", {"product_data": {}, "product_images": []})

    nhom_huongs = SanPhamNhomHuong.objects.select_related("id_NhomHuong").filter(
        id_SanPham=product_obj
    )
    nhom_huong_list = [
        {
            "name": item.id_NhomHuong.TenNhomHuong,
            "icon": item.id_NhomHuong.IconUrl.url if item.id_NhomHuong.IconUrl else "",
        }
        for item in nhom_huongs
    ]

    variants = _safe_list(BienThe.objects.filter(id_SanPham=product_obj).order_by("id_BienThe"))
    variant_attr_rows = _safe_list(
        BienTheThuocTinh.objects.select_related(
            "id_BienThe",
            "id_GiaTriThuocTinh",
            "id_GiaTriThuocTinh__id_ThuocTinh",
        ).filter(id_BienThe__id_SanPham=product_obj)
    )
    images = _safe_list(
        HinhAnh.objects.filter(
            Q(id_SanPham=product_obj) | Q(id_BienThe__id_SanPham=product_obj)
        ).order_by("id_HinhAnh")
    )
    root_reviews = _safe_list(
    DanhGia.objects.select_related("id_TaiKhoan")
    .filter(id_SanPham=product_obj, parent_id__isnull=True)
        .order_by("-NgayDanhGia", "-id_DanhGia")
    )
    # ═══════════════════════════════════════════════════════════════
# THAY TOÀN BỘ đoạn này trong hàm product_detail (views.py)
#
# Tìm dòng:    qa_items = []
# Đến hết:     qa_items.append({"question": q, "answer": answer})
# Thay bằng đoạn dưới đây:
# ═══════════════════════════════════════════════════════════════

    qa_items = []
 
    questions = HoiDap.objects.select_related(
        "id_TaiKhoan"
    ).filter(
        id_SanPham=product_obj,
        parent_id__isnull=True
    ).exclude(
        TrangThai='hidden'
    ).order_by('-NgayTao')
 
    # Thêm tạm vào cuối vòng for q in questions (trong views.py)
# để debug xem admin_answer có được tìm thấy không

    for q in questions:

        admin_answer = HoiDap.objects.select_related("id_TaiKhoan") \
            .exclude(TrangThai='hidden') \
            .filter(
                parent_id=q.id_HoiDap,
                id_TaiKhoan__LoaiTaiKhoan__in=['admin', 'staff']
            ).order_by('NgayTao').first()

        follow_ups = list(
            HoiDap.objects.select_related("id_TaiKhoan")
            .exclude(TrangThai='hidden')
            .filter(parent_id=q.id_HoiDap)
            .exclude(id_TaiKhoan__LoaiTaiKhoan__in=['admin', 'staff'])
            .order_by('NgayTao')
        )

        # DEBUG — xóa sau khi xác nhận hoạt động
        print(f"[QA DEBUG] q.id={q.id_HoiDap} nội_dung='{q.NoiDung[:20]}' "
              f"admin_answer={admin_answer.id_HoiDap if admin_answer else None} "
              f"follow_ups={[f.id_HoiDap for f in follow_ups]}")

        qa_items.append({
            "question":   q,
            "answer":     admin_answer,
            "follow_ups": follow_ups,
        })

    top_variant = variants[0] if variants else None
    variant_attr_map = {}
    option_groups = {}
    for row in variant_attr_rows:
        variant_id = row.id_BienThe_id
        attr_name = row.id_GiaTriThuocTinh.id_ThuocTinh.TenThuocTinh
        attr_value = row.id_GiaTriThuocTinh.GiaTri
        variant_attr_map.setdefault(variant_id, {})[attr_name] = attr_value
        option_groups.setdefault(attr_name, set()).add(attr_value)

    variant_payload = []
    for variant in variants:
        variant_payload.append(
            {
                "id": variant.id_BienThe,
                "sku": variant.Sku,
                "price": _format_currency(variant.GiaBan),
                "price_raw": int(variant.GiaBan or 0),
                "stock": int(variant.SoLuong or 0),
                "attributes": variant_attr_map.get(variant.id_BienThe, {}),
            }
        )
    rating_values = [item.SoSao for item in root_reviews if item.SoSao]
    rating_avg = round(sum(rating_values) / len(rating_values), 1) if rating_values else 0
    rating_count = len(rating_values)
    rating_breakdown = {star: len([v for v in rating_values if v == star]) for star in range(1, 6)}

    expert_replies = defaultdict(list)
    for reply in DanhGia.objects.select_related("id_TaiKhoan").filter(id_SanPham=product_obj, parent_id__isnull=False).order_by("NgayDanhGia", "id_DanhGia"):
        expert_replies[reply.parent_id].append(reply)

    review_cards = []
    for rv in root_reviews:
        name = _account_display_name(rv.id_TaiKhoan) if rv.id_TaiKhoan else "Khách hàng"
        review_cards.append({
            "id": rv.id_DanhGia,
            "name": name,
            "avatar": name[:1].upper(),
            "rating": int(rv.SoSao or 0),
            "label": _rating_label(int(rv.SoSao or 0)),
            "content": rv.NoiDung or "",
            "created_at": rv.NgayDanhGia.strftime("%d/%m/%Y %H:%M") if rv.NgayDanhGia else "",
            "replies": expert_replies.get(rv.id_DanhGia, []),
        })
    # print("ID:", product_obj.id_SanPham)
    # print("NongDo:", product_obj.NongDo)
    # print("XuatXu:", product_obj.XuatXu)
    # print("PhongCach:", product_obj.PhongCach)
    product_data = {
        
        "id": product_obj.id_SanPham,
        "name": product_obj.TenSanPham,
        "brand": product_obj.id_ThuongHieu.TenThuongHieu,
        "description": product_obj.MoTa_SanPham,
        "category": product_obj.id_LoaiSanPham.TenLoaiSanPham,
        "concentration": product_obj.NongDo,
        "longevity": product_obj.DoLuuHuong,
        "sillage": product_obj.DoToaHuong,

        "longevity_percent": min((product_obj.DoLuuHuong or 0) * 10, 100),
        "sillage_percent": min((product_obj.DoToaHuong or 0) * 10, 100),

        "longevity_text": get_longevity_label(product_obj.DoLuuHuong),
        "sillage_text": get_sillage_label(product_obj.DoToaHuong),

        "season": product_obj.MuaPhuHop,
        "time_use": product_obj.ThoiDiemSuDung,
        "style": product_obj.PhongCach,
        "age_group": product_obj.DoTuoiPhuHop,
        "release_year": product_obj.NamPhatHanh,
        "origin": product_obj.XuatXu,
        "scent_group": ", ".join([
                h.TenNhomHuong for h in product_obj.nhom_huongs.all()
            ]),
        "price": _format_currency(top_variant.GiaBan if top_variant else None),
        "stock": top_variant.SoLuong if top_variant else 0,
        "status": product_obj.TrangThai_SanPham,
        "rating_avg": rating_avg,
        "rating_count": rating_count,
        "rating_breakdown": {k: v for k, v in sorted(rating_breakdown.items(), reverse=True)},
        "reviews": review_cards,
        "questions": questions,
        # "reviews": root_reviews,
        "variants": json.dumps(variant_payload, ensure_ascii=False),
        "variant_count": len(variant_payload),
        "option_groups": {k: sorted(list(v)) for k, v in option_groups.items()},
        "qa_items": qa_items,
    }

    
    product_images = [img.url.url if hasattr(img.url, "url") else str(img.url) for img in images]

    related_products = _build_product_cards(
        _safe_list(
            SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")
            .prefetch_related("nhom_huongs")
            .filter(id_ThuongHieu=product_obj.id_ThuongHieu)
            .exclude(id_SanPham=product_obj.id_SanPham)
            .order_by("-id_SanPham")[:10]
        )
    )

    scent_group_ids = [item.id_NhomHuong_id for item in nhom_huongs]
    similar_scent_products = _build_product_cards(
        _safe_list(
            SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")
            .prefetch_related("nhom_huongs")
            .filter(nhom_huongs__id_NhomHuong__in=scent_group_ids)
            .exclude(id_SanPham=product_obj.id_SanPham)
            .distinct()
            .order_by("-id_SanPham")[:4]
        )
    ) if scent_group_ids else []

    return render(request, "app/product.html", {
        "product_data": product_data,
        "product_images": product_images,
        "nhom_huong_list": nhom_huong_list,
        "related_products": related_products,
        "brand_slug": slugify(product_obj.id_ThuongHieu.TenThuongHieu),
        "similar_scent_products": similar_scent_products,
    })


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
                "category": "Designer" if len(name) % 2 == 0 else "Niche",
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

    featured_articles = BaiViet.objects.order_by("-NgayTao")[:3]

    bento_articles = BaiViet.objects.order_by("-NgayTao")[3:]

    popular_articles = BaiViet.objects.order_by("-NgayTao")[:5]

    context = {
        "featured_articles": featured_articles,
        "bento_articles": bento_articles,
        "popular_articles": popular_articles,
    }

    return render(request, "app/blog.html", context)

def article_detail(request, id):
    article_obj = BaiViet.objects.get(id_BaiViet=id)

    articles_qs = BaiViet.objects.order_by("-NgayTao")

    article = {
        "id": article_obj.id_BaiViet,
        "title": article_obj.TieuDe,
        "author": article_obj.TacGia,
        "published_at": article_obj.NgayTao.strftime("%d/%m/%Y") if article_obj.NgayTao else "",
        "cover": getattr(article_obj, "AnhDaiDien", ""),
        "body": [{"type": "p", "text": article_obj.NoiDung or ""}],
    }

    related_articles = [
        {
            "id": item.id_BaiViet,
            "title": item.TieuDe,
            "cover": getattr(item, "AnhDaiDien", ""),
        }
        for item in articles_qs
        if item.id_BaiViet != article_obj.id_BaiViet
    ][:5]

    return render(request, "app/article_detail.html", {
        "article": article,
        "related_articles": related_articles,
    })


def contact_page(request):
    return render(request, 'app/contact.html')


def cart_page(request):
    cart_items = []
    order = _safe_first(
    DonHang.objects
    .select_related("id_KhachHang", "id_GiaoHang")
    .order_by("-ThoiGian")
)
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
    if request.session.get("account_id"):
        return redirect('profile-page')
    return render(request, 'app/auth.html')
# @csrf_exempt
# @require_POST
# def login_api(request):
#     email = (request.POST.get("email") or "").strip()
#     password = request.POST.get("password") or ""
#     if not email or not password:
#         return JsonResponse({"ok": False, "message": "Vui lòng nhập email và mật khẩu."}, status=400)

#     account = TaiKhoan.objects.filter(Email__iexact=email, MatKhau=password, TrangThai_TaiKhoan__iexact='active').first()
#     if not account:
#         return JsonResponse({"ok": False, "message": "Email hoặc mật khẩu không đúng."}, status=401)

#     request.session["account_id"] = account.id_TaiKhoan
#     request.session["account_name"] = account.TenDangNhap or account.Username
#     return JsonResponse({"ok": True, "message": "Đăng nhập thành công."})


# ═══════════════════════════════════════════════════════
# views.py — Thay thế hàm submit_question hiện tại
# Thêm xử lý parent_id để khách phản hồi sau câu trả lời admin
# ═══════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def submit_question(request):
    print("=== SUBMIT QUESTION CALLED ===")
    print("POST:", request.POST)

    account_id = request.session.get("account_id")

    if not account_id:
        return JsonResponse({
            "ok": False,
            "need_login": True
        })

    product_id = request.POST.get("product_id")
    content = (request.POST.get("content") or "").strip()
    parent_id = request.POST.get("parent_id")  # <-- nhận parent_id từ form phản hồi

    if not content:
        return JsonResponse({
            "ok": False,
            "message": "Vui lòng nhập câu hỏi."
        })

    try:
        account = TaiKhoan.objects.get(id_TaiKhoan=account_id)
        product = SanPham.objects.get(id_SanPham=product_id)
    except (TaiKhoan.DoesNotExist, SanPham.DoesNotExist):
        return JsonResponse({
            "ok": False,
            "message": "Không tìm thấy dữ liệu."
        })

    # Nếu có parent_id → đây là câu hỏi tiếp theo sau khi admin trả lời
    # Nếu không có → đây là câu hỏi mới hoàn toàn
    resolved_parent_id = int(parent_id) if parent_id else None

    question = HoiDap.objects.create(
        id_SanPham=product,
        id_TaiKhoan=account,
        NoiDung=content,
        TrangThai='pending',
        parent_id=resolved_parent_id,
        NgayTao=timezone.now()
    )

    return JsonResponse({
        "ok": True,
        "question": {
            "id": question.id_HoiDap,
            "name": account.TenDangNhap,
            "content": question.NoiDung,
            "created_at": question.NgayTao.strftime("%d/%m/%Y %H:%M"),
            "is_reply": resolved_parent_id is not None,  # để JS biết đây là reply hay câu hỏi mới
        }
    })

@csrf_exempt
@require_POST
def submit_review(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True, "message": "Vui lòng đăng nhập để chia sẻ trải nghiệm của bạn."})

    last_submit = request.session.get("review_last_submit")
    now_ts = timezone.now().timestamp()
    if last_submit and now_ts - float(last_submit) < 8:
        return JsonResponse({"ok": False, "message": "Bạn đang thao tác quá nhanh, vui lòng thử lại sau vài giây."}, status=429)

    product_id = request.POST.get("product_id")
    try:
        rating = int(request.POST.get("rating") or 0)
    except ValueError:
        rating = 0
    content = escape((request.POST.get("content") or "").strip())

    if rating < 1 or rating > 5:
        return JsonResponse({"ok": False, "message": "Số sao phải từ 1 đến 5."}, status=400)
    if not content:
        return JsonResponse({"ok": False, "message": "Vui lòng nhập nội dung đánh giá."}, status=400)
    if len(content) > 800:
        return JsonResponse({"ok": False, "message": "Đánh giá tối đa 800 ký tự."}, status=400)

    account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
    product = SanPham.objects.filter(id_SanPham=product_id).first()
    if not account or not product:
        return JsonResponse({"ok": False, "message": "Không tìm thấy dữ liệu."}, status=404)

    review = DanhGia.objects.create(
        id_SanPham=product,
        id_TaiKhoan=account,
        SoSao=rating,
        NoiDung=content,
        parent_id=None,
        NgayDanhGia=timezone.now(),
    )
    request.session["review_last_submit"] = now_ts

    return JsonResponse({
        "ok": True,
        "message": "Cảm ơn bạn đã chia sẻ trải nghiệm cùng Ami Perfume.",
        "review": {
            "id": review.id_DanhGia,
            "name": _account_display_name(account),
            "rating": rating,
            "label": _rating_label(rating),
            "content": content,
            "created_at": review.NgayDanhGia.strftime("%d/%m/%Y %H:%M"),
        }
    })

# ═══════════════════════════════════════════════════════
# Thêm 2 hàm này vào views.py (sau hàm submit_review)
# Và thêm 2 URL vào urls.py
# ═══════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def delete_review(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})

    review_id = request.POST.get("review_id")
    try:
        review = DanhGia.objects.get(
            id_DanhGia=review_id,
            id_TaiKhoan_id=account_id  # chỉ cho xóa review của chính mình
        )
        review.delete()
        return JsonResponse({"ok": True})
    except DanhGia.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Không tìm thấy đánh giá."}, status=404)


@csrf_exempt
@require_POST
def edit_review(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})

    review_id = request.POST.get("review_id")
    content   = escape((request.POST.get("content") or "").strip())
    try:
        rating = int(request.POST.get("rating") or 0)
    except ValueError:
        rating = 0

    if rating < 1 or rating > 5:
        return JsonResponse({"ok": False, "message": "Số sao phải từ 1 đến 5."})
    if not content:
        return JsonResponse({"ok": False, "message": "Vui lòng nhập nội dung."})
    if len(content) > 800:
        return JsonResponse({"ok": False, "message": "Tối đa 800 ký tự."})

    try:
        review = DanhGia.objects.get(
            id_DanhGia=review_id,
            id_TaiKhoan_id=account_id
        )
        review.SoSao   = rating
        review.NoiDung = content
        review.save(update_fields=["SoSao", "NoiDung"])
        return JsonResponse({"ok": True})
    except DanhGia.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Không tìm thấy đánh giá."}, status=404)
    

# ═══════════════════════════════════════════════════════
# Thêm vào views.py sau hàm edit_review
# ═══════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def toggle_wishlist(request):
    """Toggle thêm/xóa sản phẩm khỏi danh sách yêu thích."""
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})

    product_id = request.POST.get("product_id")
    if not product_id:
        return JsonResponse({"ok": False, "message": "Thiếu product_id."})

    try:
        account  = TaiKhoan.objects.get(id_TaiKhoan=account_id)
        product  = SanPham.objects.get(id_SanPham=product_id)
        customer = KhachHang.objects.filter(id_TaiKhoan=account).first()
    except (TaiKhoan.DoesNotExist, SanPham.DoesNotExist):
        return JsonResponse({"ok": False, "message": "Không tìm thấy dữ liệu."})

    if not customer:
        return JsonResponse({"ok": False, "message": "Không tìm thấy thông tin khách hàng."})

    # Kiểm tra đã yêu thích chưa
    existing = YeuThich.objects.filter(
        id_KhachHang=customer,
        id_SanPham=product
    ).first()

    if existing:
        # Đã yêu thích → xóa
        existing.delete()
        return JsonResponse({"ok": True, "action": "removed", "message": "Đã xóa khỏi danh sách yêu thích."})
    else:
        # Chưa yêu thích → thêm
        YeuThich.objects.create(
            id_KhachHang=customer,
            id_SanPham=product,
            NgayTao=timezone.now(),
        )
        return JsonResponse({"ok": True, "action": "added", "message": "Đã thêm vào danh sách yêu thích."})


def get_wishlist_status(request, product_id):
    """Kiểm tra sản phẩm có trong wishlist không — dùng khi load trang."""
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"liked": False})

    try:
        account  = TaiKhoan.objects.get(id_TaiKhoan=account_id)
        customer = KhachHang.objects.filter(id_TaiKhoan=account).first()
        if not customer:
            return JsonResponse({"liked": False})
        liked = YeuThich.objects.filter(
            id_KhachHang=customer,
            id_SanPham_id=product_id
        ).exists()
        return JsonResponse({"liked": liked})
    except TaiKhoan.DoesNotExist:
        return JsonResponse({"liked": False})


@csrf_exempt
@require_POST
def login_api(request):
    email = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""
    if not email or not password:
        return JsonResponse({"ok": False, "message": "Vui lòng nhập email và mật khẩu."}, status=400)

    account = TaiKhoan.objects.filter(Email__iexact=email, MatKhau=password, TrangThai_TaiKhoan__iexact='active').first()
    if not account:
        return JsonResponse({"ok": False, "message": "Email hoặc mật khẩu không đúng."}, status=401)

    request.session["account_id"] = account.id_TaiKhoan
    request.session["account_name"] = account.TenDangNhap
    return JsonResponse({"ok": True, "message": "Đăng nhập thành công."})


@csrf_exempt
@require_POST
def register_api(request):
    full_name = (request.POST.get("fullname") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    if not all([full_name, email, phone, username, password]):
        return JsonResponse({"ok": False, "message": "Vui lòng điền đầy đủ thông tin."}, status=400)

    if TaiKhoan.objects.filter(Username__iexact=username).exists():
        return JsonResponse({"ok": False, "message": "Tên đăng nhập đã tồn tại."}, status=409)
    if TaiKhoan.objects.filter(Email__iexact=email).exists():
        return JsonResponse({"ok": False, "message": "Email đã được sử dụng."}, status=409)

    account = TaiKhoan.objects.create(
        Username=username,
        MatKhau=password,
        TenDangNhap=full_name,
        Email=email,
        SDT=phone,
        LoaiTaiKhoan='customer',
        TrangThai_TaiKhoan='active',
        NgayTao=timezone.now(),
    )
    KhachHang.objects.create(
        id_TaiKhoan=account,
        TenKhachHang=full_name,
        DiaChi='',
        GioiTinh='',
    )
    return JsonResponse({"ok": True, "message": "Đăng ký thành công."})


@csrf_exempt
@require_POST
def forgot_password_api(request):
    email = (request.POST.get("email") or "").strip()
    username = (request.POST.get("username") or "").strip()
    new_password = request.POST.get("new_password") or ""

    if not all([email, username, new_password]):
        return JsonResponse({"ok": False, "message": "Vui lòng nhập email, tên đăng nhập và mật khẩu mới."}, status=400)

    account = TaiKhoan.objects.filter(Email__iexact=email, Username__iexact=username).first()
    if not account:
        return JsonResponse({"ok": False, "message": "Không tìm thấy tài khoản phù hợp."}, status=404)

    account.MatKhau = new_password
    account.save(update_fields=["MatKhau"])
    return JsonResponse({"ok": True, "message": "Đổi mật khẩu thành công."})

# ═══════════════════════════════════════════════════════════════
# Trong views.py — thay hàm profile_page
# FIX: query DanhGia dùng đúng field NgayDanhGia (không có NgayTao)
#       filter chỉ parent_id__isnull=True (bỏ Q(parent_id=0))
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
# Thay hàm profile_page trong views.py
# Thêm phần lấy wishlist_data từ DB
# ═══════════════════════════════════════════════════════

def profile_page(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return redirect('auth-page')

    account = _safe_first(TaiKhoan.objects.filter(id_TaiKhoan=account_id))
    customer = _safe_first(
        KhachHang.objects.select_related("id_TaiKhoan").filter(id_TaiKhoan=account)
        if account else KhachHang.objects.none()
    )

    # ── Đánh giá ──────────────────────────────────────────────
    review_data = []
    try:
        user_reviews = list(
            DanhGia.objects
            .select_related("id_SanPham", "id_SanPham__id_ThuongHieu")
            .filter(id_TaiKhoan_id=account_id, parent_id__isnull=True)
            .order_by("-NgayDanhGia")
        )
        review_product_ids = [rv.id_SanPham_id for rv in user_reviews if rv.id_SanPham_id]
        review_image_map = _product_image_map(review_product_ids) if review_product_ids else {}

        for rv in user_reviews:
            product = rv.id_SanPham
            if not product:
                continue
            images = review_image_map.get(product.id_SanPham, [])
            review_data.append({
                "id":           rv.id_DanhGia,
                "product_id":   product.id_SanPham,
                "product_name": product.TenSanPham,
                "brand":        product.id_ThuongHieu.TenThuongHieu if product.id_ThuongHieu else "",
                "image":        images[0] if images else FALLBACK_IMAGES["default"],
                "rating":       int(rv.SoSao or 0),
                "label":        _rating_label(int(rv.SoSao or 0)),
                "content":      rv.NoiDung or "",
                "created_at":   rv.NgayDanhGia.strftime("%d/%m/%Y") if rv.NgayDanhGia else "",
            })
    except Exception as e:
        import traceback; traceback.print_exc()

    # ── Yêu thích ─────────────────────────────────────────────
    wishlist_data = []
    if customer:
        try:
            wish_rows = list(
                YeuThich.objects
                .select_related("id_SanPham", "id_SanPham__id_ThuongHieu")
                .filter(id_KhachHang=customer)
                .order_by("-NgayTao")
            )
            wish_product_ids = [w.id_SanPham_id for w in wish_rows if w.id_SanPham_id]
            wish_image_map = _product_image_map(wish_product_ids) if wish_product_ids else {}

            for w in wish_rows:
                product = w.id_SanPham
                if not product:
                    continue
                images = wish_image_map.get(product.id_SanPham, [])
                # Lấy giá từ biến thể đầu tiên
                first_variant = BienThe.objects.filter(id_SanPham=product).order_by("id_BienThe").first()
                wishlist_data.append({
                    "id":           w.id_YeuThich,
                    "product_id":   product.id_SanPham,
                    "product_name": product.TenSanPham,
                    "brand":        product.id_ThuongHieu.TenThuongHieu if product.id_ThuongHieu else "",
                    "image":        images[0] if images else FALLBACK_IMAGES["default"],
                    "price":        _format_currency(first_variant.GiaBan if first_variant else None),
                    "added_at":     w.NgayTao.strftime("%d/%m/%Y") if w.NgayTao else "",
                })
        except Exception as e:
            import traceback; traceback.print_exc()

    profile = {
        "full_name": (customer.TenKhachHang if customer else None)
                     or (account.TenDangNhap if account else "") or "Khách hàng",
        "username":  (account.Username if account else "") or "guest",
        "email":     (account.Email if account else "") or "",
        "phone":     (account.SDT if account else "") or "",
        "address":   (customer.DiaChi if customer else "") or "",
        "gender":    (customer.GioiTinh if customer else "") or "",
    }

    return render(request, 'app/profile.html', {
        "profile":       profile,
        "review_data":   review_data,
        "wishlist_data": wishlist_data,
    })


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
    request.session.pop("account_id", None)
    request.session.pop("account_name", None)
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
