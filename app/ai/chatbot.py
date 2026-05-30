"""
app/ai/chatbot.py  (HOÀN CHỈNH)
================================
AI Chatbot — RAG + Llama 3.3 (Groq)
Tích hợp Intent Classification để xử lý câu hỏi off-topic.

┌──────────────────┬────────────────────────────────────────────────┐
│ Guest User       │ Session memory + temp AI profile               │
│ Registered User  │ DB persistent memory + deep personalization    │
└──────────────────┴────────────────────────────────────────────────┘

Luồng xử lý:
  1. Keyword check nhanh   → chặn off-topic rõ ràng (0ms)
  2. AI intent classify    → phân loại celebrity_gossip / off_topic (~200ms)
  3. RAG + Generate        → tư vấn đầy đủ nếu hợp lệ
"""
from __future__ import annotations
import os
import re
import uuid
import random
from app.ai.knowledge_base import retrieve


# ════════════════════════════════════════════════════════════════
# A. SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════

BASE_SYSTEM_PROMPT = """Bạn là trợ lý tư vấn nước hoa của cửa hàng Ami Perfumery tại Cần Thơ, Việt Nam.

TÍNH CÁCH: Ấm áp, tinh tế, chuyên nghiệp theo phong cách luxury lifestyle.
Luôn trả lời bằng tiếng Việt tự nhiên, thân thiện.

CÁCH TƯ VẤN:
- Hỏi thêm về dịp dùng (đi làm, tiệc, hẹn hò, quà tặng...) nếu chưa rõ
- Hỏi sở thích mùi hương (hoa, gỗ, tươi mát, ngọt...) nếu chưa rõ
- Gợi ý cụ thể 1-3 sản phẩm phù hợp nhất từ dữ liệu cửa hàng
- Giải thích tại sao sản phẩm đó phù hợp với nhu cầu khách

GIỚI HẠN:
- Chỉ giới thiệu sản phẩm có trong dữ liệu cửa hàng bên dưới
- Nếu không có sản phẩm phù hợp, hãy thành thật và hỏi thêm
- Không bịa thêm thông tin sản phẩm không có trong dữ liệu
- Giới hạn mỗi câu trả lời trong 250 từ

XỬ LÝ CÂU HỎI NGOÀI CHỦ ĐỀ:
- Nếu khách hỏi về chính trị, tin tức, y tế, lập trình, tình cảm cá nhân,
  người nổi tiếng, hoặc bất kỳ chủ đề nào không liên quan đến nước hoa:
  → Trả lời lịch sự, ngắn gọn rằng bạn chỉ tư vấn về nước hoa
  → Khéo léo hướng khách quay lại chủ đề nước hoa"""


# ════════════════════════════════════════════════════════════════
# B. INTENT CLASSIFICATION — Lớp 1: Keyword, Lớp 2: AI
# ════════════════════════════════════════════════════════════════

# Từ khóa liên quan nước hoa → KHÔNG off-topic
_PERFUME_KEYWORDS = [
    'nước hoa', 'mùi', 'hương', 'perfume', 'fragrance', 'chai', 'ml',
    'ami', 'thương hiệu', 'sản phẩm', 'giá', 'mua', 'đặt hàng',
    'giao hàng', 'voucher', 'khuyến mãi', 'review', 'đánh giá',
    'woody', 'floral', 'fresh', 'oriental', 'citrus',
    'tươi', 'ngọt', 'gỗ', 'hoa', 'xạ', 'đông phương',
    'lưu hương', 'tỏa hương', 'edp', 'edt', 'parfum',
    'dior', 'chanel', 'gucci', 'ysl', 'versace', 'burberry',
    'enchanteur', 'victoria', 'secret', 'hugo', 'boss',
    'nam', 'nữ', 'unisex', 'đi làm', 'tiệc', 'hẹn hò', 'quà tặng',
    'mùa hè', 'mùa đông', 'ban ngày', 'ban đêm',
    'đơn hàng', 'ship', 'freeship', 'hoàn tiền', 'đổi trả', 'còn nhớ', 'nhớ không', 'lần trước', 'hôm trước',
    'trước đó', 'đã nói', 'đã hỏi', 'tìm gì',
    'tư vấn cho tôi', 'giúp tôi', 'cho tôi xem',
]

