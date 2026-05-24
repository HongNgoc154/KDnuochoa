from django.contrib.auth import logout
from django.db import DatabaseError
from django.db import models
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.text import slugify
from .models import LoaiSanPham, NhomHuong
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.html import escape
import random, string
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
import requests as http_requests
import uuid
from django.http import JsonResponse
from .models import ThuocTinh, GiaTriThuocTinh
import json as _json
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone as tz
from django.db import models


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
    KhuyenMai,
    KhuyenMaiTaiKhoan,
    ThuongHieu,
    YeuThich,
    LichSuDiem,
    CauHinhThanhVien,NhaCungCap, PhieuNhap, ChiTietNhap,
    AIRecommendClick,
    ChatbotFeedback, 
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

def _payment_status_label(order):
    payment = ((order.HinhThucThanhToan or "COD").strip() or "COD").lower()
    status = (order.TrangThai or "").strip()
    if status == "Thanh toán thất bại":
        return "Thanh toán thất bại"
    if payment in ("vnpay", "momo", "paypal"):
        return "Đã thanh toán"
    if status == "Hoàn tất":
        return "Đã thanh toán"
    return "Chưa thanh toán"


def _delivery_status_label(order):
    status = (order.TrangThai or "Chờ xác nhận").strip()
    if status == "Đã thanh toán":
        return "Chờ xác nhận"
    if status == "Thanh toán thất bại":
        return "Đã hủy"
    return status or "Chờ xác nhận"


def _order_account(order):
    customer = getattr(order, "id_KhachHang", None)
    if customer and getattr(customer, "id_TaiKhoan", None):
        return customer.id_TaiKhoan
    delivery = getattr(order, "id_GiaoHang", None)
    if delivery and getattr(delivery, "id_TaiKhoan", None):
        return delivery.id_TaiKhoan
    return None


def _send_order_status_email(order, status):
    account = _order_account(order)
    email = (getattr(account, "Email", "") or "").strip() if account else ""
    if not email:
        return False

    customer_name = _account_display_name(account)
    order_code = order.MaDonHang or f"#{order.id_DonHang}"
    subject_map = {
        "Đã xác nhận": f"Ami Perfumery — Đơn hàng {order_code} đã được xác nhận",
        "Hoàn tất": f"Ami Perfumery — Đơn hàng {order_code} đã hoàn tất",
    }
    body_map = {
        "Đã xác nhận": (
            f"Xin chào {customer_name},\n\n"
            f"Đơn hàng {order_code} của bạn đã được Ami Perfumery xác nhận. "
            "Bạn có thể theo dõi trạng thái đơn trong trang tài khoản và xác nhận đã nhận hàng khi đơn được giao thành công.\n\n"
            "Cảm ơn bạn đã mua sắm tại Ami Perfumery."
        ),
        "Hoàn tất": (
            f"Xin chào {customer_name},\n\n"
            f"Đơn hàng {order_code} của bạn đã được hoàn tất. "
            "Ami Perfumery rất vui khi được phục vụ bạn.\n\n"
            "Đừng quên đánh giá sản phẩm để nhận thêm nhiều ưu đãi hấp dẫn từ cửa hàng. "
            "Bạn có thể vào trang Tài khoản > Đơn hàng và nhấn nút Đánh giá ngay trên đơn đã hoàn tất.\n\n"
            "👉 Mở nhanh trang đơn hàng: https://amiperfumery.vn/profile/?tab=orders\n\n"
            "Trân trọng,\nAmi Perfumery"
        ),
    }
    try:
        send_mail(
            subject_map.get(status, f"Ami Perfumery — Cập nhật đơn hàng {order_code}"),
            body_map.get(status, f"Đơn hàng {order_code} đã được cập nhật sang trạng thái {status}."),
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ami.com"),
            [email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        print(f"[order_email] Không gửi được email đơn {order_code} tới {email}: {exc}")
        return False


def _extract_voucher_code(order):
    note = ""
    delivery = getattr(order, "id_GiaoHang", None)
    if delivery:
        note = delivery.GhiChu or ""
    marker = "[AMI_VOUCHER:"
    if marker in note:
        return note.split(marker, 1)[1].split("]", 1)[0].strip() or "—"
    return "—"


def _clean_delivery_note(note):
    if not note:
        return ""
    marker = "[AMI_VOUCHER:"
    if marker in note:
        before, after = note.split(marker, 1)
        tail = after.split("]", 1)[1] if "]" in after else ""
        return (before + tail).strip()
    return note


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


def _voucher_type_label(voucher):
    loai = (voucher.LoaiKhuyenMai or "").lower()
    mapping = {
        "vip": "Exclusive",
        "thanh vien moi": "New Member",
        "freeship": "Freeship",
    }
    for key, label in mapping.items():
        if key in loai:
            return label
    return "Member"

# ═══════════════════════════════════════════════════════════════
# views.py — Thay các hàm helper điểm + thêm apply_points_api
# ═══════════════════════════════════════════════════════════════

# ── Helper: cộng điểm ──────────────────────────────────────────
def add_points(account, points, loai, mo_ta="", order=None):
    """Cộng điểm và ghi lịch sử. Dùng schema DB thực tế."""
    if not account or int(points) <= 0:
        return
    account.DiemTichLuy = int(account.DiemTichLuy or 0) + int(points)
    account.save(update_fields=["DiemTichLuy"])

    LichSuDiem.objects.create(
        id_TaiKhoan=account,
        id_DonHang=order,
        SoDiem=int(points),           # cột SoDiem (dương = cộng)
        Loai=loai,
        MoTa=mo_ta or f"Cộng {points} điểm",
        NgayTao=timezone.now(),
    )


# ── Helper: trừ điểm ──────────────────────────────────────────
def redeem_points(account, points, order=None):
    """Trừ điểm khi thanh toán. Trả False nếu không đủ điểm."""
    if not account:
        return False
    points = int(points)
    current = int(account.DiemTichLuy or 0)
    if points > current:
        return False
    account.DiemTichLuy = current - points
    account.save(update_fields=["DiemTichLuy"])

    LichSuDiem.objects.create(
        id_TaiKhoan=account,
        id_DonHang=order,
        SoDiem=-points,               # âm = trừ điểm
        Loai="redeem_order",
        MoTa="Dùng điểm thanh toán",
        NgayTao=timezone.now(),
    )
    return True


# ── Helper: cập nhật hạng thành viên ──────────────────────────
def update_member_level(account):
    """Cập nhật HangThanhVien theo TongChiTieu."""
    total = float(account.TongChiTieu or 0)
    if total >= 10_000_000:
        level = "Platinum"
    elif total >= 5_000_000:
        level = "Gold"
    elif total >= 2_000_000:
        level = "Silver"
    else:
        level = "Member"
    if account.HangThanhVien != level:
        account.HangThanhVien = level
        account.save(update_fields=["HangThanhVien"])


# ══════════════════════════════════════════════════════════════
# API: GET điểm hiện tại của user (dùng khi trang checkout load)
# URL: GET /api/points/
# ══════════════════════════════════════════════════════════════
def get_points_api(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "points": 0, "discount": 0})
 
    account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
    if not account:
        return JsonResponse({"ok": False, "points": 0, "discount": 0})
 
    points  = int(account.DiemTichLuy or 0)
    # 100 điểm = 10.000₫ → 1 điểm = 100₫
    discount = points * 100
    return JsonResponse({
        "ok": True,
        "points":   points,
        "discount": discount,                    # số tiền quy đổi nếu dùng hết
        "rate":     100,                          # 1 điểm = 100 VNĐ
    })


# ══════════════════════════════════════════════════════════════
# API: Tính giảm giá từ điểm (KHÔNG trừ thật, chỉ tính preview)
# POST /api/apply-points/
# Body: subtotal (tạm tính đã trừ voucher)
# ══════════════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def apply_points_api(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True,
                             "message": "Vui lòng đăng nhập."})
 
    account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
    if not account:
        return JsonResponse({"ok": False, "message": "Không tìm thấy tài khoản."})
 
    points  = int(account.DiemTichLuy or 0)
    if points <= 0:
        return JsonResponse({"ok": False, "message": "Bạn chưa có điểm tích lũy."})
 
    subtotal = float(request.POST.get("subtotal") or 0)
 
    # Giới hạn: điểm chỉ được giảm tối đa 30% tổng đơn
    RATE        = 100           # 1 điểm = 100 VNĐ
    MAX_RATIO   = 0.30          # tối đa 30% đơn hàng
    max_by_pct  = subtotal * MAX_RATIO
    discount_all = points * RATE
 
    # Số tiền thực tế được giảm
    discount = min(discount_all, max_by_pct)
    # Số điểm tương ứng
    points_used = int(discount / RATE)
 
    if points_used <= 0:
        return JsonResponse({"ok": False,
                             "message": "Đơn hàng chưa đủ điều kiện sử dụng điểm."})
 
    return JsonResponse({
        "ok":           True,
        "message":      f"Áp dụng {points_used} điểm — giảm {int(discount):,}₫ ✨",
        "points":       points,
        "points_used":  points_used,
        "discount":     int(discount),
        "rate":         RATE,
    })


# ══════════════════════════════════════════════════════════════
# Thêm vào urls.py:
# path('api/points/',         views.get_points_api,   name='points-api'),
# path('api/apply-points/',   views.apply_points_api, name='apply-points-api'),
# ══════════════════════════════════════════════════════════════

# ── Helper: cộng điểm ──────────────────────────────────────────
def add_points(account, points, loai, mo_ta="", order=None):
    """Cộng điểm và ghi lịch sử. Dùng schema DB thực tế."""
    if not account or int(points) <= 0:
        return
    account.DiemTichLuy = int(account.DiemTichLuy or 0) + int(points)
    account.save(update_fields=["DiemTichLuy"])
 
    LichSuDiem.objects.create(
        id_TaiKhoan=account,
        id_DonHang=order,
        SoDiem=int(points),           # cột SoDiem (dương = cộng)
        Loai=loai,
        MoTa=mo_ta or f"Cộng {points} điểm",
        NgayTao=timezone.now(),
    )

# ── Helper: trừ điểm ──────────────────────────────────────────
def redeem_points(account, points, order=None):
    """Trừ điểm khi thanh toán. Trả False nếu không đủ điểm."""
    if not account:
        return False
    points = int(points)
    current = int(account.DiemTichLuy or 0)
    if points > current:
        return False
    account.DiemTichLuy = current - points
    account.save(update_fields=["DiemTichLuy"])
 
    LichSuDiem.objects.create(
        id_TaiKhoan=account,
        id_DonHang=order,
        SoDiem=-points,               # âm = trừ điểm
        Loai="redeem_order",
        MoTa="Dùng điểm thanh toán",
        NgayTao=timezone.now(),
    )
    return True

