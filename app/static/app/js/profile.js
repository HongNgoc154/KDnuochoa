/* =============================================================
   Ami Perfumery — profile.js
   User Profile Dashboard interactions
   ============================================================= */

/* ─── DATA ─── */
const ORDERS = [
  { id: 'AMI-2025-001', date: '12/04/2025', status: 'delivered', product: 'Dior Sauvage Elixir', brand: 'Dior', img: 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=200&q=80', total: '4.200.000₫', qty: 1, progress: 4 },
  { id: 'AMI-2025-008', date: '18/04/2025', status: 'shipped',   product: 'Bleu de Chanel EDP', brand: 'Chanel', img: 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=200&q=80', total: '3.800.000₫', qty: 1, progress: 3 },
  { id: 'AMI-2025-015', date: '20/04/2025', status: 'processing',product: 'Y EDP YSL', brand: 'YSL', img: 'https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=200&q=80', total: '3.400.000₫', qty: 2, progress: 1 },
  { id: 'AMI-2025-020', date: '21/04/2025', status: 'cancelled', product: 'Tom Ford Oud Wood', brand: 'Tom Ford', img: 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=200&q=80', total: '6.900.000₫', qty: 1, progress: 0 },
];
const WISHLIST = [
  { id: 1, name: 'Chanel No.5 EDP', brand: 'Chanel', price: '4.500.000₫', img: 'https://images.unsplash.com/photo-1608528577891-eb055944f2e7?auto=format&fit=crop&w=600&q=80' },
  { id: 2, name: 'Hermès Terre d\'Hermès', brand: 'Hermès', price: '4.100.000₫', img: 'https://images.unsplash.com/photo-1563170351-be82bc888aa4?auto=format&fit=crop&w=600&q=80' },
  { id: 3, name: 'Gucci Guilty EDT', brand: 'Gucci', price: '3.200.000₫', img: 'https://images.unsplash.com/photo-1547887538-e3a2f32cb1cc?auto=format&fit=crop&w=600&q=80' },
  { id: 4, name: 'Versace Dylan Blue', brand: 'Versace', price: '2.600.000₫', img: 'https://images.unsplash.com/photo-1587017539504-67cfbddac569?auto=format&fit=crop&w=600&q=80' },
  { id: 5, name: 'Lancôme La Vie est Belle', brand: 'Lancôme', price: '3.700.000₫', img: 'https://images.unsplash.com/photo-1541643600914-78b084683702?auto=format&fit=crop&w=600&q=80' },
  { id: 6, name: 'Dior Miss Dior', brand: 'Dior', price: '3.600.000₫', img: 'https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?auto=format&fit=crop&w=600&q=80' },
];
const VOUCHERS = [
  { code: 'WELCOME20', value: 'Giảm 20% toàn bộ đơn hàng', expiry: '30/06/2025', expiring: false },
  { code: 'VIP50K',    value: 'Giảm 50.000₫ đơn từ 500K', expiry: '15/05/2025', expiring: true },
  { code: 'FREESHIP',  value: 'Miễn phí vận chuyển', expiry: '31/12/2025', expiring: false },
  { code: 'SUMMER15',  value: 'Giảm 15% nước hoa nam', expiry: '01/05/2025', expiring: true },
];
const REVIEWS = [
  { id: 1, product: 'Dior Sauvage Elixir', brand: 'Dior', img: 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=200&q=80', stars: 5, text: 'Mùi này thực sự đẳng cấp, lưu hương suốt 10 giờ mà vẫn dịu. Đi event tối được khen cả đêm. Mua từ Ami rất yên tâm về nguồn gốc.' },
  { id: 2, product: 'Bleu de Chanel EDP', brand: 'Chanel', img: 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=200&q=80', stars: 5, text: 'Được tư vấn rất kỹ theo phong cách cá nhân. Bleu de Chanel rất tươi mát và thanh lịch, phù hợp cả đi làm lẫn đi chơi.' },
  { id: 3, product: 'YSL Y EDP', brand: 'YSL', img: 'https://images.unsplash.com/photo-1588405748880-12d1d2a59a75?auto=format&fit=crop&w=200&q=80', stars: 4, text: 'Mùi khá ổn, woody và citrus cân bằng tốt. Tuy nhiên sillage hơi yếu hơn mong đợi. Nhìn chung vẫn worth it ở mức giá này.' },
];

/* i18n strings */
const I18N = {
  vi: { profile_title: 'Thông tin cá nhân', orders_title: 'Đơn hàng', wishlist_title: 'Yêu thích', settings_title: 'Cài đặt', save: 'Lưu thay đổi', notif_order: 'Thông báo đơn hàng', notif_promo: 'Tin tức & Khuyến mãi', notif_sms: 'Nhắn tin SMS', notif_wishlist: 'Wishlist có sale' },
  en: { profile_title: 'Personal Info', orders_title: 'Orders', wishlist_title: 'Wishlist', settings_title: 'Settings', save: 'Save changes', notif_order: 'Order notifications', notif_promo: 'News & Promotions', notif_sms: 'SMS messages', notif_wishlist: 'Wishlist sale alerts' },
  ja: { profile_title: 'プロフィール', orders_title: '注文', wishlist_title: 'お気に入り', settings_title: '設定', save: '変更を保存', notif_order: '注文通知', notif_promo: 'ニュース & プロモーション', notif_sms: 'SMSメッセージ', notif_wishlist: 'ウィッシュリストセール' },
};

/* ─── TABS ─── */
(function initTabs() {
  const navItems = document.querySelectorAll('.nav-item[data-tab]');
  const panels   = document.querySelectorAll('.tab-panel');

  navItems.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;

      navItems.forEach(b => b.classList.toggle('active', b === btn));
      panels.forEach(p => {
        const match = p.id === `tab-${target}`;
        p.hidden = !match;
        if (match) {
          p.classList.remove('fade-in');
          void p.offsetWidth;
          p.classList.add('fade-in');
        }
      });
    });
  });
})();

/* ─── AVATAR UPLOAD ─── */
(function initAvatar() {
  const wrap  = document.getElementById('avatarWrap');
  const input = document.getElementById('avatarInput');
  const img   = document.getElementById('avatarImg');
  if (!wrap || !input || !img) return;

  wrap.addEventListener('click', () => input.click());
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    img.src = url;
    showToast('Ảnh đại diện đã được cập nhật ✓');
  });
})();