# Từ khóa rõ ràng off-topic
_OFFTOPIC_KEYWORDS = [
    'chính trị', 'bầu cử', 'tổng thống', 'thủ tướng', 'chiến tranh',
    'tin tức', 'thời sự', 'covid', 'vaccine', 'dịch bệnh',
    'code', 'python', 'javascript', 'lập trình', 'thuật toán',
    'machine learning', 'chatgpt', 'openai',
    'bác sĩ', 'thuốc chữa bệnh', 'điều trị', 'chẩn đoán', 'bệnh viện',
    'luật sư', 'kiện tụng', 'tòa án', 'pháp lý',
    'chứng khoán', 'bitcoin', 'crypto', 'đầu tư tài chính', 'forex',
    'bóng đá', 'cầu thủ', 'bàn thắng', 'giải đấu', 'vô địch',
    'phim chiếu', 'diễn viên', 'ca sĩ', 'âm nhạc', 'bài hát',
    'công thức nấu', 'nguyên liệu nấu', 'món ăn',
    'vé máy bay', 'khách sạn', 'visa du lịch',
    'trầm cảm', 'lo âu', 'tự tử',
]


def _is_off_topic_keyword(message: str) -> bool:
    """
    Lớp 1: Keyword check nhanh (0ms, miễn phí).
    Ưu tiên: nếu có từ nước hoa → False (không off-topic).
    """
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in _PERFUME_KEYWORDS):
        return False
    if any(kw in msg_lower for kw in _OFFTOPIC_KEYWORDS):
        return True
    return False


_INTENT_CLASSIFY_PROMPT = """Phân loại câu hỏi sau vào ĐÚNG 1 nhãn:

- perfume_advice   : tư vấn mùi hương, chọn nước hoa
- product_info     : hỏi thông tin sản phẩm, giá, tồn kho
- order_support    : đơn hàng, giao hàng, đổi trả, thanh toán
- memory_recall    : hỏi chatbot có nhớ, lần trước nói gì, tìm gì trước đó
- celebrity_gossip : hỏi người nổi tiếng/ngôi sao dùng gì
- off_topic        : hoàn toàn không liên quan nước hoa

Chỉ trả lời ĐÚNG 1 từ nhãn, không giải thích."""


def _classify_intent_ai(message: str, client) -> str:
    """
    Lớp 2: AI classify (max_tokens=10, ~200ms, rất rẻ).
    Fallback về 'perfume_advice' nếu lỗi.
    """
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=10,
            temperature=0,
            messages=[
                {"role": "system", "content": _INTENT_CLASSIFY_PROMPT},
                {"role": "user",   "content": message},
            ],
        )
        raw = resp.choices[0].message.content.strip().lower()
        valid = {
            'perfume_advice', 'product_info',
            'order_support', 'celebrity_gossip', 'off_topic'
        }
        for label in valid:
            if label in raw:
                return label
        return 'perfume_advice'
    except Exception as e:
        print(f"[chatbot] _classify_intent_ai error: {e}")
        return 'perfume_advice'