def _get_available_vouchers(account_id):
    now = timezone.now()
    rows = KhuyenMaiTaiKhoan.objects.select_related("id_KhuyenMai").filter(
        id_TaiKhoan_id=account_id,
    ).order_by("-id")
    vouchers = []
    for row in rows:
        v = row.id_KhuyenMai
        if not v:
            continue
        is_active = (v.TrangThai or "").lower() in {"active", "on", "1"}
        not_expired = (v.NgayKetThuc is None) or (v.NgayKetThuc >= now)
        started = (v.NgayBatDau is None) or (v.NgayBatDau <= now)
        has_quota = (v.SoLuong is None) or (int(v.DaSuDung or 0) < int(v.SoLuong or 0))
        status = "Còn hiệu lực"
        if row.DaSuDung:
            status = "Đã sử dụng"
        elif not not_expired:
            status = "Hết hạn"
        elif not (is_active and started and has_quota):
            status = "Không khả dụng"

        vouchers.append({
            "id": v.id_KhuyenMai,
            "code": (v.MaKhuyenMai or "").upper(),
            "name": v.TenKhuyenMai or "",
            "description": v.MoTa or "",
            "discount_type": (v.LoaiGiam or "").lower(),
            "discount_value": float(v.GiaTriGiam or 0),
            "minimum_order": float(v.DonHangToiThieu or 0),
            "max_discount": float(v.GiamToiDa or 0),
            "expiry": v.NgayKetThuc.strftime("%d/%m/%Y") if v.NgayKetThuc else "",
            "status": status,
            "exclusive_badge": _voucher_type_label(v),
            "used": bool(row.DaSuDung),
        })
    return vouchers

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

    search_q = (request.GET.get("q") or "").strip()

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

    if search_q:
        products = products.filter(
            Q(TenSanPham__icontains=search_q)
            | Q(id_ThuongHieu__TenThuongHieu__icontains=search_q)
            | Q(nhom_huongs__TenNhomHuong__icontains=search_q)
        ).distinct()

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
        "search_q": search_q,
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
    is_favorite = False

    account_id = request.session.get("account_id")

    if account_id:

        account = TaiKhoan.objects.filter(
            id_TaiKhoan=account_id
        ).first()

        if account:

            is_favorite = YeuThich.objects.filter(
                id_TaiKhoan=account,
                id_SanPham=product_obj
            ).exists()

    nhom_huongs = SanPhamNhomHuong.objects.select_related("id_NhomHuong").filter(
        id_SanPham=product_obj
    )
     # ── Flat list (hiện tại) ──
    nhom_huong_list = [
        {
            "name": item.id_NhomHuong.TenNhomHuong,
            "icon": item.id_NhomHuong.IconUrl.url if item.id_NhomHuong.IconUrl else "",
            "vai_tro": item.VaiTroHuong or "",
        }
        for item in nhom_huongs
    ]
 
    # ── Kim tự tháp phân tầng ──
    pyramid = {"top": [], "heart": [], "base": [], "other": []}
    for item in nhom_huongs:
        vai_tro = (item.VaiTroHuong or "").strip()
        entry = {
            "name": item.id_NhomHuong.TenNhomHuong,
            "icon": item.id_NhomHuong.IconUrl.url if item.id_NhomHuong.IconUrl else "",
        }
        if vai_tro.strip() == "Top Notes":
            pyramid["top"].append(entry)
        elif vai_tro.strip() == "Heart Notes":
            pyramid["heart"].append(entry)
        elif vai_tro.strip() == "Base Notes":
            pyramid["base"].append(entry)
        else:
            pyramid["other"].append(entry)
 
    # Nếu không có top/heart/base → đưa tất cả vào "other" để vẫn hiển thị
    if not (pyramid["top"] or pyramid["heart"] or pyramid["base"]):
        # Không có tầng → đưa tất cả vào other để hiển thị flat
        pyramid["other"] = [
            {
                "name": item.id_NhomHuong.TenNhomHuong,
                "icon": item.id_NhomHuong.IconUrl.url if item.id_NhomHuong.IconUrl else "",
            }
            for item in nhom_huongs
        ]

    nhom_huong_pyramid = pyramid if any([
        pyramid["top"], pyramid["heart"], pyramid["base"], pyramid["other"]
    ]) else None

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
        # "is_favorite": is_favorite,
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
        "nhom_huong_pyramid": nhom_huong_pyramid,
        "related_products": related_products,
        "brand_slug": slugify(product_obj.id_ThuongHieu.TenThuongHieu),
        "similar_scent_products": similar_scent_products,
        "is_favorite": is_favorite,
    })


