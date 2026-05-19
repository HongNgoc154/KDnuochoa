import os
from app.ai.knowledge_base import retrieve

# System prompt — định nghĩa tính cách và giới hạn của chatbot
SYSTEM_PROMPT = """Bạn là trợ lý tư vấn nước hoa của cửa hàng Ami Perfumery tại Cần Thơ, Việt Nam.

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
- Giới hạn mỗi câu trả lời trong 250 từ"""


def chat(user_message: str, history: list = None):
    """
    Xử lý 1 lượt hội thoại theo kiến trúc RAG:
    1. Retrieve: tìm chunks liên quan từ FAISS
    2. Augment: ghép chunks vào system prompt
    3. Generate: gửi GPT-4o, nhận câu trả lời

    Args:
        user_message: câu hỏi của người dùng
        history: lịch sử hội thoại (multi-turn)
    Returns:
        dict với reply, history mới, và suggestions (sản phẩm gợi ý)
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    # ── Bước 1: RETRIEVE ──────────────────────────────────────
    # Tìm top-5 chunks liên quan nhất với câu hỏi
    chunks = retrieve(user_message, top_k=5)

    # ── Bước 2: AUGMENT ───────────────────────────────────────
    # Ghép chunks thành context string
    context_lines = []
    for i, c in enumerate(chunks, 1):
        prefix = "[SẢN PHẨM]" if c["type"] == "product" else "[BÀI VIẾT]"
        context_lines.append(f"{i}. {prefix} {c['name']}: {c['text']}")
    context = "\n\n".join(context_lines)

    # Ghép vào system prompt
    full_system = (
        SYSTEM_PROMPT
        + "\n\n" + "=" * 50
        + "\nDỮ LIỆU SẢN PHẨM CỬA HÀNG AMI PERFUMERY:\n"
        + "=" * 50 + "\n"
        + context
        + "\n" + "=" * 50
    )

    # ── Bước 3: GENERATE ──────────────────────────────────────
    # Build messages: history + câu hỏi mới
    messages = list(history or [])
    messages.append({"role": "user", "content": user_message})

    # Gọi OpenAI GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        temperature=0.7,     # 0=chính xác, 1=sáng tạo, 0.7=cân bằng
        messages=[
            {"role": "system", "content": full_system}
        ] + messages,
    )

    reply = response.choices[0].message.content

    # Cập nhật history để dùng cho lượt sau (multi-turn)
    messages.append({"role": "assistant", "content": reply})

    # Lấy sản phẩm được tìm thấy để hiển thị card gợi ý
    suggested = [c for c in chunks if c["type"] == "product"][:3]

    return {
        "reply":       reply,
        "history":     messages,
        "suggestions": suggested,
    }