# Reply mẫu cho từng intent đặc biệt
_INTENT_REPLIES = {
    "celebrity_gossip": [
        "Mình không có thông tin về sở thích cá nhân của người nổi tiếng đâu bạn ơi! 😄 "
        "Nhưng nếu bạn muốn một mùi hương nam tính, mạnh mẽ và thu hút — "
        "mình có thể gợi ý vài chai rất ấn tượng tại Ami Perfumery đó!",

        "Câu hỏi thú vị đấy! 🌟 Nhưng mình chỉ biết về sản phẩm tại Ami thôi. "
        "Thay vì tìm nước hoa của người nổi tiếng, sao bạn không để mình "
        "giúp tìm một mùi hương 'của riêng bạn' nhỉ? "
        "Bạn thích mùi gỗ, hoa hay tươi mát?",

        "Haha, người nổi tiếng thường giữ bí mật sở thích cá nhân lắm! 😊 "
        "Nhưng mình có thể giúp bạn tìm một mùi hương đẳng cấp không kém — "
        "bạn cần cho dịp gì vậy?",
    ],
    "off_topic": [
        "Xin lỗi bạn nhé! 😊 Mình chỉ có thể tư vấn về nước hoa "
        "và sản phẩm tại Ami Perfumery thôi. "
        "Bạn đang tìm kiếm hương thơm cho dịp nào không?",

        "Câu hỏi này nằm ngoài chuyên môn của mình rồi! 🌸 "
        "Mình là trợ lý tư vấn nước hoa — hãy để mình giúp bạn "
        "tìm mùi hương ưng ý nhất nhé?",

        "Mình chỉ là chuyên gia về mùi hương thôi bạn ơi! 😄 "
        "Nếu có thắc mắc về nước hoa hay sản phẩm tại Ami, "
        "mình sẵn sàng hỗ trợ ngay!",
    ],
}


# ════════════════════════════════════════════════════════════════
# C. PREFERENCE EXTRACTION — giữ nguyên từ v2
# ════════════════════════════════════════════════════════════════

_SCENT_KEYWORDS = {
    'Woody':    ['gỗ', 'woody', 'đàn hương', 'sandalwood', 'cedar', 'trầm'],
    'Floral':   ['hoa', 'floral', 'hồng', 'nhài', 'hoa hồng', 'jasmine', 'rose'],
    'Fresh':    ['tươi', 'fresh', 'biển', 'cam', 'chanh', 'aquatic', 'mát'],
    'Oriental': ['oriental', 'ấm', 'vani', 'vanilla', 'hổ phách', 'amber', 'musk'],
    'Citrus':   ['citrus', 'cam', 'chanh', 'bergamot', 'bưởi'],
    'Gourmand': ['ngọt', 'gourmand', 'caramel', 'chocolate', 'bánh'],
    'Aromatic': ['thảo mộc', 'aromatic', 'lavender', 'oải hương'],
    'Chypre':   ['chypre', 'mossy', 'oak'],
    'Fougere':  ['fougere', 'nam tính', 'classic'],
}

_OCCASION_KEYWORDS = {
    'office':  ['đi làm', 'công sở', 'văn phòng', 'meeting', 'họp'],
    'evening': ['tiệc', 'dạ tiệc', 'đêm', 'party', 'event'],
    'casual':  ['hàng ngày', 'casual', 'đi chơi', 'dạo phố'],
    'date':    ['hẹn hò', 'date', 'lãng mạn', 'romantic'],
    'sport':   ['thể thao', 'sport', 'gym', 'tập'],
    'gift':    ['quà', 'tặng', 'gift'],
}

_GENDER_KEYWORDS = {
    'nam':    ['nam', 'male', 'men', 'anh', 'bạn nam', 'cho nam'],
    'nu':     ['nữ', 'female', 'women', 'chị', 'bạn nữ', 'cho nữ'],
    'unisex': ['unisex', 'trung tính', 'cả hai'],
}


def _extract_intent(text: str) -> dict:
    """Trích xuất preference từ tin nhắn — giữ nguyên từ v2."""
    text_lower = text.lower()
    result = {}

    for scent, kws in _SCENT_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            result.setdefault('scents', []).append(scent)

    for occ, kws in _OCCASION_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            result.setdefault('occasions', []).append(occ)

    for gender, kws in _GENDER_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            result['gender'] = gender
            break

    price_match = re.search(r'(\d{2,4})[kK]?\s*[-–]\s*(\d{2,4})[kK]?', text)
    if price_match:
        result['price_min'] = int(price_match.group(1)) * 1000
        result['price_max'] = int(price_match.group(2)) * 1000
    elif re.search(r'dưới\s*(\d+)[kK]', text_lower):
        m = re.search(r'dưới\s*(\d+)[kK]', text_lower)
        result['price_max'] = int(m.group(1)) * 1000

    return result