def brand_list(request):
    brands = list(ThuongHieu.objects.all().order_by("TenThuongHieu"))
    # brands = []
    # for row in brand_rows:
    #     name = row["TenThuongHieu"]
    #     slug = slugify(name)
    #     brands.append(
    #         {
    #             "slug": slug,
    #             "name": name,
    #             "tagline": "Tinh hoa mùi hương đẳng cấp",
    #             "palette": "#6f7d62",
    #             "poster_image": row["LogoUrl"] or FALLBACK_IMAGES["brand_poster"],
    #             "category": "Designer" if len(name) % 2 == 0 else "Niche",
    #         }
    #     )
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
        "cover": article_obj.AnhDaiDien.url if article_obj.AnhDaiDien else FALLBACK_IMAGES["article_cover"],
        "body": [{"type": "p", "text": article_obj.NoiDung or ""}],
    }

    related_articles = [
        {
            "id": item.id_BaiViet,
            "title": item.TieuDe,
            "cover": item.AnhDaiDien.url if item.AnhDaiDien else FALLBACK_IMAGES["article_cover"],
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

@csrf_exempt
@require_POST
def contact_send(request):
    name    = (request.POST.get('name')    or '').strip()
    email   = (request.POST.get('email')   or '').strip()
    phone   = (request.POST.get('phone')   or '').strip()
    subject = (request.POST.get('subject') or '').strip()
    message = (request.POST.get('message') or '').strip()

    if not all([name, email, subject, message]):
        return JsonResponse({'ok': False, 'message': 'Vui lòng điền đầy đủ thông tin.'})

    from django.core.mail import EmailMessage

    # ── Email gửi đến cửa hàng ──
    body_store = f"""Tin nhắn mới từ website Ami Perfumery
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Họ tên:        {name}
Email:         {email}
Số điện thoại: {phone}
Chủ đề:        {subject}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{message}

↩ Reply email này để trả lời trực tiếp cho khách: {email}
"""

    # ── Email xác nhận gửi cho khách ──
    body_customer = f"""Xin chào {name},

Ami Perfumery đã nhận được tin nhắn của bạn.
Chúng tôi sẽ phản hồi trong vòng 24 giờ!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nội dung bạn đã gửi:
Chủ đề: {subject}

{message}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Trân trọng,
Ami Perfumery
📍 123 Đường 30/4, Quận Ninh Kiều, Cần Thơ
📞 0901 234 567
"""

    try:
        # Gửi cho cửa hàng
        mail_store = EmailMessage(
            subject=f'[Ami Web] {subject} — {name}',
            body=body_store,
            from_email='Ami Perfumery <lhngocc1304@gmail.com>',
            to=['lhngocc1304@gmail.com'],
            reply_to=[f'{name} <{email}>'],
        )
        mail_store.send(fail_silently=False)

        # Gửi xác nhận cho khách
        mail_customer = EmailMessage(
            subject='Ami Perfumery đã nhận tin nhắn của bạn ✨',
            body=body_customer,
            from_email='Ami Perfumery <lhngocc1304@gmail.com>',
            to=[email],
        )
        mail_customer.send(fail_silently=False)

        return JsonResponse({'ok': True})

    except Exception as e:
        print(f'[contact_send] Lỗi gửi mail: {e}')
        return JsonResponse({'ok': False, 'message': 'Không thể gửi email. Vui lòng thử lại sau.'})


def cart_page(request):
    account_id = request.session.get("account_id")
 
    suggestions = _build_product_cards(
        _safe_list(
            SanPham.objects.select_related("id_ThuongHieu", "id_LoaiSanPham")
                           .prefetch_related("nhom_huongs")
                           .order_by("-id_SanPham")[:8]
        )
    )[:4]
 
    voucher_data = []
    account      = None
    if account_id:
        voucher_data = _get_available_vouchers(account_id)
        account      = _safe_first(TaiKhoan.objects.filter(id_TaiKhoan=account_id))
 
    return render(request, 'app/cart.html', {
        'suggestions':  suggestions,
        'voucher_data': voucher_data,
        'is_logged_in': bool(account_id),
        'account':      account,
    })



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
        return JsonResponse({"ok": False, "need_login": True, "message": "Vui lòng đăng nhập để đánh giá."})

    last_submit = request.session.get("review_last_submit")
    now_ts = timezone.now().timestamp()
    if last_submit and now_ts - float(last_submit) < 8:
        return JsonResponse({"ok": False, "message": "Bạn đang thao tác quá nhanh, vui lòng thử lại sau vài giây."}, status=429)

    order_id = request.POST.get("order_id")
    product_id = request.POST.get("product_id")

    try:
        rating = int(request.POST.get("rating") or 0)
    except ValueError:
        rating = 0

    content = escape((request.POST.get("content") or "").strip())

    if not order_id:
        return JsonResponse({"ok": False, "message": "Thiếu mã đơn hàng."}, status=400)

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

    customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()

    order_filter = Q(id_DonHang=order_id) & Q(TrangThai="Hoàn tất")

    if customer:
        order_filter &= (
            Q(id_KhachHang=customer) |
            Q(id_GiaoHang__id_TaiKhoan_id=account_id)
        )
    else:
        order_filter &= Q(id_GiaoHang__id_TaiKhoan_id=account_id)

    order = DonHang.objects.filter(order_filter).first()

    if not order:
        return JsonResponse({
            "ok": False,
            "message": "Đơn hàng chưa hoàn tất hoặc không thuộc tài khoản của bạn."
        }, status=403)

    product_in_order = ChiTietDonHang.objects.filter(
        id_DonHang=order,
        id_BienThe__id_SanPham=product
    ).exists()

    if not product_in_order:
        return JsonResponse({
            "ok": False,
            "message": "Sản phẩm này không thuộc đơn hàng cần đánh giá."
        }, status=403)

    already_reviewed = DanhGia.objects.filter(
        id_DonHang=order,
        id_SanPham=product,
        id_TaiKhoan=account,
        parent_id__isnull=True
    ).exists()

    if already_reviewed:
        return JsonResponse({
            "ok": False,
            "message": "Bạn đã đánh giá sản phẩm trong đơn hàng này rồi."
        }, status=400)

    review = DanhGia.objects.create(
        id_DonHang=order,
        id_SanPham=product,
        id_TaiKhoan=account,
        SoSao=rating,
        NoiDung=content,
        parent_id=None,
        NgayDanhGia=timezone.now(),
    )

    request.session["review_last_submit"] = now_ts

    config = CauHinhThanhVien.objects.filter(
        TrangThai='active'
    ).order_by('MucChiTieuToiThieu').first()

    review_bonus = int(config.ThuongDanhGia or 100) if config else 100

    add_points(
        account,
        review_bonus,
        "review_bonus",
        f"Thưởng đánh giá sản phẩm trong đơn {order.MaDonHang}",
        order
    )

    update_member_level(account)

    return JsonResponse({
        "ok": True,
        "message": "Cảm ơn bạn đã chia sẻ trải nghiệm cùng Ami Perfume.",
        "reviewed": True,
        "order_id": order.id_DonHang,
        "product_id": product.id_SanPham,
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
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"liked": False})
    try:
        account = TaiKhoan.objects.get(id_TaiKhoan=account_id)
        liked = YeuThich.objects.filter(
            id_TaiKhoan=account,
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
        KhachHang.objects
        .select_related("id_TaiKhoan")
        .filter(id_TaiKhoan_id=account_id)
    )
    print(f"[DEBUG] account={account_id}, customer={customer}, gender={customer.GioiTinh if customer else 'NO CUSTOMER'}")

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
    try:
        wish_rows = list(
            YeuThich.objects
            .select_related("id_SanPham", "id_SanPham__id_ThuongHieu")
            .filter(id_TaiKhoan_id=account_id)
        )
        wish_product_ids = [w.id_SanPham_id for w in wish_rows if w.id_SanPham_id]
        wish_image_map   = _product_image_map(wish_product_ids) if wish_product_ids else {}
 
        for w in wish_rows:
            product = w.id_SanPham
            if not product:
                continue
            images        = wish_image_map.get(product.id_SanPham, [])
            first_variant = BienThe.objects.filter(id_SanPham=product).order_by("id_BienThe").first()
            wishlist_data.append({
                "id":           w.id_YeuThich,
                "product_id":   product.id_SanPham,
                "product_name": product.TenSanPham,
                "brand":        product.id_ThuongHieu.TenThuongHieu if product.id_ThuongHieu else "",
                "image":        images[0] if images else FALLBACK_IMAGES["default"],
                "price":        _format_currency(first_variant.GiaBan if first_variant else None),
            })
    except Exception:
        import traceback; traceback.print_exc()

    profile = {
        "full_name": (customer.TenKhachHang if customer else None)
                     or (account.TenDangNhap if account else "") or "Khách hàng",
        "username":  (account.Username if account else "") or "guest",
        "email":     (account.Email if account else "") or "",
        "phone":     (account.SDT if account else "") or "",
        "address":   (customer.DiaChi if customer else "") or "",
        "gender":    (customer.GioiTinh if customer else "") or "",
        "points": account.DiemTichLuy if account else 0,

        "level": account.HangThanhVien if account else "Member",

        "total_spending": _format_currency(
            account.TongChiTieu if account else 0
        ),
        "profile_avatar": (
            account.AnhDaiDien.url
            if account and account.AnhDaiDien
            else "/static/app/images/default-avatar.png"
        ),
    }

    print("WISHLIST DATA:", wishlist_data)
    vouchers = _get_available_vouchers(account_id)

    point_logs = []

    if account:

        point_logs = list(

            LichSuDiem.objects
            .filter(id_TaiKhoan=account)
            .order_by("-NgayTao")[:20]

        )
    return render(request, 'app/profile.html', {
        "profile":       profile,
        "review_data":   review_data,
        "wishlist_data": wishlist_data,
        "voucher_data": vouchers,
        "point_logs": point_logs,
    })


def checkout_page(request):
    account_id = request.session.get("account_id")
 
    delivery  = None
    form_data = {"name": "", "phone": "", "email": "", "address": "", "note": ""}
 
    if account_id:
        # Lấy thông tin giao hàng gần nhất của tài khoản này
        delivery = _safe_first(
            GiaoHang.objects
            .filter(id_TaiKhoan_id=account_id)
            .order_by("-id_GiaoHang")
        )
        if delivery:
            form_data["name"]    = delivery.TenNguoiNhan or ""
            form_data["phone"]   = delivery.SDT          or ""
            form_data["address"] = delivery.DiaChi       or ""
            form_data["note"]    = _clean_delivery_note(delivery.GhiChu)
 
        # Email lấy từ TaiKhoan
        acc = _safe_first(TaiKhoan.objects.filter(id_TaiKhoan=account_id))
        if acc:
            form_data["email"] = acc.Email or ""
            if not form_data["name"]:
                form_data["name"] = acc.TenDangNhap or ""
 
    return render(request, 'app/checkout.html', {
        "checkout":     form_data,
        "is_logged_in": bool(account_id),
        "voucher_data": _get_available_vouchers(account_id) if account_id else [],
    })


@csrf_exempt
@require_POST
def place_order_api(request):
    """
    Nhận thông tin từ checkout.js → lưu GiaoHang + DonHang + ChiTietDonHang
    """
    account_id = request.session.get("account_id")
 
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": False, "message": "Dữ liệu không hợp lệ."}, status=400)
 
    name       = (body.get("name")    or "").strip()
    phone      = (body.get("phone")   or "").strip()
    address    = (body.get("address") or "").strip()
    note       = (body.get("note")    or "").strip()
    payment    = (body.get("payment") or "cod").strip()
    items      = body.get("items", [])
    total      = float(body.get("total") or 0)
    voucher_cd = (body.get("voucher_code") or "").strip().upper()
    pts_used   = int(body.get("points_used") or 0)
    pts_disc   = float(body.get("points_discount") or 0)
 
    if not name or not phone or not address:
        return JsonResponse({"ok": False, "message": "Thiếu thông tin giao hàng."}, status=400)
    if not items:
        return JsonResponse({"ok": False, "message": "Giỏ hàng trống."}, status=400)
 
    ma_don = "AMI-" + "".join(random.choices(string.digits, k=8))
 
    try:
        account  = None
        customer = None
 
        if account_id:
            account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
            if account:
                customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
 
                # ── FIX: Tự tạo KhachHang nếu chưa có ──────────
                if not customer:
                    customer = KhachHang.objects.create(
                        id_TaiKhoan=account,
                        TenKhachHang=account.TenDangNhap or name,
                        DiaChi=address,
                        GioiTinh='',
                    )
                    print(f"[place_order] Đã tạo KhachHang mới id={customer.id_KhachHang} cho account={account_id}")
 
        # ── 1. Lưu GiaoHang ─────────────────────────────────────
        delivery_note = note
        if voucher_cd:
            delivery_note = f"{note}\n[AMI_VOUCHER:{voucher_cd}]".strip()
        giao_hang = GiaoHang.objects.create(
            id_TaiKhoan_id = account_id if account_id else None,
            TenNguoiNhan   = name,
            SDT            = phone,
            DiaChi         = address,
            GhiChu         = delivery_note,
        )
 
        # ── 2. Lưu DonHang ──────────────────────────────────────
        don_hang = DonHang.objects.create(
            MaDonHang           = ma_don,
            id_KhachHang        = customer,      # Giờ luôn có giá trị nếu đăng nhập
            id_GiaoHang         = giao_hang,
            ThoiGian            = timezone.now(),
            HinhThucThanhToan   = payment,
            TrangThai           = "Chờ xác nhận",
            TongTien            = total,
            DiemDaDung          = pts_used,
            TienGiamTuDiem      = pts_disc,
            DiemNhanDuoc        = 0,
        )
        print(f"[place_order] Đã tạo DonHang {ma_don} | customer={customer} | total={total}")
 
        # ── 3. Lưu ChiTietDonHang ───────────────────────────────
        for item in items:
            product_id = item.get("productId")
            variant_id = item.get("variantId")
            qty        = int(item.get("qty") or 1)
            price      = float(item.get("price") or 0)
 
            bien_the = None
            if variant_id and variant_id != "default":
                if str(variant_id).isdigit():
                    bien_the = BienThe.objects.filter(id_BienThe=int(variant_id)).first()
            if not bien_the and product_id:
                bien_the = BienThe.objects.filter(id_SanPham_id=product_id).order_by("id_BienThe").first()
 
            if bien_the:
                ChiTietDonHang.objects.create(
                    id_DonHang  = don_hang,
                    id_BienThe  = bien_the,
                    SoLuong     = qty,
                    GiaBan      = price,
                    GiaGiam     = 0,
                )
            else:
                print(f"[place_order] WARNING: Không tìm thấy BienThe cho productId={product_id}, variantId={variant_id}")
 
        # ── 4. Đánh dấu voucher đã dùng ─────────────────────────
        if voucher_cd and account_id:
            rel = KhuyenMaiTaiKhoan.objects.filter(
                id_TaiKhoan_id=account_id,
                id_KhuyenMai__MaKhuyenMai__iexact=voucher_cd,
                DaSuDung=False,
            ).first()
            if rel:
                rel.DaSuDung = True
                rel.save(update_fields=["DaSuDung"])
                v = rel.id_KhuyenMai
                if v:
                    v.DaSuDung = int(v.DaSuDung or 0) + 1
                    v.save(update_fields=["DaSuDung"])
 
        # ── 5. Trừ điểm nếu dùng ────────────────────────────────
        if pts_used > 0 and account:
            redeem_points(account, pts_used, order=don_hang)
 
        # ── 6. Cộng điểm đơn đầu tiên ───────────────────────────
        if account and customer:
            order_count = DonHang.objects.filter(id_KhachHang=customer).count()
            if order_count == 1:
                add_points(account, 200, "first_order_bonus",
                           "Thưởng đơn hàng đầu tiên", don_hang)
 
        # ── 7. Cộng điểm thường ─────────────────────────────────
        if account:
            earned = int(total / 10000)
            if earned > 0:
                add_points(account, earned, "earn_order",
                           f"Tích điểm đơn hàng {ma_don}", don_hang)
 
        # ── 8. Cập nhật TongChiTieu & hạng ──────────────────────
        if account:
            account.TongChiTieu = float(account.TongChiTieu or 0) + total
            account.save(update_fields=["TongChiTieu"])
            update_member_level(account)
 
        # ── Return ───────────────────────────────────────────────
        if payment == "vnpay":
            return JsonResponse({
                "ok":       True,
                "order_id": ma_don,
                "redirect": f"/api/vnpay-create/?order_id={ma_don}&amount={int(total)}",
            })
        if payment == "momo":
            return JsonResponse({
                "ok":       True,
                "order_id": ma_don,
                "redirect": f"/api/momo-create/?order_id={ma_don}&amount={int(total)}",
            })
        if payment == "paypal":
            return JsonResponse({
                "ok":       True,
                "order_id": ma_don,
                "redirect": f"/api/paypal-create/?order_id={ma_don}&amount={int(total)}",
            })
 
        # COD
        return JsonResponse({
            "ok":       True,
            "order_id": ma_don,
            "message":  "Đặt hàng thành công!",
        })
 
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({"ok": False, "message": f"Lỗi hệ thống: {str(e)}"}, status=500)


@csrf_exempt
@require_POST
def apply_voucher_api(request):

    account_id = request.session.get("account_id")

    if not account_id:
        return JsonResponse({
            "ok": False,
            "need_login": True,
            "message": "Vui lòng đăng nhập để sử dụng ưu đãi thành viên."
        }, status=401)

    # =========================
    # LẤY DỮ LIỆU
    # =========================
    code = (request.POST.get("code") or "").strip()
    subtotal = float(request.POST.get("subtotal") or 0)

    print("CODE:", code)
    print("SUBTOTAL:", subtotal)

    if not code:
        return JsonResponse({
            "ok": False,
            "message": "Vui lòng nhập mã khuyến mãi."
        }, status=400)

    # =========================
    # TÌM VOUCHER
    # =========================
    voucher = KhuyenMai.objects.filter(
        MaKhuyenMai__iexact=code,
        TrangThai="active"
    ).first()

    print("FOUND VOUCHER:", voucher)

    if not voucher:
        return JsonResponse({
            "ok": False,
            "message": "Mã khuyến mãi không hợp lệ."
        }, status=404)

    # =========================
    # KIỂM TRA USER CÓ SỞ HỮU
    # =========================
    rel = KhuyenMaiTaiKhoan.objects.filter(
        id_TaiKhoan_id=account_id,
        id_KhuyenMai=voucher
    ).first()

    print("USER REL:", rel)

    if not rel:
        return JsonResponse({
            "ok": False,
            "message": "Bạn không sở hữu mã này."
        }, status=403)

    # =========================
    # KIỂM TRA ĐÃ DÙNG
    # =========================
    if rel.DaSuDung:
        return JsonResponse({
            "ok": False,
            "message": "Bạn đã sử dụng mã này."
        }, status=400)

    # =========================
    # KIỂM TRA THỜI GIAN
    # =========================
    now = timezone.now()

    if voucher.NgayBatDau and voucher.NgayBatDau > now:
        return JsonResponse({
            "ok": False,
            "message": "Mã chưa thể sử dụng."
        }, status=400)

    if voucher.NgayKetThuc and voucher.NgayKetThuc < now:
        return JsonResponse({
            "ok": False,
            "message": "Mã đã hết hạn."
        }, status=400)

    # =========================
    # KIỂM TRA SỐ LƯỢNG
    # =========================
    if (
        voucher.SoLuong is not None
        and int(voucher.DaSuDung or 0) >= int(voucher.SoLuong)
    ):
        return JsonResponse({
            "ok": False,
            "message": "Mã khuyến mãi đã hết lượt sử dụng."
        }, status=400)

    # =========================
    # KIỂM TRA ĐƠN TỐI THIỂU
    # =========================
    if subtotal < float(voucher.DonHangToiThieu or 0):
        return JsonResponse({
            "ok": False,
            "message": "Đơn hàng chưa đạt giá trị tối thiểu."
        }, status=400)

    # =========================
    # TÍNH GIẢM GIÁ
    # =========================
    discount = 0
    loai_giam = (voucher.LoaiGiam or "").lower()

    print("LOAI GIAM:", loai_giam)

    # GIẢM %
    if loai_giam == "percent":

        discount = subtotal * (
            float(voucher.GiaTriGiam or 0) / 100
        )

        # GIẢM TỐI ĐA
        if voucher.GiamToiDa:
            discount = min(
                discount,
                float(voucher.GiamToiDa)
            )

    # FREE SHIP
    elif loai_giam == "free_ship":

        discount = 0

    # GIẢM TIỀN CỐ ĐỊNH
    elif loai_giam == "fixed":

        discount = float(voucher.GiaTriGiam or 0)

    print("DISCOUNT:", discount)

    # =========================
    # RESPONSE
    # =========================
    return JsonResponse({
        "ok": True,
        "message": "Áp dụng mã thành công ✨",
        "code": voucher.MaKhuyenMai,
        "discount": int(discount),
        "type": loai_giam,
    })

def logout_view(request):
    logout(request)
    request.session.pop("account_id", None)
    request.session.pop("account_name", None)
    return redirect('home')


@csrf_exempt
@require_POST
def toggle_favorite(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})
 
    product_id = request.POST.get("product_id")
    if not product_id:
        return JsonResponse({"ok": False, "message": "Thiếu product_id."})
 
    try:
        account = TaiKhoan.objects.get(id_TaiKhoan=account_id)
        product = SanPham.objects.get(id_SanPham=product_id)
    except (TaiKhoan.DoesNotExist, SanPham.DoesNotExist):
        return JsonResponse({"ok": False, "message": "Không tìm thấy dữ liệu."})
 
    existing = YeuThich.objects.filter(
        id_TaiKhoan=account,
        id_SanPham=product
    ).first()
 
    if existing:
        existing.delete()
        count = YeuThich.objects.filter(id_TaiKhoan=account).count()
        return JsonResponse({
            "ok":             True,
            "action":         "removed",
            "message":        "Đã xóa khỏi danh sách yêu thích.",
            "wishlist_count": count,
        })
    else:
        YeuThich.objects.create(
            id_TaiKhoan=account,
            id_SanPham=product,
        )
        count = YeuThich.objects.filter(id_TaiKhoan=account).count()
        return JsonResponse({
            "ok":             True,
            "action":         "added",
            "message":        "Đã thêm vào danh sách yêu thích.",
            "wishlist_count": count,
        })

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

# ═══════════════════════════════════════════════════════════════
# Thêm vào views.py — API kiểm tra đơn hàng đầu tiên
# URL: GET /api/check-first-order/
# ═══════════════════════════════════════════════════════════════

def check_first_order_api(request):
    """
    Kiểm tra xem đây có phải đơn hàng đầu tiên của khách không.
    Nếu chưa có đơn nào → freeship tự động.
    """
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"is_first": False, "freeship": False})

    try:
        customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
        if not customer:
            return JsonResponse({"is_first": True, "freeship": True,
                                 "message": "🎁 Đơn hàng đầu tiên — Miễn phí vận chuyển!"})

        has_order = DonHang.objects.filter(
            id_KhachHang=customer
        ).exists()

        if not has_order:
            return JsonResponse({
                "is_first": True,
                "freeship": True,
                "message": "🎁 Đơn hàng đầu tiên — Miễn phí vận chuyển!",
            })
        else:
            return JsonResponse({"is_first": False, "freeship": False})

    except Exception:
        return JsonResponse({"is_first": False, "freeship": False})


