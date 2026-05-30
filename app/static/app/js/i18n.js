/* =============================================================
   Ami Perfumery — i18n.js
   Đa ngôn ngữ VI / EN
   ============================================================= */

const TRANSLATIONS = {
  vi: {
    // Navbar
    nav_home:     'Trang chủ',
    nav_products: 'Nước hoa',
    nav_blog:     'Bài viết',
    nav_contact:  'Liên hệ',
    nav_brands:   'Xem tất cả thương hiệu →',

    // Header
    search_placeholder: 'Tìm kiếm theo tên, thương hiệu, mùi hương...',
    wishlist:     'Yêu thích',
    cart:         'Giỏ hàng',
    account:      'Tài khoản',
    login:        'Đăng nhập',
    register:     'Đăng ký',
    logout:       'Đăng xuất',

    // Sản phẩm
    add_cart:     'Thêm vào giỏ',
    buy_now:      'Mua ngay',
    in_stock:     '● Còn hàng',
    out_stock:    '● Hết hàng',
    view_detail:  'Xem chi tiết',

    // Footer
    footer_desc:  'Ami Perfumery mang đến trải nghiệm mua sắm nước hoa cao cấp chính hãng.',

    // Cart
    cart_empty:   'Giỏ hàng trống',
    cart_total:   'Tổng cộng',
    checkout:     'Thanh toán',

    // Profile
    profile_title:   'Thông tin cá nhân',
    orders_title:    'Đơn hàng',
    wishlist_title:  'Yêu thích',
    vouchers_title:  'Khuyến mãi',
    reviews_title:   'Đánh giá',
    points_title:    'Lịch sử điểm',
    settings_title:  'Cài đặt',
    save_changes:    'Lưu thay đổi',

    // Chatbot
    chat_placeholder: 'Nhập câu hỏi về nước hoa...',
    chat_greeting:    'Xin chào! Tôi là trợ lý tư vấn nước hoa của Ami Perfumery. Bạn đang tìm kiếm hương thơm cho dịp nào? ✨',
  },

  en: {
    nav_home:     'Home',
    nav_products: 'Fragrances',
    nav_blog:     'Journal',
    nav_contact:  'Contact',
    nav_brands:   'View all brands →',

    search_placeholder: 'Search by name, brand, scent...',
    wishlist:     'Wishlist',
    cart:         'Cart',
    account:      'Account',
    login:        'Sign in',
    register:     'Register',
    logout:       'Sign out',

    add_cart:     'Add to cart',
    buy_now:      'Buy now',
    in_stock:     '● In stock',
    out_stock:    '● Out of stock',
    view_detail:  'View detail',

    footer_desc:  'Ami Perfumery brings you an authentic luxury fragrance shopping experience.',

    cart_empty:   'Your cart is empty',
    cart_total:   'Total',
    checkout:     'Checkout',

    profile_title:   'Personal info',
    orders_title:    'Orders',
    wishlist_title:  'Wishlist',
    vouchers_title:  'Promotions',
    reviews_title:   'Reviews',
    points_title:    'Points history',
    settings_title:  'Settings',
    save_changes:    'Save changes',

    chat_placeholder: 'Ask about fragrances...',
    chat_greeting:    'Hello! I\'m Ami Perfumery\'s fragrance consultant. What occasion are you shopping for? ✨',
  }
};

function applyLanguage(lang) {
  const strings = TRANSLATIONS[lang] || TRANSLATIONS['vi'];

  // Thay text theo data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (strings[key]) el.textContent = strings[key];
  });

  // Thay placeholder theo data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (strings[key]) el.placeholder = strings[key];
  });

  // Thay title attribute theo data-i18n-title
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.dataset.i18nTitle;
    if (strings[key]) el.title = strings[key];
  });

  // Lưu vào localStorage
  localStorage.setItem('ami_lang', lang);

  // Cập nhật lang attribute trên <html>
  document.documentElement.lang = lang === 'vi' ? 'vi' : 'en';
}

// Auto-apply khi load trang
document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('ami_lang') || 'vi';
  applyLanguage(saved);
});

// Expose global
window.applyLanguage = applyLanguage;