# ════════════════════════════════════════════════════════════════
# D. GUEST SESSION HELPERS — giữ nguyên từ v2
# ════════════════════════════════════════════════════════════════

def _build_guest_context_prompt(request) -> str:
    lines = []
    temp_profile = request.session.get('guest_ai_profile', {})
    if temp_profile:
        if temp_profile.get('scents'):
            lines.append(f"Khách thích nhóm mùi: {', '.join(temp_profile['scents'])}")
        if temp_profile.get('gender'):
            lines.append(f"Giới tính nước hoa ưa thích: {temp_profile['gender']}")
        if temp_profile.get('occasions'):
            lines.append(f"Dịp dùng: {', '.join(temp_profile['occasions'])}")
        if temp_profile.get('price_max'):
            lines.append(f"Ngân sách tối đa: {temp_profile['price_max']:,}đ")

    current_product = request.session.get('current_viewing_product')
    if current_product:
        lines.append(f"Khách đang xem sản phẩm: {current_product}")

    try:
        from app.ai.recently_viewed import guest_get_viewed
        viewed_ids = guest_get_viewed(request)
        if viewed_ids:
            from app.models import SanPham
            names = list(SanPham.objects.filter(
                id_SanPham__in=viewed_ids[:3]
            ).values_list('TenSanPham', flat=True))
            if names:
                lines.append(f"Sản phẩm đã xem trong phiên: {', '.join(names)}")
    except Exception:
        pass

    return ("\nCONTEXT KHÁCH HÀNG HIỆN TẠI:\n"
            + "\n".join(f"- {l}" for l in lines)) if lines else ""


def _update_guest_temp_profile(request, intent: dict) -> None:
    profile = request.session.get('guest_ai_profile', {})
    if intent.get('scents'):
        existing = set(profile.get('scents', []))
        existing.update(intent['scents'])
        profile['scents'] = list(existing)[:5]
    if intent.get('gender'):
        profile['gender'] = intent['gender']
    if intent.get('occasions'):
        existing = set(profile.get('occasions', []))
        existing.update(intent['occasions'])
        profile['occasions'] = list(existing)[:3]
    if intent.get('price_max'):
        profile['price_max'] = intent['price_max']
    profile['confidence'] = min(1.0, profile.get('confidence', 0) + 0.15)
    request.session['guest_ai_profile'] = profile
    request.session.modified = True


# ════════════════════════════════════════════════════════════════
# E. REGISTERED USER HELPERS — giữ nguyên từ v2
# ════════════════════════════════════════════════════════════════

def _build_user_context_prompt(account_id: int) -> str:
    lines = []
    try:
        from app.models import (
            AIUserProfile, TaiKhoan, YeuThich,
            SanPham, ChiTietDonHang, DonHang, KhachHang
        )
        tk = TaiKhoan.objects.filter(id_TaiKhoan=account_id).first()
        if tk and tk.TenDangNhap:
            lines.append(f"Tên khách hàng: {tk.TenDangNhap}")

        profile = AIUserProfile.objects.filter(
            id_TaiKhoan_id=account_id
        ).first()
        if profile and profile.ConfidenceScore > 0.1:
            scents = profile.get_nhom_mua()
            brands = profile.get_thuong_hieu()
            if scents:
                lines.append(f"Nhóm mùi yêu thích: {', '.join(scents[:3])}")
            if brands:
                lines.append(f"Thương hiệu ưa thích: {', '.join(brands[:3])}")
            if profile.GiaMin and profile.GiaMax:
                lines.append(
                    f"Khoảng giá thường mua: "
                    f"{int(profile.GiaMin):,}đ – {int(profile.GiaMax):,}đ"
                )

        customer = KhachHang.objects.filter(id_TaiKhoan_id=account_id).first()
        if customer:
            recent_orders = DonHang.objects.filter(
                id_KhachHang=customer,
                TrangThai__in=['Hoàn tất', 'Khách đã nhận hàng']
            ).order_by('-ThoiGian')[:2].values_list('id_DonHang', flat=True)
            if recent_orders:
                bought = list(SanPham.objects.filter(
                    bienthe__chiTietDonHang__id_DonHang_id__in=list(recent_orders)
                ).distinct().values_list('TenSanPham', flat=True)[:3])
                if bought:
                    lines.append(f"Đã từng mua: {', '.join(bought)}")

        wish_ids = list(YeuThich.objects.filter(
            id_TaiKhoan_id=account_id
        ).values_list('id_SanPham_id', flat=True)[:3])
        if wish_ids:
            wish_names = list(SanPham.objects.filter(
                id_SanPham__in=wish_ids
            ).values_list('TenSanPham', flat=True))
            if wish_names:
                lines.append(f"Yêu thích: {', '.join(wish_names)}")

        try:
            from app.ai.recently_viewed import user_get_viewed
            viewed_ids = user_get_viewed(account_id, limit=3)
            if viewed_ids:
                view_names = list(SanPham.objects.filter(
                    id_SanPham__in=viewed_ids
                ).values_list('TenSanPham', flat=True))
                if view_names:
                    lines.append(f"Xem gần đây: {', '.join(view_names)}")
        except Exception:
            pass

    except Exception:
        pass

    return ("\nHỒ SƠ KHÁCH HÀNG CÁ NHÂN HÓA:\n"
            + "\n".join(f"- {l}" for l in lines)) if lines else ""