# ═══════════════════════════════════════════════════════════════
# Thêm vào urls.py:
# path('api/check-first-order/', views.check_first_order_api, name='check-first-order'),
# ═══════════════════════════════════════════════════════════════


# ── Ký VNPAY ──────────────────────────────────────────────────
def _vnpay_sign(data: dict, secret: str) -> str:
    """
    VNPAY yêu cầu:
    1. Sắp xếp key theo alphabet
    2. Nối thành query string (KHÔNG encode value)
    3. Ký HMAC-SHA512
    """
    # Sắp xếp theo key
    sorted_items = sorted(data.items())
    # Nối chuỗi dạng key=value&key=value (KHÔNG urllib.parse.urlencode)
    query_string = "&".join(f"{k}={v}" for k, v in sorted_items)
    
    # Ký HMAC-SHA512
    signature = hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()
    return signature


# ── Tạo URL thanh toán VNPAY ──────────────────────────────────
def vnpay_create(request):
    order_id = request.GET.get("order_id", "")
    amount   = int(request.GET.get("amount", 0))

    now         = datetime.now()
    create_date = now.strftime("%Y%m%d%H%M%S")
    expire_date = (now + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")

    params = {
        "vnp_Version":    "2.1.0",
        "vnp_Command":    "pay",
        "vnp_TmnCode":    settings.VNPAY_TMN_CODE,
        "vnp_Amount":     str(amount * 100),
        "vnp_CurrCode":   "VND",
        "vnp_TxnRef":     order_id,
        "vnp_OrderInfo":  f"Thanh toan don hang {order_id}",
        "vnp_OrderType":  "other",
        "vnp_Locale":     "vn",
        "vnp_ReturnUrl":  settings.VNPAY_RETURN_URL,
        "vnp_IpAddr":     request.META.get("REMOTE_ADDR", "127.0.0.1"),
        "vnp_CreateDate": create_date,
        "vnp_ExpireDate": expire_date,
    }

    # ── Bước 1: Sắp xếp ──
    sorted_params = sorted(params.items())

    # ── Bước 2: Tạo chuỗi ký — dùng urllib.parse.quote_plus cho value ──
    hash_data = "&".join(
        f"{k}={urllib.parse.quote_plus(str(v), safe='')}"
        for k, v in sorted_params
    )

    # ── Bước 3: Ký HMAC-SHA512 ──
    secure_hash = hmac.new(
        settings.VNPAY_HASH_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()

    # DEBUG
    print("=== VNPAY HASH DATA ===")
    print(hash_data)
    print("HASH:", secure_hash[:20], "...")

    # ── Bước 4: Build URL cuối ──
    query = "&".join(
        f"{k}={urllib.parse.quote_plus(str(v), safe='')}"
        for k, v in sorted_params
    )
    pay_url = f"{settings.VNPAY_URL}?{query}&vnp_SecureHash={secure_hash}"

    return redirect(pay_url)


# ── Nhận kết quả từ VNPAY trả về ─────────────────────────────
def _vnpay_sign_verify(data: dict, secret: str) -> str:
    """Dùng để verify callback từ VNPAY — cùng logic encode."""
    sorted_items = sorted(data.items())
    hash_data = "&".join(
        f"{k}={urllib.parse.quote_plus(str(v), safe='')}"
        for k, v in sorted_items
    )
    return hmac.new(
        secret.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()


def vnpay_return(request):
    params        = dict(request.GET)
    vnp_hash      = request.GET.get("vnp_SecureHash", "")
    order_id      = request.GET.get("vnp_TxnRef", "")
    response_code = request.GET.get("vnp_ResponseCode", "")

    # Loại bỏ hash khỏi params trước khi verify
    verify_params = {
        k: (v[0] if isinstance(v, list) else v)
        for k, v in params.items()
        if k not in ("vnp_SecureHash", "vnp_SecureHashType")
    }

    expected_hash   = _vnpay_sign_verify(verify_params, settings.VNPAY_HASH_SECRET)
    signature_valid = hmac.compare_digest(expected_hash, vnp_hash)

    print("=== VNPAY RETURN ===")
    print("Response code:", response_code)
    print("Signature valid:", signature_valid)
    print("Expected:", expected_hash[:20])
    print("Got:     ", vnp_hash[:20])

    if signature_valid and response_code == "00":
        DonHang.objects.filter(MaDonHang=order_id).exclude(TrangThai__in=["Đã hủy", "Hoàn tất"]).update(TrangThai="Chờ xác nhận")
        return render(request, "app/payment_success.html", {
            "order_id": order_id,
            "message":  "Thanh toán VNPAY thành công!",
        })
    else:
        DonHang.objects.filter(MaDonHang=order_id).update(TrangThai="Thanh toán thất bại")
        return render(request, "app/payment_failed.html", {
            "order_id":      order_id,
            "response_code": response_code,
            "message":       "Thanh toán thất bại hoặc bị hủy.",
        })
    

# Thanh toán MOMO
def momo_create(request):
    order_id   = request.GET.get("order_id", "")
    amount     = int(request.GET.get("amount", 0))
    request_id = str(uuid.uuid4())  # ID duy nhất cho mỗi request
    order_info = f"Thanh toan don hang {order_id}"
    extra_data = ""

    # ── Tạo chữ ký ──────────────────────────────────────────
    raw_signature = (
        f"accessKey={settings.MOMO_ACCESS_KEY}"
        f"&amount={amount}"
        f"&extraData={extra_data}"
        f"&ipnUrl={settings.MOMO_NOTIFY_URL}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={settings.MOMO_PARTNER_CODE}"
        f"&redirectUrl={settings.MOMO_RETURN_URL}"
        f"&requestId={request_id}"
        f"&requestType=payWithMethod"
    )

    signature = hmac.new(
        settings.MOMO_SECRET_KEY.encode("utf-8"),
        raw_signature.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # ── Gọi API MoMo ────────────────────────────────────────
    payload = {
        "partnerCode": settings.MOMO_PARTNER_CODE,
        "partnerName": "Ami Perfumery",
        "storeId":     "AmiStore",
        "requestId":   request_id,
        "amount":      str(amount),
        "orderId":     order_id,
        "orderInfo":   order_info,
        "redirectUrl": settings.MOMO_RETURN_URL,
        "ipnUrl":      settings.MOMO_NOTIFY_URL,
        "requestType": "payWithMethod",
        "extraData":   extra_data,
        "lang":        "vi",
        "signature":   signature,
    }

    print("=== MOMO REQUEST ===")
    print("Raw signature:", raw_signature)
    print("Signature:", signature[:20], "...")

    try:
        res  = http_requests.post(
            settings.MOMO_ENDPOINT,
            json=payload,
            timeout=15
        )
        data = res.json()

        print("=== MOMO RESPONSE ===")
        print(data)

        if data.get("resultCode") == 0:
            return redirect(data["payUrl"])
        else:
            print("MoMo Error:", data.get("message"))
            return render(request, "app/payment_failed.html", {
                "order_id": order_id,
                "message":  f"MoMo: {data.get('message', 'Lỗi không xác định')}",
                "response_code": str(data.get("resultCode", "")),
            })
    except Exception as e:
        import traceback; traceback.print_exc()
        return render(request, "app/payment_failed.html", {
            "order_id": order_id,
            "message":  f"Lỗi kết nối MoMo: {str(e)}",
            "response_code": "",
        })


def momo_return(request):
    """MoMo redirect về đây sau khi thanh toán."""
    result_code = request.GET.get("resultCode", "")
    order_id    = request.GET.get("orderId",    "")
    message     = request.GET.get("message",    "")

    print("=== MOMO RETURN ===")
    print("resultCode:", result_code)
    print("orderId:",    order_id)
    print("message:",    message)

    if result_code == "0":
        DonHang.objects.filter(MaDonHang=order_id).exclude(TrangThai__in=["Đã hủy", "Hoàn tất"]).update(TrangThai="Chờ xác nhận")
        return render(request, "app/payment_success.html", {
            "order_id": order_id,
            "message":  "Thanh toán MoMo thành công!",
        })
    else:
        DonHang.objects.filter(MaDonHang=order_id).update(TrangThai="Thanh toán thất bại")
        return render(request, "app/payment_failed.html", {
            "order_id":      order_id,
            "message":       f"Thanh toán thất bại: {message}",
            "response_code": result_code,
        })


@csrf_exempt
def momo_ipn(request):
    """MoMo gọi IPN để xác nhận server-to-server."""
    try:
        data        = json.loads(request.body)
        result_code = str(data.get("resultCode", ""))
        order_id    = data.get("orderId", "")

        print("=== MOMO IPN ===")
        print(data)

        if result_code == "0":
            DonHang.objects.filter(MaDonHang=order_id).exclude(TrangThai__in=["Đã hủy", "Hoàn tất"]).update(TrangThai="Chờ xác nhận")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    

def my_orders_api(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})
 
    customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
 
    # Query cả 2 trường hợp để không bỏ sót đơn hàng
    if customer:
        orders = list(
            DonHang.objects
            .filter(
                Q(id_KhachHang=customer) |
                Q(id_GiaoHang__id_TaiKhoan_id=account_id)
            )
            .select_related("id_GiaoHang")
            .distinct()
            .order_by("-ThoiGian")
        )
    else:
        # Không có KhachHang → tìm qua GiaoHang
        orders = list(
            DonHang.objects
            .filter(id_GiaoHang__id_TaiKhoan_id=account_id)
            .select_related("id_GiaoHang")
            .order_by("-ThoiGian")
        )
 
    if not orders:
        return JsonResponse({"ok": True, "orders": []})
 
    order_ids = [o.id_DonHang for o in orders]
    details = list(
        ChiTietDonHang.objects
        .filter(id_DonHang_id__in=order_ids)
        .select_related(
            "id_BienThe",
            "id_BienThe__id_SanPham",
            "id_BienThe__id_SanPham__id_ThuongHieu"
        )
    )
 
    detail_map = {}
    product_ids_all = []
    for d in details:
        detail_map.setdefault(d.id_DonHang_id, []).append(d)
        if d.id_BienThe and d.id_BienThe.id_SanPham_id:
            product_ids_all.append(d.id_BienThe.id_SanPham_id)
 
    image_map = _product_image_map(list(set(product_ids_all)))
 
    STATUS_STEP = {
        "Chờ xác nhận":   0,
        "Đã xác nhận":    1,
        "Đang giao":      2,
        "Khách đã nhận hàng": 3,
        "Hoàn tất":       4,
        "Đã hủy":         -1,
        "Đã giao":        3,
        "Đã thanh toán":  1,
        "Thanh toán thất bại": -1,
    }
 
    result = []
    for order in orders:
        items = detail_map.get(order.id_DonHang, [])
        item_list = []
        for d in items:
            bt = d.id_BienThe
            if not bt:
                continue
            sp = bt.id_SanPham
            if not sp:
                continue
            imgs = image_map.get(sp.id_SanPham, [])
            reviewed = DanhGia.objects.filter(
                id_DonHang=order,
                id_SanPham=sp,
                id_TaiKhoan_id=account_id,
                parent_id__isnull=True
            ).exists()
            item_list.append({
                "product_id":   sp.id_SanPham,
                "product_name": sp.TenSanPham,
                "brand":        sp.id_ThuongHieu.TenThuongHieu if sp.id_ThuongHieu else "",
                "image":        imgs[0] if imgs else FALLBACK_IMAGES["default"],
                "qty":          d.SoLuong or 1,
                "price":        _format_currency(d.GiaBan),
                "reviewed": reviewed,
            })
 
        trang_thai = _delivery_status_label(order)
        gh = order.id_GiaoHang
 
        result.append({
            "id":       order.id_DonHang,
            "ma_don":   order.MaDonHang or f"#{order.id_DonHang}",
            "date":     order.ThoiGian.strftime("%d/%m/%Y") if order.ThoiGian else "",
            "status":   trang_thai,
            "step":     STATUS_STEP.get(trang_thai, 0),
            "total":    _format_currency(order.TongTien),
            "payment":  order.HinhThucThanhToan or "COD",
            "payment_status": _payment_status_label(order),
            "items":    item_list,
            "address":  gh.DiaChi if gh else "",
            "receiver": gh.TenNguoiNhan if gh else "",
            "phone":    gh.SDT if gh else "",
        })
 
    return JsonResponse({"ok": True, "orders": result})
 
 
# ── 2. API: Khách xác nhận đã nhận hàng ──────────────────────────
# URL: POST /api/confirm-received/
# Body: order_id
# ──────────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def confirm_received_api(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})
 
    order_id = request.POST.get("order_id")
    if not order_id:
        return JsonResponse({"ok": False, "message": "Thiếu order_id."})
 
    customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
 
    if customer:
        order = DonHang.objects.filter(
            Q(id_KhachHang=customer) | Q(id_GiaoHang__id_TaiKhoan_id=account_id),
            id_DonHang=order_id,
            TrangThai__in=["Đã xác nhận", "Đang giao"]
        ).first()
    else:
        order = DonHang.objects.filter(
            id_DonHang=order_id,
            id_GiaoHang__id_TaiKhoan_id=account_id,
            TrangThai__in=["Đã xác nhận", "Đang giao"]
        ).first()
 
    if not order:
        return JsonResponse({
            "ok": False,
            "message": "Không tìm thấy đơn hàng hoặc đơn chưa đủ điều kiện xác nhận."
        })
 
    order.TrangThai = "Khách đã nhận hàng"
    order.save(update_fields=["TrangThai"])
 
    return JsonResponse({
        "ok":         True,
        "message":    "Cảm ơn bạn đã xác nhận! Ami Perfumery sẽ hoàn tất đơn hàng trong thời gian sớm nhất.",
        "new_status": "Khách đã nhận hàng",
    })
 
 
# ── 3. API: Khách hủy đơn hàng ────────────────────────────────────
# URL: POST /api/cancel-order/
# Body: order_id, reason
# ──────────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def cancel_order_api(request):
    account_id = request.session.get("account_id")
    if not account_id:
        return JsonResponse({"ok": False, "need_login": True})
 
    order_id = request.POST.get("order_id")
    customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
 
    # Tìm đơn hàng qua cả 2 trường hợp
    if customer:
        order = DonHang.objects.filter(
            Q(id_KhachHang=customer) | Q(id_GiaoHang__id_TaiKhoan_id=account_id),
            id_DonHang=order_id,
            TrangThai="Chờ xác nhận"
        ).first()
    else:
        order = DonHang.objects.filter(
            id_DonHang=order_id,
            id_GiaoHang__id_TaiKhoan_id=account_id,
            TrangThai="Chờ xác nhận"
        ).first()
 
    if not order:
        return JsonResponse({
            "ok": False,
            "message": "Không thể hủy đơn này. Đơn hàng đã được xác nhận hoặc đang giao."
        })
 
    order.TrangThai = "Đã hủy"
    order.save(update_fields=["TrangThai"])
 
    account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
    if account and int(order.DiemDaDung or 0) > 0:
        add_points(account, int(order.DiemDaDung), "refund_points",
                   f"Hoàn điểm do hủy đơn {order.MaDonHang}", order)
 
    return JsonResponse({
        "ok":         True,
        "message":    "Đơn hàng đã được hủy thành công.",
        "new_status": "Đã hủy",
    })
 
 
# ═══════════════════════════════════════════════════════════════════
# ADMIN VIEWS — Quản lý đơn hàng
# ═══════════════════════════════════════════════════════════════════
 
# ─────────────────────────────────────────────────────────────────
# ADMIN VIEWS — Quản lý đơn hàng
# ─────────────────────────────────────────────────────────────────

def admin_orders_view(request):
    is_django_admin = bool(
        getattr(request, "user", None)
        and request.user.is_authenticated
        and request.user.is_staff
    )
    account_id = request.session.get("account_id")
    account    = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first() if account_id else None
    if not is_django_admin and (not account or account.LoaiTaiKhoan not in ('admin','staff')):
        return redirect('/admin/login/?next=/admin-orders/')

    status_filter = request.GET.get("status", "all")
    search_q      = (request.GET.get("q") or "").strip()

    orders_qs = DonHang.objects.select_related(
        "id_KhachHang", "id_KhachHang__id_TaiKhoan",
        "id_GiaoHang",  "id_GiaoHang__id_TaiKhoan"
    ).order_by("-ThoiGian")

    if status_filter != "all":
        orders_qs = orders_qs.filter(TrangThai=status_filter)

    if search_q:
        orders_qs = orders_qs.filter(
            Q(MaDonHang__icontains=search_q) |
            Q(id_KhachHang__TenKhachHang__icontains=search_q) |
            Q(id_GiaoHang__TenNguoiNhan__icontains=search_q) |
            Q(id_GiaoHang__SDT__icontains=search_q)
        )

    orders = list(orders_qs[:200])
    order_ids = [o.id_DonHang for o in orders]

    details = list(
        ChiTietDonHang.objects
        .filter(id_DonHang_id__in=order_ids)
        .select_related("id_BienThe", "id_BienThe__id_SanPham",
                        "id_BienThe__id_SanPham__id_ThuongHieu")
    ) if order_ids else []

    detail_map = defaultdict(list)
    for d in details:
        detail_map[d.id_DonHang_id].append(d)

    product_ids_all = list({
        d.id_BienThe.id_SanPham_id
        for d in details
        if d.id_BienThe and d.id_BienThe.id_SanPham_id
    })
    image_map = _product_image_map(product_ids_all)

    for order in orders:
        rows = detail_map.get(order.id_DonHang, [])
        order.admin_items    = rows
        order.admin_products = ", ".join(
            d.id_BienThe.id_SanPham.TenSanPham
            for d in rows if d.id_BienThe and d.id_BienThe.id_SanPham
        ) or "—"
        order.admin_variants = ", ".join(
            d.id_BienThe.Sku for d in rows if d.id_BienThe and d.id_BienThe.Sku
        ) or "—"
        order.admin_quantity    = sum(int(d.SoLuong or 0) for d in rows)
        order.delivery_status   = _delivery_status_label(order)
        order.payment_status    = _payment_status_label(order)

        # Ảnh sản phẩm đầu tiên trong đơn
        first_img = ""
        for d in rows:
            if d.id_BienThe and d.id_BienThe.id_SanPham_id:
                imgs = image_map.get(d.id_BienThe.id_SanPham_id, [])
                if imgs:
                    first_img = imgs[0]
                    break
        order.first_image = first_img

    from django.db.models import Count
    status_counts = {
        row["TrangThai"]: row["cnt"]
        for row in DonHang.objects.values("TrangThai").annotate(cnt=Count("id_DonHang"))
    }

    STATUS_TABS = [
        {"label": "Chờ xác nhận",       "key": "Chờ xác nhận"},
        {"label": "Đã xác nhận",         "key": "Đã xác nhận"},
        {"label": "Đang giao",           "key": "Đang giao"},
        {"label": "Khách đã nhận hàng",  "key": "Khách đã nhận hàng"},
        {"label": "Hoàn tất",            "key": "Hoàn tất"},
        {"label": "Đã hủy",              "key": "Đã hủy"},
    ]
    for tab in STATUS_TABS:
        tab["count"] = status_counts.get(tab["key"], 0)

    return render(request, "admin/orders.html", {
        "orders":        orders,
        "status_filter": status_filter,
        "search_q":      search_q,
        "status_tabs":   STATUS_TABS,
        "total_count":   DonHang.objects.count(),
    })


# ═══════════════════════════════════════════════════════════════════
# ADMIN — Cập nhật trạng thái đơn hàng
# URL: POST /api/admin/update-order-status/
# ═══════════════════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def admin_update_order_status(request):
    is_django_admin = bool(
        getattr(request, "user", None)
        and request.user.is_authenticated
    )
    account_id = request.session.get("account_id")
    if not is_django_admin and not account_id:
        return JsonResponse({"ok": False, "message": "Chưa đăng nhập."}, status=403)

    order_id   = request.POST.get("order_id")
    new_status = (request.POST.get("status") or "").strip()

    VALID = [
        "Chờ xác nhận", "Đã xác nhận", "Đang giao",
        "Khách đã nhận hàng", "Hoàn tất", "Đã hủy"
    ]
    if new_status not in VALID:
        return JsonResponse({"ok": False, "message": "Trạng thái không hợp lệ."})

    order = DonHang.objects.select_related(
        "id_KhachHang", "id_KhachHang__id_TaiKhoan",
        "id_GiaoHang",  "id_GiaoHang__id_TaiKhoan",
    ).filter(id_DonHang=order_id).first()
    if not order:
        return JsonResponse({"ok": False, "message": "Không tìm thấy đơn hàng."})

    # ── Luồng hợp lệ (dùng TrangThai thô trong DB) ──
    FLOW = {
        "Chờ xác nhận":       ["Đã xác nhận",        "Đã hủy"],
        "Đã thanh toán":      ["Đã xác nhận",        "Đã hủy"],
        "Đã xác nhận":        ["Đang giao",           "Đã hủy"],
        "Đang giao":          ["Khách đã nhận hàng"],
        "Khách đã nhận hàng": ["Hoàn tất"],
        "Hoàn tất":           [],
        "Đã hủy":             [],
        "Thanh toán thất bại":[],
    }
    current = (order.TrangThai or "Chờ xác nhận").strip()
    if new_status not in FLOW.get(current, []):
        return JsonResponse({
            "ok": False,
            "message": f"Không thể chuyển từ '{current}' sang '{new_status}'."
        })

    order.TrangThai = new_status
    order.save(update_fields=["TrangThai"])

    # ── Gửi email theo mốc ──
    email_sent = False
    if new_status in ("Đã xác nhận", "Hoàn tất"):
        email_sent = _send_order_status_email(order, new_status)

    # ── Khi Hoàn tất: cộng điểm, cập nhật TongChiTieu, hạng ──
    if new_status == "Hoàn tất":
        acc = _order_account(order)
        if acc:
            total_val = float(order.TongTien or 0)
            acc.TongChiTieu = float(acc.TongChiTieu or 0) + total_val
            acc.save(update_fields=["TongChiTieu"])
            earned = int(total_val / 10000)
            if earned > 0:
                add_points(acc, earned, "earn_order",
                           f"Tích điểm hoàn tất đơn {order.MaDonHang}", order)
            update_member_level(acc)
            order.DiemNhanDuoc = earned
            order.save(update_fields=["DiemNhanDuoc"])

    suffix = " · Email đã gửi." if email_sent else ""
    return JsonResponse({
        "ok":         True,
        "message":    f"Đã cập nhật → {new_status}.{suffix}",
        "new_status": new_status,
        "order_id":   order.id_DonHang,
        "email_sent": email_sent,
    })


# ═══════════════════════════════════════════════════════════════════
# ADMIN — Chi tiết đơn hàng (JSON)
# URL: GET /api/admin/order-detail/?order_id=...
# ═══════════════════════════════════════════════════════════════════
def admin_order_detail_api(request):
    is_django_admin = bool(
        getattr(request, "user", None)
        and request.user.is_authenticated
    )
    account_id = request.session.get("account_id")
    if not is_django_admin and not account_id:
        return JsonResponse({"ok": False, "message": "Chưa đăng nhập."}, status=403)

    order_id = request.GET.get("order_id")
    order = DonHang.objects.select_related(
        "id_KhachHang", "id_GiaoHang",
        "id_KhachHang__id_TaiKhoan", "id_GiaoHang__id_TaiKhoan",
    ).filter(id_DonHang=order_id).first()
    if not order:
        return JsonResponse({"ok": False, "message": "Không tìm thấy đơn hàng."})

    details = list(
        ChiTietDonHang.objects
        .filter(id_DonHang=order)
        .select_related(
            "id_BienThe", "id_BienThe__id_SanPham",
            "id_BienThe__id_SanPham__id_ThuongHieu",
        )
    )
    product_ids = [
        d.id_BienThe.id_SanPham_id for d in details
        if d.id_BienThe and d.id_BienThe.id_SanPham_id
    ]
    image_map = _product_image_map(product_ids)

    items = []
    for d in details:
        bt = d.id_BienThe
        if not bt:
            continue
        sp = bt.id_SanPham
        if not sp:
            continue
        imgs = image_map.get(sp.id_SanPham, [])
        items.append({
            "product_name": sp.TenSanPham,
            "brand":  sp.id_ThuongHieu.TenThuongHieu if sp.id_ThuongHieu else "",
            "image":  imgs[0] if imgs else FALLBACK_IMAGES["default"],
            "sku":    bt.Sku,
            "qty":    d.SoLuong or 1,
            "price":  _format_currency(d.GiaBan),
        })

    gh = order.id_GiaoHang
    kh = order.id_KhachHang

    # ── Tính next_status dựa trên TrangThai thô trong DB ──
    raw_status = (order.TrangThai or "").strip()
    display_status = _delivery_status_label(order)   # trạng thái hiển thị cho người dùng

    FLOW_NEXT = {
        "Chờ xác nhận":       ("Đã xác nhận",        "✅ Xác nhận đơn"),
        "Đã thanh toán":      ("Đã xác nhận",        "✅ Xác nhận đơn"),
        "Đã xác nhận":        ("Đang giao",           "🚚 Bắt đầu giao hàng"),
        "Đang giao":          ("Khách đã nhận hàng",  "📦 Đánh dấu đã giao"),
        "Khách đã nhận hàng": ("Hoàn tất",            "🎉 Hoàn tất đơn hàng"),
    }
    next_action = FLOW_NEXT.get(raw_status) or FLOW_NEXT.get(display_status)

    can_cancel = raw_status in ("Chờ xác nhận", "Đã xác nhận", "Đã thanh toán")

    return JsonResponse({
        "ok": True,
        "order": {
            "id":             order.id_DonHang,
            "ma_don":         order.MaDonHang,
            "date":           order.ThoiGian.strftime("%d/%m/%Y %H:%M") if order.ThoiGian else "",
            "status":         display_status,
            "raw_status":     raw_status,
            "payment":        order.HinhThucThanhToan or "COD",
            "payment_status": _payment_status_label(order),
            "voucher_code":   _extract_voucher_code(order),
            "points_used":    int(order.DiemDaDung or 0),
            "points_discount":_format_currency(order.TienGiamTuDiem),
            "points_earned":  int(order.DiemNhanDuoc or 0),
            "total":          _format_currency(order.TongTien),
            "items":          items,
            "receiver":       gh.TenNguoiNhan if gh else "",
            "phone":          gh.SDT if gh else "",
            "address":        gh.DiaChi if gh else "",
            "note":           _clean_delivery_note(gh.GhiChu) if gh else "",
            "customer":       kh.TenKhachHang if kh else "Khách vãng lai",
            "next_status":    next_action[0] if next_action else None,
            "next_label":     next_action[1] if next_action else None,
            "can_cancel":     can_cancel,
        }
    })

# ═══════════════════════════════════════════════════════════════════
# ADMIN — API đếm đơn mới (dùng cho auto-poll)
# URL: GET /api/admin/new-orders-count/
# ═══════════════════════════════════════════════════════════════════
def admin_new_orders_count(request):
    is_django_admin = bool(
        getattr(request, "user", None)
        and request.user.is_authenticated
    )
    account_id = request.session.get("account_id")
    if not is_django_admin and not account_id:
        return JsonResponse({"ok": False, "count": 0})

    count = DonHang.objects.filter(TrangThai="Chờ xác nhận").count()
    return JsonResponse({"ok": True, "count": count})
 

@csrf_exempt
@require_POST
def update_profile_api(request):
    account_id = request.session.get("account_id")

    def profile_json(payload, status=200):
        return JsonResponse(payload, status=status,
                            json_dumps_params={"ensure_ascii": False})

    if not account_id:
        return profile_json({"ok": False, "need_login": True,
                             "message": "Vui lòng đăng nhập."}, status=401)

    account = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
    if not account:
        return profile_json({"ok": False, "message": "Không tìm thấy tài khoản."}, status=404)

    full_name = (request.POST.get("full_name") or "").strip()
    username  = (request.POST.get("username")  or "").strip()
    email     = (request.POST.get("email")     or "").strip()
    phone     = (request.POST.get("phone")     or "").strip()
    gender    = (request.POST.get("gender")    or "").strip()
    avatar    = request.FILES.get("avatar")

    # ── Validate ──
    if not full_name:
        return profile_json({"ok": False, "message": "Vui lòng nhập họ và tên."}, status=400)
    if not username:
        return profile_json({"ok": False, "message": "Vui lòng nhập tên đăng nhập."}, status=400)

    import re
    if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return profile_json({"ok": False, "message": "Email không đúng định dạng."}, status=400)
    if phone and not re.match(r'^(0|\+84)[0-9]{8,10}$', phone.replace(' ', '')):
        return profile_json({"ok": False, "message": "Số điện thoại không đúng định dạng (VD: 0901234567)."}, status=400)

    if TaiKhoan.objects.filter(Username__iexact=username).exclude(id_TaiKhoan=account_id).exists():
        return profile_json({"ok": False, "message": "Tên đăng nhập đã tồn tại."}, status=409)

    # ── Lưu TaiKhoan ──
    account.TenDangNhap = full_name
    account.Username    = username
    account.Email       = email
    account.SDT         = phone
    if avatar:
        account.AnhDaiDien = avatar

    fields = ["TenDangNhap", "Username", "Email", "SDT"]
    if avatar:
        fields.append("AnhDaiDien")
    account.save(update_fields=fields)

    # ── Lưu KhachHang ──
    customer = KhachHang.objects.filter(id_TaiKhoan=account).first()
    if customer:
        customer.TenKhachHang = full_name
        customer.GioiTinh     = gender
        customer.save(update_fields=["TenKhachHang", "GioiTinh"])
        print(f"[DEBUG] Saved gender='{gender}' for customer id={customer.id_KhachHang}")
        customer.save(update_fields=["TenKhachHang", "GioiTinh"])
    else:
        KhachHang.objects.create(
            id_TaiKhoan=account,
            TenKhachHang=full_name,
            DiaChi="", GioiTinh=gender,
        )

    request.session["account_name"] = full_name

    avatar_url = account.AnhDaiDien.url if account.AnhDaiDien else ""

    return profile_json({
        "ok": True,
        "message": "Cập nhật thành công.",
        "profile": {
            "full_name": full_name,
            "username":  username,
            "email":     email,
            "phone":     phone,
            "gender":    gender,
            "avatar":    avatar_url,
        },
        "avatar": avatar_url,
    })

def api_thuoc_tinh_list(request):
    """Trả về danh sách thuộc tính — không cần đăng nhập."""
    try:
        data = []
        for tt in ThuocTinh.objects.all().order_by('TenThuocTinh'):
            data.append({
                'id': tt.pk,
                'name': str(tt.TenThuocTinh or ''),
            })
        # ensure_ascii=False để tiếng Việt hiển thị đúng
        return JsonResponse({'ok': True, 'data': data}, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'ok': False, 'message': str(e)}, status=500)
 
 
def api_gia_tri_thuoc_tinh(request):
    """Trả về giá trị thuộc tính theo id_ThuocTinh — không cần đăng nhập."""
    tt_id = request.GET.get('thuoc_tinh_id', '').strip()
 
    if not tt_id:
        return JsonResponse({'ok': False, 'message': 'Thiếu thuoc_tinh_id'}, status=400)
 
    try:
        tt_id_int = int(tt_id)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'message': 'thuoc_tinh_id phải là số'}, status=400)
 
    try:
        rows = GiaTriThuocTinh.objects.filter(
            id_ThuocTinh=tt_id_int
        ).order_by('GiaTri')
 
        data = []
        for r in rows:
            data.append({
                'id': r.pk,
                'name': str(r.GiaTri or ''),
            })
 
        print(f"[api_gia_tri] tt_id={tt_id_int}, found={len(data)} rows")
 
        return JsonResponse(
            {'ok': True, 'data': data},
            json_dumps_params={'ensure_ascii': False}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'ok': False, 'message': str(e)}, status=500)
    