/* ─── RENDER ORDERS ─── */
(function renderOrders() {
  const container = document.getElementById('ordersList');
  if (!container) return;

  const statusLabel = { delivered: 'Đã giao', shipped: 'Đang giao', processing: 'Đang xử lý', cancelled: 'Đã hủy' };
  const statusClass = { delivered: 'status-delivered', shipped: 'status-shipped', processing: 'status-processing', cancelled: 'status-cancelled' };
  const steps = ['Đặt hàng','Xác nhận','Đang giao','Đã giao'];

  ORDERS.forEach(order => {
    const card = document.createElement('div');
    card.className = 'order-card';

    const progressHTML = order.status !== 'cancelled' ? `
      <div class="order-progress">
        ${steps.map((s, i) => `
          <div class="progress-step ${i < order.progress ? 'done' : i === order.progress - 1 ? 'active' : ''}">
            <div class="step-dot">${i < order.progress ? '✓' : i + 1}</div>
            <span class="step-label">${s}</span>
          </div>
        `).join('')}
      </div>` : '';

    card.innerHTML = `
      ${progressHTML}
      <div class="order-header">
        <span class="order-id">${order.id}</span>
        <span class="order-date">${order.date}</span>
        <span class="order-status ${statusClass[order.status]}">${statusLabel[order.status]}</span>
      </div>
      <div class="order-body">
        <img class="order-product-img" src="${order.img}" alt="${order.product}">
        <div class="order-product-info">
          <p class="order-product-brand">${order.brand}</p>
          <h3 class="order-product-name">${order.product}</h3>
        </div>
        <div class="order-total">${order.total}</div>
      </div>
      <div class="order-footer">
        <button class="btn-order btn-order-detail" data-order-id="${order.id}">Xem chi tiết</button>
        ${order.status === 'processing' ? `<button class="btn-order btn-order-cancel" data-order-id="${order.id}">Hủy đơn</button>` : ''}
      </div>
    `;
    container.appendChild(card);
  });

  /* Detail modal */
  container.addEventListener('click', e => {
    const detailBtn = e.target.closest('.btn-order-detail');
    const cancelBtn = e.target.closest('.btn-order-cancel');

    if (detailBtn) openOrderModal(detailBtn.dataset.orderId);
    if (cancelBtn) openCancelModal(cancelBtn.dataset.orderId);
  });
})();