def _save_chatbot_history(account_id: int, session_id: str,
                           user_msg: str, bot_reply: str,
                           intent: dict) -> None:
    try:
        from app.models import ChatbotHistory
        parts = []
        if intent.get('gender'):
            parts.append(intent['gender'])
        if intent.get('scents'):
            parts.extend(intent['scents'][:2])
        if intent.get('occasions'):
            parts.extend(intent['occasions'][:1])
        intent_str = '_'.join(parts) if parts else None

        ChatbotHistory.objects.create(
            id_TaiKhoan_id=account_id,
            SessionId=session_id,
            Role='user',
            NoiDung=user_msg[:2000],
            ExtractedIntent=intent_str,
        )
        ChatbotHistory.objects.create(
            id_TaiKhoan_id=account_id,
            SessionId=session_id,
            Role='assistant',
            NoiDung=bot_reply[:2000],
        )
        # Giới hạn 200 bản ghi
        count = ChatbotHistory.objects.filter(
            id_TaiKhoan_id=account_id
        ).count()
        if count > 200:
            oldest = list(
                ChatbotHistory.objects
                .filter(id_TaiKhoan_id=account_id)
                .order_by('NgayTao')
                .values_list('id_History', flat=True)[:count - 200]
            )
            ChatbotHistory.objects.filter(id_History__in=oldest).delete()
    except Exception:
        pass


def _update_profile_from_chatbot(account_id: int, intent: dict) -> None:
    if not intent:
        return
    try:
        from app.models import AIUserProfile
        profile, _ = AIUserProfile.objects.get_or_create(
            id_TaiKhoan_id=account_id
        )
        if intent.get('scents'):
            existing = profile.get_nhom_mua()
            merged   = list(dict.fromkeys(intent['scents'] + existing))[:5]
            profile.set_nhom_mua(merged)
        if intent.get('gender') and not profile.GioiTinhUuTien:
            profile.GioiTinhUuTien = intent['gender']
        if intent.get('occasions'):
            cur = profile.DipDungUuTien or ''
            all_occ = list(set(
                (cur.split(',') if cur else []) + intent['occasions']
            ))[:3]
            profile.DipDungUuTien = ','.join(all_occ)
        if intent.get('price_max') and not profile.GiaMax:
            profile.GiaMax = intent['price_max']
            profile.GiaMin = intent['price_max'] * 0.5
        profile.ConfidenceScore = min(1.0, profile.ConfidenceScore + 0.1)
        profile.SoLanCapNhat += 1
        profile.save()
    except Exception:
        pass


def _load_recent_chatbot_history(account_id: int, limit: int = 6) -> list:
    try:
        from app.models import ChatbotHistory
        rows = list(reversed(list(
            ChatbotHistory.objects
            .filter(id_TaiKhoan_id=account_id)
            .order_by('-NgayTao')[:limit]
        )))
        return [{"role": r.Role, "content": r.NoiDung} for r in rows]
    except Exception:
        return []