# ════════════════════════════════════════════════════════════
# AI — Gợi ý sản phẩm tương tự (Content-based Filtering)
# ════════════════════════════════════════════════════════════
def ai_recommend_api(request, product_id):
    """
    GET /api/recommend/<product_id>/
    Trả về tối đa 8 sản phẩm tương tự dựa trên TF-IDF cosine.
    """
    from app.ai.recommender import get_similar_products

    similar_ids = get_similar_products(product_id, top_n=8)
    if not similar_ids:
        return JsonResponse({"ok": True, "products": []})

    products = list(
        SanPham.objects
        .select_related("id_ThuongHieu", "id_LoaiSanPham")
        .prefetch_related("nhom_huongs")
        .filter(id_SanPham__in=similar_ids)
    )

    # Giữ đúng thứ tự theo độ tương tự
    product_map = {p.id_SanPham: p for p in products}
    ordered = [product_map[pid] for pid in similar_ids if pid in product_map]

    cards = _build_product_cards(ordered)
    return JsonResponse({"ok": True, "products": cards},
                        json_dumps_params={"ensure_ascii": False})


def admin_api_bien_the(request):
    """Trả về danh sách biến thể theo id_SanPham."""
    sp_id = request.GET.get('sp_id')
    if not sp_id:
        return JsonResponse({'ok': False, 'data': []})
    from .models import BienThe, BienTheThuocTinh
    bien_the = BienThe.objects.filter(id_SanPham_id=sp_id)
    data = []
    for bt in bien_the:
        attrs = BienTheThuocTinh.objects.select_related(
            'id_GiaTriThuocTinh__id_ThuocTinh'
        ).filter(id_BienThe=bt)
        attr_str = ', '.join(
            f"{a.id_GiaTriThuocTinh.id_ThuocTinh.TenThuocTinh}: {a.id_GiaTriThuocTinh.GiaTri}"
            for a in attrs
        )
        data.append({
            'id':       bt.id_BienThe,
            'sku':      bt.Sku,
            'gia_nhap': float(bt.GiaNhap or 0),
            'gia_ban':  float(bt.GiaBan or 0),
            'ton_kho':  bt.SoLuong,
            'attrs':    attr_str or bt.Sku,
        })
    return JsonResponse({'ok': True, 'data': data})
 
 
