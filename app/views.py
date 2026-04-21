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


def product_detail(request):
    return render(request, 'app/product.html')

BRANDS = [
    {
        'slug': 'dior',
        'name': 'Dior',
        'tagline': 'Haute Parfumerie for modern icons',
        'palette': '#5f6f52',
        'hero_image': 'https://images.unsplash.com/photo-1610461888750-10bfc601b874?auto=format&fit=crop&w=1800&q=80',
        'poster_image': 'https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?auto=format&fit=crop&w=900&q=80',
        'about_image': 'https://images.unsplash.com/photo-1615634260167-c8cdede054de?auto=format&fit=crop&w=1200&q=80',
        'story': 'Tinh thần couture của Dior mở ra thế giới hương thơm sang trọng, cân bằng giữa di sản Pháp và phong cách hiện đại.',
        'philosophy': 'Mỗi mùi hương là một silhouette: sắc nét, thanh lịch và có chiều sâu.',
        'signature_notes': ['Bergamot Calabria', 'Ambroxan', 'Vanilla Absolute'],
    },
    {
        'slug': 'chanel',
        'name': 'Chanel',
        'tagline': 'Timeless elegance with bold character',
        'palette': '#8f9779',
        'hero_image': 'https://images.unsplash.com/photo-1618331835717-801e976710b2?auto=format&fit=crop&w=1800&q=80',
        'poster_image': 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=900&q=80',
        'about_image': 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=1200&q=80',
        'story': 'Chanel kiến tạo những tầng hương kinh điển, tối giản nhưng đầy cá tính.',
        'philosophy': 'Sự cân bằng giữa kỹ nghệ chế tác và vẻ đẹp vượt thời gian.',
        'signature_notes': ['Lemon Zest', 'Incense', 'Sandalwood'],
    },
    {
        'slug': 'tom-ford',
        'name': 'Tom Ford',
        'tagline': 'Noir sensuality, cinematic luxury',
        'palette': '#6a5f4d',
        'hero_image': 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=1800&q=80',
        'poster_image': 'https://images.unsplash.com/photo-1590736704728-f4730bb30770?auto=format&fit=crop&w=900&q=80',
        'about_image': 'https://images.unsplash.com/photo-1590736969955-71cc94901144?auto=format&fit=crop&w=1200&q=80',
        'story': 'Tom Ford Private Blend thể hiện chất noir táo bạo với chữ ký gỗ – gia vị – da thuộc.',
        'philosophy': 'Sự xa xỉ mang chất điện ảnh, mạnh mẽ và gợi cảm.',
        'signature_notes': ['Cardamom', 'Oud Accord', 'Tonka Bean'],
    },
    {
        'slug': 'ysl',
        'name': 'YSL',
        'tagline': 'Sharp lines, magnetic freshness',
        'palette': '#7d8f70',
        'hero_image': 'https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=1800&q=80',
        'poster_image': 'https://images.unsplash.com/photo-1590736969955-71cc94901144?auto=format&fit=crop&w=900&q=80',
        'about_image': 'https://images.unsplash.com/photo-1547887538-e3a2f32cb1cc?auto=format&fit=crop&w=1200&q=80',
        'story': 'YSL mang tinh thần thành thị đương đại: sạch, sắc, và đầy năng lượng.',
        'philosophy': 'Mùi hương dành cho người dám tạo dấu ấn cá nhân.',
        'signature_notes': ['Apple Accord', 'Sage', 'Vetiver'],
    },
    {
        'slug': 'gucci',
        'name': 'Gucci',
        'tagline': 'Eclectic elegance in modern rhythm',
        'palette': '#8a8169',
        'hero_image': 'https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=1800&q=80',
        'poster_image': 'https://images.unsplash.com/photo-1547887538-e3a2f32cb1cc?auto=format&fit=crop&w=900&q=80',
        'about_image': 'https://images.unsplash.com/photo-1587017539504-67cfbddac569?auto=format&fit=crop&w=1200&q=80',
        'story': 'Gucci Fragrances kết hợp tinh thần cổ điển Ý với sự phá cách nghệ thuật.',
        'philosophy': 'Sáng tạo, tự do và luôn có điểm nhấn thời trang.',
        'signature_notes': ['Lavender', 'Orange Blossom', 'Patchouli'],
    },
]

