import os
from app.ai.knowledge_base import retrieve

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
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

    # ── Bước 1: RETRIEVE ──────────────────────────────────
    chunks = retrieve(user_message, top_k=5)

    # ── Bước 2: AUGMENT ───────────────────────────────────
    context_lines = []
    for i, c in enumerate(chunks, 1):
        prefix = "[SẢN PHẨM]" if c["type"] == "product" else "[BÀI VIẾT]"
        context_lines.append(f"{i}. {prefix} {c['name']}: {c['text']}")
    context = "\n\n".join(context_lines)

    full_system = (
        SYSTEM_PROMPT
        + "\n\n" + "=" * 50
        + "\nDỮ LIỆU SẢN PHẨM CỬA HÀNG AMI PERFUMERY:\n"
        + "=" * 50 + "\n"
        + context
        + "\n" + "=" * 50
    )

    # ── Bước 3: GENERATE ──────────────────────────────────
    messages = list(history or [])
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        temperature=0.7,
        messages=[
            {"role": "system", "content": full_system}
        ] + messages,
    )

    reply = response.choices[0].message.content

    # Cập nhật history cho multi-turn
    messages.append({"role": "assistant", "content": reply})

    suggested = [c for c in chunks if c["type"] == "product"][:3]

    return {
        "reply":       reply,
        "history":     messages,
        "suggestions": suggested,
    }