function openOrderModal(orderId) {
  const order = ORDERS.find(o => o.id === orderId);
  if (!order) return;
  const modal   = document.getElementById('orderModal');
  const content = document.getElementById('orderModalContent');
  if (!modal || !content) return;

  content.innerHTML = `
    <h3 class="modal-title">Đơn hàng ${order.id}</h3>
    <p class="od-section-title">Sản phẩm</p>
    <div class="order-detail-items">
      <div class="od-item">
        <img class="od-item-img" src="${order.img}" alt="${order.product}">
        <span class="od-item-name">${order.product}</span>
        <span class="od-item-price">${order.total}</span>
      </div>
    </div>
    <div class="od-totals">
      <div class="od-row"><span>Tạm tính</span><span>${order.total}</span></div>
      <div class="od-row"><span>Phí vận chuyển</span><span>Miễn phí</span></div>
      <div class="od-row total"><span>Tổng cộng</span><span>${order.total}</span></div>
    </div>
    <p class="od-section-title">Cập nhật thông tin giao hàng</p>
    <div class="form-grid" style="grid-template-columns:1fr;">
      <div class="field-group">
        <label class="field-label">Địa chỉ giao hàng</label>
        <input class="field-input" type="text" value="123 Đường 30/4, Cần Thơ" placeholder="Địa chỉ">
      </div>
      <div class="field-group">
        <label class="field-label">Số điện thoại</label>
        <input class="field-input" type="tel" value="0901 234 567" placeholder="SĐT">
      </div>
    </div>
    <div class="modal-actions" style="margin-top:20px;">
      <button class="btn-save" onclick="showToast('Đã cập nhật thông tin giao hàng ✓'); document.getElementById('orderModal').hidden=true;">
        <span class="btn-text">Cập nhật</span><span class="btn-spinner"></span>
      </button>
    </div>
  `;
  modal.hidden = false;
}

function openCancelModal(orderId) {
  const modal = document.getElementById('cancelModal');
  if (!modal) return;
  modal.dataset.orderId = orderId;
  modal.hidden = false;
}

document.getElementById('orderModalClose')?.addEventListener('click', () => {
  document.getElementById('orderModal').hidden = true;
});
document.getElementById('cancelModalClose')?.addEventListener('click', () => {
  document.getElementById('cancelModal').hidden = true;
});
document.getElementById('confirmCancel')?.addEventListener('click', () => {
  document.getElementById('cancelModal').hidden = true;
  showToast('Đơn hàng đã được hủy thành công.');
});

/* ─── RENDER WISHLIST ─── */
(function renderWishlist() {
  const grid = document.getElementById('wishlistGrid');
  if (!grid) return;

  WISHLIST.forEach(item => {
    const card = document.createElement('div');
    card.className = 'wish-card';
    card.dataset.id = item.id;
    card.innerHTML = `
      <div class="wish-media">
        <img src="${item.img}" alt="${item.name}" loading="lazy">
        <div class="wish-actions">
          <button class="wish-action-btn" title="Xem chi tiết">🔍</button>
          <button class="wish-action-btn" title="Thêm vào giỏ">🛒</button>
        </div>
        <button class="wish-remove" title="Bỏ yêu thích">♥</button>
      </div>
      <div class="wish-body">
        <p class="wish-brand">${item.brand}</p>
        <h3 class="wish-name">${item.name}</h3>
        <p class="wish-price">${item.price}</p>
      </div>
    `;
    card.querySelector('.wish-remove').addEventListener('click', () => {
      card.classList.add('removing');
      card.addEventListener('animationend', () => card.remove(), { once: true });
      showToast('Đã xóa khỏi danh sách yêu thích.');
    });
    grid.appendChild(card);
  });
})();

