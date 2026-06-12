"""
app/ai/evaluation.py
=====================
Module tính các chỉ số đánh giá hiệu quả gợi ý AI (Trục 1).
Dùng cho Chương 4/5 của luận văn — "Đánh giá hiệu quả gợi ý
và mức độ hài lòng của khách hàng".

Các chỉ số:
- CTR (Click-Through Rate)
- Conversion Rate (tỷ lệ click -> mua hàng)
- Coverage (độ phủ sản phẩm được gợi ý)
- Personalization Confidence (độ tin cậy cá nhân hóa trung bình)
- Chatbot Resolution Rate (% phiên chat dẫn đến click sản phẩm)
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg


def calculate_ctr(since_days=30):
    """
    CTR (%) = tổng lượt click / tổng số sản phẩm đã hiển thị qua gợi ý.

    Lưu ý: "impression" được tính theo product_count (số SP hiển thị
    mỗi lần gọi API), không phải số lần gọi API — vì 1 lần gọi có thể
    hiển thị nhiều sản phẩm, mỗi sản phẩm là 1 cơ hội để khách click.
    """
    from app.models import AIRecommendClick, AIRecommendImpression

    since = timezone.now() - timedelta(days=since_days)

    total_impressions = sum(
        AIRecommendImpression.objects
        .filter(NgayHienThi__gte=since)
        .values_list('product_count', flat=True)
    )
    total_clicks = AIRecommendClick.objects.filter(NgayClick__gte=since).count()

    ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
    return {
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "ctr_percent": round(ctr, 2),
    }


def calculate_conversion_rate(since_days=30, window_days=7):
    """
    Conversion (%) = tỷ lệ lượt click (của user đã đăng nhập) dẫn đến
    việc mua CHÍNH sản phẩm đó trong vòng `window_days` ngày sau click.

    Chỉ tính cho user có id_TaiKhoan (vì cần liên kết với DonHang/KhachHang).
    """
    from app.models import AIRecommendClick, ChiTietDonHang

    since = timezone.now() - timedelta(days=since_days)
    clicks = AIRecommendClick.objects.filter(
        NgayClick__gte=since, id_TaiKhoan__isnull=False
    )

    total = clicks.count()
    converted = 0

    for click in clicks:
        window_end = click.NgayClick + timedelta(days=window_days)
        bought = ChiTietDonHang.objects.filter(
            id_BienThe__id_SanPham=click.id_SanPham,
            id_DonHang__id_KhachHang__id_TaiKhoan=click.id_TaiKhoan,
            id_DonHang__ThoiGian__gte=click.NgayClick,
            id_DonHang__ThoiGian__lte=window_end,
        ).exists()
        if bought:
            converted += 1

    rate = (converted / total * 100) if total else 0
    return {
        "total_clicks_with_account": total,
        "converted_to_purchase": converted,
        "conversion_rate_percent": round(rate, 2),
    }


def calculate_coverage():
    """
    Coverage (%) = % sản phẩm từng được AI gợi ý (và khách click)
    ít nhất 1 lần / tổng số sản phẩm trong hệ thống.

    Ý nghĩa: hệ thống có đang "đa dạng hóa" gợi ý hay chỉ lặp lại
    vài sản phẩm cố định (long-tail problem).
    """
    from app.models import SanPham, AIRecommendClick

    total_products = SanPham.objects.count()
    recommended_products = AIRecommendClick.objects.values('id_SanPham').distinct().count()
    coverage = (recommended_products / total_products * 100) if total_products else 0
    return {
        "total_products": total_products,
        "recommended_at_least_once": recommended_products,
        "coverage_percent": round(coverage, 2),
    }


def calculate_avg_confidence():
    """
    Độ tin cậy trung bình của AIUserProfile.ConfidenceScore — đo mức độ
    hệ thống đã "học" được sở thích của khách hàng theo thời gian.
    """
    from app.models import AIUserProfile

    avg = AIUserProfile.objects.aggregate(a=Avg('ConfidenceScore'))['a'] or 0
    distribution = {
        "low_0_0.3": AIUserProfile.objects.filter(ConfidenceScore__lt=0.3).count(),
        "medium_0.3_0.7": AIUserProfile.objects.filter(
            ConfidenceScore__gte=0.3, ConfidenceScore__lt=0.7).count(),
        "high_0.7_1.0": AIUserProfile.objects.filter(ConfidenceScore__gte=0.7).count(),
    }
    return {
        "avg_confidence": round(float(avg), 3),
        "distribution": distribution,
        "total_profiles": AIUserProfile.objects.count(),
    }


def calculate_chatbot_resolution_rate(since_days=30):
    """
    Resolution rate (%) = % phiên chat (theo SessionId, người dùng đã
    đăng nhập) có dẫn đến ít nhất 1 lượt click sản phẩm từ chatbot.

    Ý nghĩa: chatbot tư vấn có "thành công" trong việc dẫn khách đến
    sản phẩm họ quan tâm hay không.
    """
    from app.models import ChatbotHistory, AIRecommendClick

    since = timezone.now() - timedelta(days=since_days)

    total_sessions = (
        ChatbotHistory.objects
        .filter(NgayTao__gte=since, Role='user')
        .values('SessionId').distinct().count()
    )

    chatbot_clicks = AIRecommendClick.objects.filter(
        NgayClick__gte=since, source='chatbot'
    ).values('id_TaiKhoan').distinct().count()

    rate = (chatbot_clicks / total_sessions * 100) if total_sessions else 0
    return {
        "total_chat_sessions": total_sessions,
        "sessions_with_click": chatbot_clicks,
        "resolution_rate_percent": round(rate, 2),
    }


def generate_full_report(since_days=30):
    """Tổng hợp toàn bộ chỉ số Trục 1 — dùng để in/biểu đồ cho Chương 4/5."""
    return {
        "period_days": since_days,
        "ctr": calculate_ctr(since_days),
        "conversion": calculate_conversion_rate(since_days),
        "coverage": calculate_coverage(),
        "personalization": calculate_avg_confidence(),
        "chatbot_resolution": calculate_chatbot_resolution_rate(since_days),
        "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
    }