# ════════════════════════════════════════════════════════════════
# F. HÀM CHAT CHÍNH
# ════════════════════════════════════════════════════════════════

def chat(user_message: str, history: list = None,
         request=None, account_id: int | None = None,
         chat_session_id: str | None = None):
    """
    Hàm chat chính với 3 lớp xử lý:
      1. Keyword check  → chặn off-topic rõ ràng
      2. AI classify    → celebrity_gossip / off_topic
      3. RAG + Generate → tư vấn đầy đủ
    """
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

    if not chat_session_id:
        chat_session_id = str(uuid.uuid4())[:16]

    messages = list(history or [])

    # ── Lớp 1: Keyword check (0ms) ────────────────────────────
    if _is_off_topic_keyword(user_message):
        reply = random.choice(_INTENT_REPLIES["off_topic"])
        messages.append({"role": "user",      "content": user_message})
        messages.append({"role": "assistant", "content": reply})
        return {
            "reply":           reply,
            "history":         messages,
            "suggestions":     [],
            "chat_session_id": chat_session_id,
            "intent":          {"type": "off_topic", "layer": "keyword"},
        }

    # ── Lớp 2 + 3 song song: AI classify + RAG retrieve ────────
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        future_topic  = ex.submit(_classify_intent_ai, user_message, client)
        future_chunks = ex.submit(retrieve, user_message, 5)
        topic  = future_topic.result()
        chunks = future_chunks.result()
    # Cả 2 chạy đồng thời → tổng ~300ms thay vì ~400ms

    # Nếu off-topic → trả về luôn
    if topic in _INTENT_REPLIES:
        reply = random.choice(_INTENT_REPLIES[topic])
        messages.append({"role": "user",      "content": user_message})
        messages.append({"role": "assistant", "content": reply})
        if account_id:
            _save_chatbot_history(account_id, chat_session_id,
                                  user_message, reply, {})
        return {
            "reply":           reply,
            "history":         messages,
            "suggestions":     [],
            "chat_session_id": chat_session_id,
            "intent":          {"type": topic, "layer": "ai_classify"},
        }

    # ── Lớp 3: Generate (chunks đã có từ bước song song) ────────
    intent = _extract_intent(user_message)
    context_lines = []
    for i, c in enumerate(chunks, 1):
        prefix = "[SẢN PHẨM]" if c["type"] == "product" else "[BÀI VIẾT]"
        context_lines.append(f"{i}. {prefix} {c['name']}: {c['text']}")
    rag_context = "\n\n".join(context_lines)

    # Personalization context
    if account_id:
        personal_context = _build_user_context_prompt(account_id)
    elif request:
        _update_guest_temp_profile(request, intent)
        personal_context = _build_guest_context_prompt(request)
    else:
        personal_context = ""

    # Assemble system prompt
    full_system = (
        BASE_SYSTEM_PROMPT
        + personal_context
        + "\n\n" + "=" * 50
        + "\nDỮ LIỆU SẢN PHẨM CỬA HÀNG AMI PERFUMERY:\n"
        + "=" * 50 + "\n"
        + rag_context
        + "\n" + "=" * 50
    )

    # Load DB history nếu registered và chưa có history
    if account_id and not messages:
        db_history = _load_recent_chatbot_history(account_id, limit=6)
        if db_history:
            messages = db_history

    messages.append({"role": "user", "content": user_message})

    # Generate
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        temperature=0.7,
        messages=[{"role": "system", "content": full_system}] + messages,
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    # Persist
    if account_id:
        _save_chatbot_history(account_id, chat_session_id,
                              user_message, reply, intent)
        _update_profile_from_chatbot(account_id, intent)

    suggested = [c for c in chunks if c["type"] == "product"][:3]

    return {
        "reply":           reply,
        "history":         messages,
        "suggestions":     suggested,
        "chat_session_id": chat_session_id,
        "intent":          intent,
    }