/* ─── RENDER VOUCHERS ─── */
(function renderVouchers() {
  const list = document.getElementById('vouchersList');
  if (!list) return;

  VOUCHERS.forEach(v => {
    const card = document.createElement('div');
    card.className = `voucher-card ${v.expiring ? 'expiring' : ''}`;
    card.innerHTML = `
      <div class="voucher-left">
        <div class="voucher-code">${v.code}</div>
        <div class="voucher-value">${v.value}</div>
      </div>
      <div class="voucher-notch"><span></span><span></span><span></span></div>
      <div class="voucher-right">
        <span class="voucher-expiry">${v.expiring ? '⚠ ' : ''}HSD: ${v.expiry}</span>
        <button class="btn-copy" data-code="${v.code}" data-tip="Đã sao chép!">Sao chép</button>
      </div>
    `;
    list.appendChild(card);
  });

  list.addEventListener('click', e => {
    const btn = e.target.closest('.btn-copy');
    if (!btn) return;
    navigator.clipboard?.writeText(btn.dataset.code).catch(() => {});
    btn.classList.add('copied');
    setTimeout(() => btn.classList.remove('copied'), 1800);
    showToast(`Đã sao chép mã ${btn.dataset.code} ✓`);
  });
})();

/* ─── RENDER REVIEWS ─── */
let editingReviewId = null;
(function renderReviews() {
  const list = document.getElementById('reviewsList');
  if (!list) return;

  const render = () => {
    list.innerHTML = '';
    REVIEWS.forEach(r => {
      const card = document.createElement('div');
      card.className = 'review-card';
      card.dataset.id = r.id;
      card.innerHTML = `
        <div class="review-card-head">
          <img class="review-product-img" src="${r.img}" alt="${r.product}">
          <div>
            <h3 class="review-product-name">${r.product}</h3>
            <p class="review-product-brand">${r.brand}</p>
          </div>
        </div>
        <div class="review-stars-display">
          ${'★'.repeat(r.stars)}${'☆'.repeat(5 - r.stars)}
        </div>
        <p class="review-text-display">${r.text}</p>
        <div class="review-actions">
          <button class="btn-review-edit" data-id="${r.id}">Chỉnh sửa</button>
          <button class="btn-review-delete" data-id="${r.id}">Xóa</button>
        </div>
      `;
      list.appendChild(card);
    });
  };

  render();

  list.addEventListener('click', e => {
    const editBtn   = e.target.closest('.btn-review-edit');
    const deleteBtn = e.target.closest('.btn-review-delete');

    if (editBtn) {
      const id = Number(editBtn.dataset.id);
      const review = REVIEWS.find(r => r.id === id);
      if (!review) return;
      editingReviewId = id;
      document.getElementById('reviewEditText').value = review.text;
      renderStarEditor(review.stars);
      document.getElementById('reviewModal').hidden = false;
    }
    if (deleteBtn) {
      const id = Number(deleteBtn.dataset.id);
      const idx = REVIEWS.findIndex(r => r.id === id);
      if (idx >= 0) REVIEWS.splice(idx, 1);
      render();
      showToast('Đã xóa đánh giá.');
    }
  });
})();

function renderStarEditor(selected = 5) {
  const editor = document.getElementById('starEditor');
  if (!editor) return;
  editor.innerHTML = '';
  let currentRating = selected;
  for (let i = 1; i <= 5; i++) {
    const star = document.createElement('span');
    star.className = `star-editor-star ${i <= currentRating ? 'lit' : ''}`;
    star.textContent = '★';
    star.dataset.val = i;
    star.addEventListener('click', () => {
      currentRating = i;
      renderStarEditor(currentRating);
      editor.dataset.rating = currentRating;
    });
    editor.appendChild(star);
  }
  editor.dataset.rating = currentRating;
}

document.getElementById('reviewModalClose')?.addEventListener('click',  () => { document.getElementById('reviewModal').hidden = true; });
document.getElementById('reviewModalClose2')?.addEventListener('click', () => { document.getElementById('reviewModal').hidden = true; });
document.getElementById('saveReview')?.addEventListener('click', async () => {
  const btn    = document.getElementById('saveReview');
  const text   = document.getElementById('reviewEditText')?.value?.trim();
  const rating = Number(document.getElementById('starEditor')?.dataset.rating || 5);

  if (!text) return;
  btn.classList.add('loading'); btn.disabled = true;
  await delay(1000);
  btn.classList.remove('loading'); btn.disabled = false;

  const review = REVIEWS.find(r => r.id === editingReviewId);
  if (review) { review.text = text; review.stars = rating; }

  document.getElementById('reviewModal').hidden = true;
  /* Re-render */
  const list = document.getElementById('reviewsList');
  if (list) list.innerHTML = '';
  document.querySelector('[data-tab="reviews"]')?.click();
  showToast('Đánh giá đã được cập nhật ✓');
});