@csrf_exempt
def admin_api_luu_phieu(request):
    """Lưu phiếu nhập + chi tiết + cập nhật tồn kho."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)
 
    try:
        body     = json.loads(request.body)
        phieu_id = body.get('phieu_id')  # None = tạo mới
        ncc_id   = body.get('ncc_id')
        trang_thai = body.get('trang_thai', 'confirmed')
        rows     = body.get('rows', [])   # [{bien_the_id, so_luong, gia_nhap}, ...]
        new_products = body.get('new_products', [])  # sản phẩm mới chưa có
 
        from .models import TaiKhoan as TK, BienThe as BT, ThuocTinh, GiaTriThuocTinh
        from django.db import transaction
 
        with transaction.atomic():
            # 1. Lưu sản phẩm mới nếu có
            for np in new_products:
                sp_name = (np.get('ten_san_pham') or '').strip()
                if not sp_name:
                    continue
                # Tạo SanPham
                new_sp = SanPham.objects.create(
                    TenSanPham=sp_name,
                    TrangThai_SanPham='active',
                )
                # Tạo biến thể cho sản phẩm mới
                for bt_data in np.get('bien_the', []):
                    new_bt = BT.objects.create(
                        id_SanPham=new_sp,
                        Sku=bt_data.get('sku', f'SKU-{new_sp.pk}'),
                        GiaNhap=bt_data.get('gia_nhap', 0),
                        GiaBan=bt_data.get('gia_ban', 0),
                        SoLuong=0,
                    )
                    # Gán thuộc tính
                    for attr in bt_data.get('attrs', []):
                        thuoc_tinh, _ = ThuocTinh.objects.get_or_create(
                            TenThuocTinh=attr.get('ten_thuoc_tinh', 'Dung tích')
                        )
                        gia_tri, _ = GiaTriThuocTinh.objects.get_or_create(
                            id_ThuocTinh=thuoc_tinh,
                            GiaTri=attr.get('gia_tri', '')
                        )
                        BienTheThuocTinh.objects.create(
                            id_BienThe=new_bt,
                            id_GiaTriThuocTinh=gia_tri
                        )
                    # Thêm vào rows để nhập kho
                    rows.append({
                        'bien_the_id': new_bt.id_BienThe,
                        'so_luong':    bt_data.get('so_luong', 0),
                        'gia_nhap':    bt_data.get('gia_nhap', 0),
                    })
 
            # 2. Tạo / cập nhật PhieuNhap
            tk = None
            if request.user.is_authenticated:
                tk = TK.objects.filter(Username=request.user.username).first()
 
            tong_tien = sum(
                float(r.get('gia_nhap', 0)) * int(r.get('so_luong', 0))
                for r in rows
            )
 
            if phieu_id:
                phieu = PhieuNhap.objects.get(pk=phieu_id)
                phieu.TrangThai = trang_thai
                phieu.TongTien  = tong_tien
                if ncc_id:
                    phieu.id_NCC_id = ncc_id
                phieu.save()
                # Xóa chi tiết cũ để ghi lại
                phieu.chi_tiet.all().delete()
            else:
                import random, string
                ma = 'PN' + tz.now().strftime('%y%m%d') + ''.join(
                    random.choices(string.ascii_uppercase + string.digits, k=4)
                )
                phieu = PhieuNhap.objects.create(
                    ThoiGian=tz.now(),
                    id_TaiKhoan=tk,
                    id_NCC_id=ncc_id if ncc_id else None,
                    MaPhieu=ma,
                    TongTien=tong_tien,
                    TrangThai=trang_thai,
                )
 
            # 3. Lưu chi tiết + cập nhật tồn kho
            for r in rows:
                bt_id    = r.get('bien_the_id')
                so_luong = int(r.get('so_luong', 0))
                gia_nhap = float(r.get('gia_nhap', 0))
                if not bt_id or so_luong <= 0:
                    continue
 
                ChiTietNhap.objects.create(
                    id_PhieuNhap=phieu,
                    id_BienThe_id=bt_id,
                    SoLuongNhap=so_luong,
                    GiaNhap=gia_nhap,
                )
 
                if trang_thai in ('confirmed', 'done'):
                    BT.objects.filter(pk=bt_id).update(
                        SoLuong=models.F('SoLuong') + so_luong
                    )
 
        return JsonResponse({
            'ok': True,
            'phieu_id': phieu.id_PhieuNhap,
            'ma_phieu': phieu.MaPhieu,
        })
 
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
 
 
@csrf_exempt
def admin_api_them_sp_moi(request):
    """Kiểm tra tên sản phẩm có tồn tại chưa."""
    if request.method != 'POST':
        return JsonResponse({'ok': False})
    body = json.loads(request.body)
    ten  = (body.get('ten_san_pham') or '').strip()
    if not ten:
        return JsonResponse({'ok': False, 'error': 'Tên trống'})
    exists = SanPham.objects.filter(TenSanPham__iexact=ten).first()
    if exists:
        from .models import BienThe as BT
        bien_the = list(BT.objects.filter(id_SanPham=exists).values(
            'id_BienThe', 'Sku', 'GiaNhap', 'GiaBan', 'SoLuong'
        ))
        return JsonResponse({'ok': True, 'exists': True, 'sp_id': exists.id_SanPham,
                             'ten': exists.TenSanPham, 'bien_the': bien_the})
    return JsonResponse({'ok': True, 'exists': False})


# ════════════════════════════════════════════════════
# CHATBOT AI — RAG + GPT-4o
# ════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def chatbot_api(request):
    """
    POST /api/chatbot/
    Body: { "message": "...", "history": [...] }
    """
    import json as _json
 
    try:
        data     = _json.loads(request.body)
        user_msg = (data.get("message") or "").strip()
        history  = data.get("history") or []
 
        if not user_msg:
            return JsonResponse({"ok": False, "error": "Tin nhắn không được trống."})
 
        if len(history) > 20:
            history = history[-20:]
 
        from app.ai.chatbot import chat
        result = chat(user_msg, history)
 
        # ── Bổ sung ảnh + giá vào suggestions ──────────────────
        suggestions = result.get("suggestions") or []
        if suggestions:
            product_ids = [s["id"] for s in suggestions if s.get("type") == "product"]
            if product_ids:
                img_map     = _product_image_map(product_ids)
                variant_map = _first_variant_map(product_ids)
 
                for s in suggestions:
                    if s.get("type") != "product":
                        continue
                    pid    = s["id"]
                    imgs   = img_map.get(pid, [])
                    s["image"] = imgs[0] if imgs else ""
 
                    variant = variant_map.get(pid)
                    if variant and variant.GiaBan:
                        s["price"] = _format_currency(variant.GiaBan)
                    else:
                        s["price"] = ""
 
        return JsonResponse({
            "ok":          True,
            "reply":       result["reply"],
            "history":     result["history"],
            "suggestions": suggestions,
        }, json_dumps_params={"ensure_ascii": False})
 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "ok":    False,
            "error": "Lỗi hệ thống. Vui lòng thử lại sau."
        }, status=500)
    

# ════════════════════════════════════════════════════════════
# PERSONALIZED RECOMMENDATIONS — Giai đoạn 3
# ════════════════════════════════════════════════════════════
def personalized_recommend_api(request):
    """
    GET /api/recommend/personal/
    Trả về gợi ý cá nhân hóa cho user đang đăng nhập.
    Nếu chưa đăng nhập → trả về sản phẩm phổ biến.
    """
    from app.ai.personalize import (
        get_personalized_recommendations,
        _get_popular_products
    )

    account_id = request.session.get("account_id")

    if account_id:
        product_ids = get_personalized_recommendations(account_id, top_n=8)
    else:
        product_ids = _get_popular_products(top_n=8)

    if not product_ids:
        return JsonResponse({"ok": True, "products": [], "type": "empty"})

    products = list(
        SanPham.objects
        .select_related("id_ThuongHieu", "id_LoaiSanPham")
        .filter(id_SanPham__in=product_ids)
    )

    # Giữ đúng thứ tự theo điểm
    product_map = {p.id_SanPham: p for p in products}
    ordered = [product_map[pid] for pid in product_ids if pid in product_map]

    cards = _build_product_cards(ordered)

    return JsonResponse({
        "ok":      True,
        "products": cards,
        "type":    "personalized" if account_id else "popular",
    }, json_dumps_params={"ensure_ascii": False})


def admin_phieunhap_list(request):
    """Trang lich su phieu nhap kho."""
    from .models import PhieuNhap, NhaCungCap, ChiTietNhap
    from django.db.models import Count, Sum, Q
    from django.utils import timezone as tz
    import datetime
 
    # Query tat ca phieu, sort moi nhat truoc
    phieu_qs = PhieuNhap.objects.select_related(
        'id_TaiKhoan', 'id_NCC'
    ).order_by('-ThoiGian')
 
    # Them so_dong vao tung phieu
    phieu_list = []
    for p in phieu_qs:
        p.so_dong = ChiTietNhap.objects.filter(id_PhieuNhap=p).count()
        phieu_list.append(p)
 
    # Stats
    now = tz.now()
    tong_tien_val = PhieuNhap.objects.filter(
        TrangThai__in=['confirmed', 'done']
    ).aggregate(s=Sum('TongTien'))['s'] or 0
 
    thang_nay = PhieuNhap.objects.filter(
        ThoiGian__year=now.year,
        ThoiGian__month=now.month
    ).count()
 
    stats = {
        'tong_phieu': PhieuNhap.objects.count(),
        'hoan_tat':   PhieuNhap.objects.filter(TrangThai__in=['confirmed','done']).count(),
        'tong_tien':  f"{int(tong_tien_val):,}".replace(",", ".") + "₫",
        'thang_nay':  thang_nay,
    }
 
    context = {
        'phieu_list': phieu_list,
        'ncc_list':   list(NhaCungCap.objects.values('id_NCC', 'Ten_NCC')),
        'stats':      stats,
        'title':      'Lịch sử phiếu nhập kho',
    }
    return render(request, 'admin/phieunhap_list.html', context)
 
 
def admin_api_chi_tiet_phieu(request):
    """API tra ve chi tiet cua 1 phieu nhap."""
    phieu_id = request.GET.get('phieu_id')
    if not phieu_id:
        return JsonResponse({'ok': False, 'error': 'Thieu phieu_id'})
 
    from .models import PhieuNhap, ChiTietNhap, BienThe
 
    try:
        phieu = PhieuNhap.objects.get(pk=phieu_id)
        chi_tiet = ChiTietNhap.objects.select_related(
            'id_BienThe__id_SanPham__id_ThuongHieu'
        ).filter(id_PhieuNhap=phieu)
 
        rows = []
        for ct in chi_tiet:
            bt = ct.id_BienThe
            sp = bt.id_SanPham if bt else None
            rows.append({
                'san_pham':   sp.TenSanPham if sp else '—',
                'thuong_hieu': sp.id_ThuongHieu.TenThuongHieu if sp and sp.id_ThuongHieu else '',
                'sku':        bt.Sku if bt else '—',
                'gia_nhap':   float(ct.GiaNhap or 0),
                'so_luong':   ct.SoLuongNhap or 0,
            })
 
        return JsonResponse({
            'ok':       True,
            'ma_phieu': phieu.MaPhieu or f'PN-{phieu.id_PhieuNhap}',
            'rows':     rows,
        })
    except PhieuNhap.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Khong tim thay phieu'})
 
 
def admin_api_xuat_excel(request):
    """Xuat file Excel cho 1 phieu hoac tat ca phieu."""
    from .models import PhieuNhap, ChiTietNhap
 
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return HttpResponse('Chua cai openpyxl. Chay: pip install openpyxl', status=500)
 
    phieu_id = request.GET.get('phieu_id')
    tat_ca   = request.GET.get('tat_ca') == '1'
 
    wb = openpyxl.Workbook()
 
    # === Styles ===
    OL_COLOR   = '4B672D'
    OL_LT      = 'EBF6C4'
    WHITE      = 'FFFFFF'
    GRAY_BG    = 'F5F5F5'
    BORDER_CLR = 'D0D0D0'
 
    def make_border():
        side = Side(style='thin', color=BORDER_CLR)
        return Border(left=side, right=side, top=side, bottom=side)
 
    def style_header(cell, bg=OL_COLOR, fg=WHITE, size=11, bold=True):
        cell.font      = Font(bold=bold, color=fg, size=size, name='Calibri')
        cell.fill      = PatternFill('solid', fgColor=bg)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border    = make_border()
 
    def style_cell(cell, bold=False, align='left', color='333333'):
        cell.font      = Font(bold=bold, color=color, size=10, name='Calibri')
        cell.alignment = Alignment(horizontal=align, vertical='center')
        cell.border    = make_border()
 
    def fmt_vnd(val):
        try:
            return f"{int(float(val)):,}".replace(',', '.') + '₫'
        except:
            return '—'
 
    def write_phieu_sheet(ws, phieu):
        """Ghi 1 phieu vao 1 sheet."""
        ws.title = (phieu.MaPhieu or f'PN-{phieu.id_PhieuNhap}')[:31]
 
        # === TIEU DE PHIEU ===
        ws.merge_cells('A1:F1')
        c = ws['A1']
        c.value = f'PHIẾU NHẬP KHO — {phieu.MaPhieu or phieu.id_PhieuNhap}'
        c.font      = Font(bold=True, size=14, color=OL_COLOR, name='Calibri')
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.fill      = PatternFill('solid', fgColor=OL_LT)
        ws.row_dimensions[1].height = 32
 
        # === META INFO ===
        meta = [
            ('Mã phiếu',       phieu.MaPhieu or '—'),
            ('Thời gian',      phieu.ThoiGian.strftime('%d/%m/%Y %H:%M') if phieu.ThoiGian else '—'),
            ('Người nhập',     phieu.id_TaiKhoan.TenDangNhap if phieu.id_TaiKhoan else '—'),
            ('Nhà cung cấp',   phieu.id_NCC.Ten_NCC if phieu.id_NCC else '—'),
            ('Trạng thái',     {'draft':'Nháp','confirmed':'Xác nhận','done':'Hoàn tất','cancelled':'Huỷ'}.get(phieu.TrangThai or '', phieu.TrangThai or '—')),
            ('Tổng tiền',      fmt_vnd(phieu.TongTien) if phieu.TongTien else '—'),
        ]
        for i, (label, val) in enumerate(meta):
            row = i + 2
            ws.cell(row=row, column=1, value=label).font = Font(bold=True, color='666666', size=10, name='Calibri')
            ws.cell(row=row, column=1).fill = PatternFill('solid', fgColor='F8FCF0')
            ws.cell(row=row, column=1).border = make_border()
            ws.merge_cells(f'B{row}:F{row}')
            c2 = ws.cell(row=row, column=2, value=val)
            c2.font   = Font(bold=(label in ['Tổng tiền','Mã phiếu']), size=10, name='Calibri',
                             color=OL_COLOR if label == 'Tổng tiền' else '333333')
            c2.border = make_border()
 
        # === HEADER BANG CHI TIET ===
        HDR_ROW = 9
        headers = ['#', 'Tên sản phẩm', 'Thương hiệu', 'SKU / Biến thể', 'Đơn giá nhập', 'Số lượng', 'Thành tiền']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=HDR_ROW, column=col, value=h)
            style_header(cell)
        ws.row_dimensions[HDR_ROW].height = 24
 
        # === CHI TIET ===
        chi_tiet = ChiTietNhap.objects.select_related(
            'id_BienThe__id_SanPham__id_ThuongHieu'
        ).filter(id_PhieuNhap=phieu)
 
        tong = 0
        for i, ct in enumerate(chi_tiet):
            bt = ct.id_BienThe
            sp = bt.id_SanPham if bt else None
            ten_sp    = sp.TenSanPham if sp else '—'
            thuong_hieu = sp.id_ThuongHieu.TenThuongHieu if sp and sp.id_ThuongHieu else '—'
            sku       = bt.Sku if bt else '—'
            gia_nhap  = float(ct.GiaNhap or 0)
            so_luong  = ct.SoLuongNhap or 0
            thanh_tien = gia_nhap * so_luong
            tong += thanh_tien
 
            dr = HDR_ROW + 1 + i
            bg = 'FFFFFF' if i % 2 == 0 else 'F8FCF0'
            row_data = [i+1, ten_sp, thuong_hieu, sku, gia_nhap, so_luong, thanh_tien]
            for col, val in enumerate(row_data, 1):
                cell = ws.cell(row=dr, column=col, value=val)
                align = 'center' if col == 1 else ('right' if col in [5,6,7] else 'left')
                bold  = col in [2, 7]
                color = OL_COLOR if col == 7 else '333333'
                cell.font      = Font(bold=bold, color=color, size=10, name='Calibri')
                cell.alignment = Alignment(horizontal=align, vertical='center')
                cell.border    = make_border()
                cell.fill      = PatternFill('solid', fgColor=bg)
                if col in [5, 7]:
                    cell.number_format = '#,##0'
 
        # === TONG CONG ===
        tong_row = HDR_ROW + 1 + len(list(chi_tiet))
        ws.merge_cells(f'A{tong_row}:F{tong_row}')
        tc = ws.cell(row=tong_row, column=1, value='TỔNG CỘNG')
        tc.font      = Font(bold=True, size=11, color=WHITE, name='Calibri')
        tc.fill      = PatternFill('solid', fgColor=OL_COLOR)
        tc.alignment = Alignment(horizontal='right', vertical='center')
        tc.border    = make_border()
        tv = ws.cell(row=tong_row, column=7, value=tong)
        tv.font         = Font(bold=True, size=12, color=WHITE, name='Calibri')
        tv.fill         = PatternFill('solid', fgColor=OL_COLOR)
        tv.alignment    = Alignment(horizontal='right', vertical='center')
        tv.border       = make_border()
        tv.number_format = '#,##0'
        ws.row_dimensions[tong_row].height = 26
 
        # === COL WIDTH ===
        col_widths = [5, 30, 20, 20, 16, 12, 16]
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
 
    # === XUAT ===
    if tat_ca:
        phieu_list = PhieuNhap.objects.select_related('id_TaiKhoan','id_NCC').order_by('-ThoiGian')
        # Sheet tong hop
        ws_sum = wb.active
        ws_sum.title = 'Tong_hop'
 
        ws_sum['A1'] = 'LỊCH SỬ PHIẾU NHẬP KHO — AMI PERFUMERY'
        ws_sum['A1'].font      = Font(bold=True, size=14, color=OL_COLOR, name='Calibri')
        ws_sum['A1'].fill      = PatternFill('solid', fgColor=OL_LT)
        ws_sum['A1'].alignment = Alignment(horizontal='center')
        ws_sum.merge_cells('A1:G1')
 
        hdrs = ['Mã phiếu', 'Thời gian', 'Người nhập', 'Nhà cung cấp', 'Trạng thái', 'Số dòng', 'Tổng tiền']
        for col, h in enumerate(hdrs, 1):
            style_header(ws_sum.cell(row=2, column=col, value=h))
 
        total_all = 0
        for i, p in enumerate(phieu_list):
            dr = i + 3
            so_dong = ChiTietNhap.objects.filter(id_PhieuNhap=p).count()
            tt_val  = float(p.TongTien or 0)
            total_all += tt_val
            row_vals = [
                p.MaPhieu or f'PN-{p.id_PhieuNhap}',
                p.ThoiGian.strftime('%d/%m/%Y %H:%M') if p.ThoiGian else '—',
                p.id_TaiKhoan.TenDangNhap if p.id_TaiKhoan else '—',
                p.id_NCC.Ten_NCC if p.id_NCC else '—',
                {'draft':'Nháp','confirmed':'Xác nhận','done':'Hoàn tất','cancelled':'Huỷ'}.get(p.TrangThai or '', '—'),
                so_dong,
                tt_val,
            ]
            bg = 'FFFFFF' if i % 2 == 0 else 'F8FCF0'
            for col, val in enumerate(row_vals, 1):
                cell = ws_sum.cell(row=dr, column=col, value=val)
                align = 'right' if col in [6, 7] else 'left'
                cell.font      = Font(size=10, name='Calibri',
                                      bold=(col==7), color=(OL_COLOR if col==7 else '333333'))
                cell.alignment = Alignment(horizontal=align, vertical='center')
                cell.border    = make_border()
                cell.fill      = PatternFill('solid', fgColor=bg)
                if col == 7: cell.number_format = '#,##0'
 
            # Sheet chi tiet cho tung phieu
            ws_p = wb.create_sheet()
            write_phieu_sheet(ws_p, p)
 
        # Dong tong
        tr = len(list(phieu_list)) + 3
        ws_sum.merge_cells(f'A{tr}:F{tr}')
        c = ws_sum.cell(row=tr, column=1, value='TỔNG CỘNG')
        c.font = Font(bold=True, size=11, color=WHITE, name='Calibri')
        c.fill = PatternFill('solid', fgColor=OL_COLOR)
        c.alignment = Alignment(horizontal='right')
        c.border = make_border()
        tv = ws_sum.cell(row=tr, column=7, value=total_all)
        tv.font = Font(bold=True, size=12, color=WHITE, name='Calibri')
        tv.fill = PatternFill('solid', fgColor=OL_COLOR)
        tv.alignment = Alignment(horizontal='right')
        tv.border = make_border()
        tv.number_format = '#,##0'
 
        for i, w in enumerate([18, 18, 16, 20, 14, 10, 16], 1):
            ws_sum.column_dimensions[get_column_letter(i)].width = w
 
        filename = f'LichSuPhieuNhap_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx'
 
    else:
        # Xuat 1 phieu
        try:
            phieu = PhieuNhap.objects.select_related('id_TaiKhoan','id_NCC').get(pk=phieu_id)
        except PhieuNhap.DoesNotExist:
            return HttpResponse('Khong tim thay phieu', status=404)
 
        ws = wb.active
        write_phieu_sheet(ws, phieu)
        filename = f'PhieuNhap_{phieu.MaPhieu or phieu_id}_{timezone.now().strftime("%Y%m%d")}.xlsx'
 
    # Response
    from io import BytesIO
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
 
    response = HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ════════════════════════════════════════════════════
# GIAI ĐOẠN 4 — Ghi nhận click AI recommendation
# ════════════════════════════════════════════════════
@csrf_exempt
@require_POST
def ai_track_click(request):
    """
    POST /api/ai/track-click/
    Body: { "product_id": 9, "source": "content_based" }
    Ghi nhận mỗi lần khách nhấp vào sản phẩm được AI gợi ý.
    """
    try:
        data       = _json.loads(request.body)
        product_id = data.get("product_id")
        source     = data.get("source", "content_based")
        account_id = request.session.get("account_id")

        if not product_id:
            return JsonResponse({"ok": False})

        product = SanPham.objects.filter(id_SanPham=product_id).first()
        if not product:
            return JsonResponse({"ok": False})

        account = None
        if account_id:
            account = TaiKhoan.objects.filter(
                id_TaiKhoan=account_id
            ).first()

        AIRecommendClick.objects.create(
            id_TaiKhoan=account,
            id_SanPham=product,
            source=source,
        )
        return JsonResponse({"ok": True})

    except Exception:
        return JsonResponse({"ok": False})
    

@csrf_exempt
@require_POST
def ai_chatbot_feedback(request):
    """
    POST /api/ai/chatbot-feedback/
    Body: { "rating": 5, "content": "Tư vấn rất tốt" }
    """
    import json as _json
    try:
        data       = _json.loads(request.body)
        rating     = int(data.get("rating") or 0)
        content    = (data.get("content") or "").strip()[:500]
        account_id = request.session.get("account_id")

        if rating < 1 or rating > 5:
            return JsonResponse({"ok": False, "error": "Rating từ 1–5"})

        account = None
        if account_id:
            account = TaiKhoan.objects.filter(
                id_TaiKhoan=account_id
            ).first()

        ChatbotFeedback.objects.create(
            id_TaiKhoan=account,
            Rating=rating,
            NoiDung=content or None,
        )
        return JsonResponse({"ok": True})

    except Exception:
        return JsonResponse({"ok": False})
    
def ai_dashboard_api(request):
    """
    GET /api/admin/ai-dashboard/
    Trả về thống kê hiệu quả AI cho admin dashboard.
    """
    from django.db.models import Count, Avg
    from datetime import timedelta

    # Cách 1: Đăng nhập qua Django Admin (/admin/)
    is_django_admin = bool(
        getattr(request, "user", None)
        and request.user.is_authenticated
        and request.user.is_staff
    )

    # Cách 2: Đăng nhập qua session tự định nghĩa
    account_id = request.session.get("account_id")
    account    = TaiKhoan.objects.filter(
        id_TaiKhoan=account_id
    ).first() if account_id else None
    is_custom_admin = bool(
        account and account.LoaiTaiKhoan in ('admin', 'staff')
    )

    if not is_django_admin and not is_custom_admin:
        return JsonResponse({"ok": False}, status=403)

    # Khoảng thời gian 30 ngày gần nhất
    since = timezone.now() - timedelta(days=30)

    # ── 1. Click-through rate theo nguồn ──────────────────────
    clicks_by_source = list(
        AIRecommendClick.objects
        .filter(NgayClick__gte=since)
        .values('source')
        .annotate(total=Count('id_Click'))
        .order_by('-total')
    )

    # ── 2. Click theo ngày (7 ngày gần nhất) ──────────────────
    clicks_by_day = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        count = AIRecommendClick.objects.filter(
            NgayClick__date=day
        ).count()
        clicks_by_day.append({
            "date":  day.strftime("%d/%m"),
            "count": count,
        })

    # ── 3. Chatbot satisfaction ───────────────────────────────
    feedback_avg = ChatbotFeedback.objects.filter(
        NgayTao__gte=since
    ).aggregate(avg=Avg('Rating'))['avg'] or 0

    feedback_dist = list(
        ChatbotFeedback.objects
        .filter(NgayTao__gte=since)
        .values('Rating')
        .annotate(total=Count('id_Feedback'))
        .order_by('Rating')
    )

    total_feedback = ChatbotFeedback.objects.filter(
        NgayTao__gte=since
    ).count()

    # ── 4. Top sản phẩm được gợi ý nhiều nhất ─────────────────
    top_products = list(
        AIRecommendClick.objects
        .filter(NgayClick__gte=since)
        .values('id_SanPham__TenSanPham', 'id_SanPham__id_SanPham')
        .annotate(total=Count('id_Click'))
        .order_by('-total')[:5]
    )

    return JsonResponse({
        "ok":             True,
        "clicks_by_source": clicks_by_source,
        "clicks_by_day":    clicks_by_day,
        "feedback_avg":     round(float(feedback_avg), 1),
        "feedback_dist":    feedback_dist,
        "total_feedback":   total_feedback,
        "top_products":     top_products,
    }, json_dumps_params={"ensure_ascii": False})

def ai_dashboard_page(request):
    account_id = request.session.get("account_id")
    account    = TaiKhoan.objects.filter(
        id_TaiKhoan=account_id
    ).first() if account_id else None
    if not account or account.LoaiTaiKhoan not in ('admin', 'staff'):
        return redirect('/')
    return render(request, "app/ai_dashboard.html")