BRAND_PRODUCTS = [
    {'name': 'Sauvage Elixir', 'brand': 'dior', 'price': '4.200.000₫', 'image': 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=700&q=80', 'pinned': True},
    {'name': 'Dior Homme Parfum', 'brand': 'dior', 'price': '4.700.000₫', 'image': 'https://images.unsplash.com/photo-1563170351-be82bc888aa4?auto=format&fit=crop&w=700&q=80', 'pinned': False},
    {'name': 'Bleu de Chanel EDP', 'brand': 'chanel', 'price': '3.800.000₫', 'image': 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=700&q=80', 'pinned': True},
    {'name': 'Égoïste Platinum', 'brand': 'chanel', 'price': '5.100.000₫', 'image': 'https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?auto=format&fit=crop&w=700&q=80', 'pinned': False},
    {'name': 'Oud Wood Parfum', 'brand': 'tom-ford', 'price': '6.900.000₫', 'image': 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=700&q=80', 'pinned': True},
    {'name': 'Noir Extreme', 'brand': 'tom-ford', 'price': '5.800.000₫', 'image': 'https://images.unsplash.com/photo-1590736704728-f4730bb30770?auto=format&fit=crop&w=700&q=80', 'pinned': False},
    {'name': 'Y Eau de Parfum', 'brand': 'ysl', 'price': '3.400.000₫', 'image': 'https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=700&q=80', 'pinned': True},
    {'name': 'Libre Le Parfum', 'brand': 'ysl', 'price': '4.100.000₫', 'image': 'https://images.unsplash.com/photo-1590736969955-71cc94901144?auto=format&fit=crop&w=700&q=80', 'pinned': False},
    {'name': 'Gucci Guilty EDT', 'brand': 'gucci', 'price': '3.200.000₫', 'image': 'https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=700&q=80', 'pinned': True},
    {'name': 'Gucci Bloom', 'brand': 'gucci', 'price': '3.600.000₫', 'image': 'https://images.unsplash.com/photo-1547887538-e3a2f32cb1cc?auto=format&fit=crop&w=700&q=80', 'pinned': False},
]


def brand_list(request):
    return render(request, 'app/brand_list.html', {'brands': BRANDS})


def brand_detail(request, slug):
    brand = next((item for item in BRANDS if item['slug'] == slug), BRANDS[0])
    products = [item for item in BRAND_PRODUCTS if item['brand'] == brand['slug']]
    pinned_products = [item for item in products if item['pinned']]
    return render(request, 'app/brand_detail.html', {
        'brand': brand,
        'products': products,
        'pinned_products': pinned_products,
    })

BLOG_ARTICLES = [
    {
        'slug': 'chon-mui-huong-cho-moi-thoi-tiet',
        'title': 'Chọn mùi hương theo thời tiết Việt Nam',
        'category': 'Guide',
        'audience': 'unisex',
        'author': 'Ami Editorial',
        'published_at': '21/04/2026',
        'cover': 'https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=1600&q=80',
        'excerpt': 'Mẹo chọn EDT, EDP, Parfum cho ngày nắng nóng và đêm se lạnh để hương thơm luôn tinh tế.',
        'body': [
            {'type': 'p', 'text': 'Khí hậu nhiệt đới khiến cách mùi hương thể hiện trên da thay đổi liên tục. Nồng độ phù hợp giúp mùi thơm tự nhiên, không quá gắt.'},
            {'type': 'h3', 'text': 'Buổi sáng: hương tươi sáng và sạch'},
            {'type': 'p', 'text': 'Citrus, tea notes và white musk tạo cảm giác dễ chịu khi bắt đầu ngày mới. Ưu tiên EDT hoặc EDP nhẹ.'},
            {'type': 'quote', 'text': 'Một mùi hương đẹp là mùi hương được người khác cảm nhận khi bạn lướt qua — không phải trước khi bạn bước vào phòng.'},
            {'type': 'h3', 'text': 'Buổi tối: tăng chiều sâu và độ lưu hương'},
            {'type': 'p', 'text': 'Amber, vanilla hay gỗ ấm giúp diện mạo sang trọng hơn cho tiệc tối. Có thể dùng Parfum với 1-2 điểm xịt.'},
        ],
    },
    {
        'slug': 'signature-scent-cho-quy-ong',
        'title': 'Signature scent cho quý ông hiện đại',
        'category': 'For Him',
        'audience': 'men',
        'author': 'Hải Nam',
        'published_at': '18/04/2026',
        'cover': 'https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=1600&q=80',
        'excerpt': 'Cách xây dựng mùi hương đại diện cho phong cách cá nhân trong công việc và đời sống.',
        'body': [
            {'type': 'p', 'text': 'Một signature scent không cần phức tạp, nhưng phải đủ riêng để được ghi nhớ.'},
            {'type': 'h3', 'text': 'Chọn theo bối cảnh sử dụng'},
            {'type': 'p', 'text': 'Đi làm: woody aromatic gọn gàng. Cuối tuần: thêm citrus hoặc spice để linh hoạt hơn.'},
            {'type': 'quote', 'text': 'Mùi hương là ngôn ngữ thầm lặng nhưng có sức ảnh hưởng mạnh nhất.'},
            {'type': 'p', 'text': 'Hãy thử mùi trên da ít nhất 4 giờ trước khi quyết định.'},
        ],
    },
    {
        'slug': 'nuoc-hoa-niche-vi-sao-khac-biet',
        'title': 'Nước hoa niche: Vì sao khác biệt?',
        'category': 'Editorial',
        'audience': 'unisex',
        'author': 'Ami Lab',
        'published_at': '14/04/2026',
        'cover': 'https://images.unsplash.com/photo-1615634260167-c8cdede054de?auto=format&fit=crop&w=1200&q=80',
        'excerpt': 'Đi sâu vào triết lý chế tác niche và lý do người yêu mùi hương ngày càng ưu tiên.',
        'body': [],
    },
    {
        'slug': 'top-note-va-heart-note',
        'title': 'Top note và heart note khác nhau thế nào?',
        'category': 'Guide',
        'audience': 'unisex',
        'author': 'Ami Editorial',
        'published_at': '10/04/2026',
        'cover': 'https://images.unsplash.com/photo-1541643600914-78b084683702?auto=format&fit=crop&w=1200&q=80',
        'excerpt': 'Hiểu cấu trúc mùi hương để chọn perfume phù hợp tính cách.',
        'body': [],
    },
    {
        'slug': 'layering-danh-cho-nu',
        'title': 'Layering tinh tế dành cho nữ',
        'category': 'For Her',
        'audience': 'women',
        'author': 'Ngọc Ánh',
        'published_at': '06/04/2026',
        'cover': 'https://images.unsplash.com/photo-1547887538-e3a2f32cb1cc?auto=format&fit=crop&w=1200&q=80',
        'excerpt': 'Kỹ thuật phối 2 mùi hương để tăng cá tính nhưng vẫn thanh lịch.',
        'body': [],
    },
    {
        'slug': 'lich-su-thuong-hieu-dior-fragrance',
        'title': 'Lịch sử Dior Fragrance qua từng thời kỳ',
        'category': 'Brand Story',
        'audience': 'unisex',
        'author': 'Ami Archive',
        'published_at': '02/04/2026',
        'cover': 'https://images.unsplash.com/photo-1610461888750-10bfc601b874?auto=format&fit=crop&w=1200&q=80',
        'excerpt': 'Từ tinh thần couture đến bộ sưu tập mùi hương biểu tượng.',
        'body': [],
    },
]


def blog_list(request):
    featured_articles = BLOG_ARTICLES[:2]
    bento_articles = BLOG_ARTICLES[2:]
    popular_articles = BLOG_ARTICLES[:5]
    return render(request, 'app/blog.html', {
        'featured_articles': featured_articles,
        'bento_articles': bento_articles,
        'popular_articles': popular_articles,
    })


def article_detail(request, slug):
    article = next((item for item in BLOG_ARTICLES if item['slug'] == slug), BLOG_ARTICLES[0])
    related_articles = [item for item in BLOG_ARTICLES if item['slug'] != article['slug']][:5]

    audience_map = {
        'men': ['Sauvage Elixir', 'Bleu de Chanel EDP', 'Y Eau de Parfum'],
        'women': ['Libre Le Parfum', 'Gucci Bloom', 'Égoïste Platinum'],
        'unisex': ['Oud Wood Parfum', 'Dior Homme Parfum', 'Gucci Guilty EDT'],
    }
    suggested_names = audience_map.get(article['audience'], audience_map['unisex'])
    suggested_products = [item for item in BRAND_PRODUCTS if item['name'] in suggested_names]

    return render(request, 'app/article_detail.html', {
        'article': article,
        'related_articles': related_articles,
        'suggested_products': suggested_products,
    })


def contact_page(request):
    faq_items = [
        {'question': 'Ami có tư vấn chọn mùi theo cá tính không?', 'answer': 'Có. Đội ngũ tư vấn 1:1 theo nhu cầu đi làm, đi tiệc, du lịch và ngân sách của bạn.'},
        {'question': 'Tôi có thể đặt lịch thử mùi riêng?', 'answer': 'Bạn có thể đặt lịch private appointment trong khung giờ 10:00–20:00 hằng ngày.'},
        {'question': 'Ami hỗ trợ giao hàng toàn quốc?', 'answer': 'Có. Đơn hàng được đóng gói chống sốc, hỗ trợ COD và đổi trả theo chính sách.'},
    ]
    reviews = [
        {'name': 'Minh Khang', 'comment': 'Tư vấn cực kỳ có tâm, chọn đúng mùi cho môi trường văn phòng.'},
        {'name': 'Ngọc Ánh', 'comment': 'Không gian boutique sang và dịch vụ hậu mãi rất tốt.'},
        {'name': 'Quốc Đạt', 'comment': 'Đặt lịch nhanh, được hướng dẫn layering rất chuyên nghiệp.'},
    ]
    return render(request, 'app/contact.html', {'faq_items': faq_items, 'reviews': reviews})


def cart_page(request):
    cart_items = [
        {'name': 'Dior Sauvage Elixir', 'price': 4200000, 'quantity': 1, 'image': 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=600&q=80'},
        {'name': 'Bleu de Chanel EDP', 'price': 3800000, 'quantity': 2, 'image': 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=600&q=80'},
    ]
    suggestions = [
        {'name': 'Y Eau de Parfum', 'price': '3.400.000₫', 'image': 'https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=700&q=80'},
        {'name': 'Gucci Guilty EDT', 'price': '3.200.000₫', 'image': 'https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=700&q=80'},
        {'name': 'Dior Homme Parfum', 'price': '4.700.000₫', 'image': 'https://images.unsplash.com/photo-1563170351-be82bc888aa4?auto=format&fit=crop&w=700&q=80'},
        {'name': 'Oud Wood Parfum', 'price': '6.900.000₫', 'image': 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=700&q=80'},
    ]
    return render(request, 'app/cart.html', {'cart_items': cart_items, 'suggestions': suggestions})