/* ─── PROFILE FORM ─── */
document.getElementById('profileForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const btn = document.getElementById('profileSaveBtn');
  btn.classList.add('loading'); btn.disabled = true;
  await delay(1200);
  btn.classList.remove('loading');
  btn.classList.add('success');
  btn.querySelector('.btn-text').textContent = '✓ Đã lưu';
  setTimeout(() => { btn.classList.remove('success'); btn.querySelector('.btn-text').textContent = 'Lưu thay đổi'; btn.disabled = false; }, 2200);
  showToast('Thông tin cá nhân đã được cập nhật ✓');
});

/* ─── PASSWORD FORM ─── */
document.getElementById('passwordForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const pw1 = document.getElementById('pNewPass')?.value;
  const pw2 = document.getElementById('pConfirmPass')?.value;
  const btn = document.getElementById('passwordSaveBtn');
  if (pw1 !== pw2) { showToast('Mật khẩu không khớp. Vui lòng kiểm tra lại.'); return; }
  btn.classList.add('loading'); btn.disabled = true;
  await delay(1400);
  btn.classList.remove('loading');
  btn.querySelector('.btn-text').textContent = '✓ Đã cập nhật';
  setTimeout(() => { btn.querySelector('.btn-text').textContent = 'Cập nhật mật khẩu'; btn.disabled = false; }, 2200);
  showToast('Mật khẩu đã được thay đổi thành công ✓');
});

/* ─── PASSWORD STRENGTH ─── */
document.getElementById('pNewPass')?.addEventListener('input', function() {
  const pw = this.value;
  const bar = document.getElementById('pwStrengthBar');
  const lbl = document.getElementById('pwStrengthLabel');
  if (!bar || !lbl) return;
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/[0-9]/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  const levels = [
    { w: '0%',   c: 'transparent', t: '' },
    { w: '25%',  c: '#c0392b', t: 'Yếu' },
    { w: '50%',  c: '#e67e22', t: 'Trung bình' },
    { w: '75%',  c: '#c9a96e', t: 'Tốt' },
    { w: '100%', c: '#4a7c4e', t: 'Mạnh' },
  ];
  const l = levels[Math.min(s, 4)];
  bar.style.width = l.w; bar.style.background = l.c;
  lbl.textContent = l.t; lbl.style.color = l.c;
});

/* ─── EYE TOGGLE ─── */
document.querySelectorAll('.eye-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = document.getElementById(btn.dataset.target);
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.textContent = input.type === 'password' ? '👁' : '🙈';
  });
});

/* ─── SETTINGS: LANGUAGE ─── */
document.getElementById('langOptions')?.addEventListener('click', e => {
  const opt = e.target.closest('.lang-opt');
  if (!opt) return;
  const lang = opt.dataset.lang;
  document.querySelectorAll('.lang-opt').forEach(o => o.classList.toggle('active', o === opt));
  applyI18n(lang);
  localStorage.setItem('ami_lang', lang);
  showToast(`Ngôn ngữ đã được thay đổi ✓`);
});

function applyI18n(lang) {
  const strings = I18N[lang] || I18N.vi;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (strings[key]) el.textContent = strings[key];
  });
}

/* ─── SETTINGS: THEME ─── */
document.querySelectorAll('[data-theme-opt]').forEach(opt => {
  opt.addEventListener('click', () => {
    const theme = opt.dataset.themeOpt;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ami_theme', theme);
    showToast(`Đã chuyển sang giao diện ${theme === 'dark' ? 'tối 🌙' : 'sáng ☀️'}`);
  });
});

/* Load saved theme */
const savedTheme = localStorage.getItem('ami_theme');
if (savedTheme) {
  document.documentElement.setAttribute('data-theme', savedTheme);
  const radio = document.querySelector(`[data-theme-opt="${savedTheme}"] input`);
  if (radio) radio.checked = true;
}

/* ─── TOAST ─── */
let toastTimer = null;
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3200);
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }