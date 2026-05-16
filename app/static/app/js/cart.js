/* =============================================================
   Ami Perfumery — cart.js v5
   - Voucher + Điểm tích lũy + Freeship đơn đầu tiên
   - Lưu discount state vào localStorage → checkout đọc lại
   ============================================================= */

const CART_KEY      = 'ami_cart_v2';
const DISCOUNT_KEY  = 'ami_cart_discount';   // lưu state giảm giá
const SHIP_FEE      = 30000;

/* ── State giảm giá ── */
let cartDiscount    = 0;
let cartFreeShip    = false;
let cartFirstOrder  = false;
let cartVoucherCode = null;
let cartPointsDiscount = 0;
let cartPointsUsed     = 0;
let cartPointsApplied  = false;

/* ── Helpers ── */
function formatVnd(v) {
  return `${Math.round(v).toLocaleString('vi-VN')}₫`;
}
function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY) || '[]'); }
  catch { return []; }
}
function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}
function getCSRF() {
  return document.cookie.split('; ')
    .find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}
function isLoggedIn() {
  return (document.body.dataset.accountName || '').trim() !== '';
}

/* Lưu discount state để checkout đọc */
function saveDiscountState() {
  localStorage.setItem(DISCOUNT_KEY, JSON.stringify({
    discount:       cartDiscount,
    freeShip:       cartFreeShip,
    firstOrder:     cartFirstOrder,
    voucherCode:    cartVoucherCode,
    pointsDiscount: cartPointsDiscount,
    pointsUsed:     cartPointsUsed,
    pointsApplied:  cartPointsApplied,
  }));
}

/* ── Badge ── */
function updateCartBadge() {
  const count = getCart().length;
  document.querySelectorAll('[data-cart-badge]').forEach(b => {
    b.textContent   = String(count);
    b.style.display = count > 0 ? '' : 'none';
  });
}

/* ── Thêm vào giỏ ── */
function addToCart({ variantId, productId, name, price, image, sku = '', qty = 1 }) {
  const cart = getCart();
  const key  = `${productId}-${variantId || 'default'}`;
  const idx  = cart.findIndex(i => i.key === key);
  if (idx >= 0) cart[idx].qty += qty;
  else cart.push({ key, variantId, productId, name, price, image, sku, qty, checked: true });
  saveCart(cart);
  showCartToast(name, qty);
}

/* ── Toast ── */
function showCartToast(name, qty) {
  const old = document.getElementById('_cartToast');
  if (old) old.remove();
  const el = document.createElement('div');
  el.id = '_cartToast';
  el.style.cssText = `
    position:fixed;bottom:28px;left:50%;
    transform:translateX(-50%) translateY(12px);
    background:#2c3324;color:#EBF6C4;
    padding:12px 24px;border-radius:40px;
    font-family:'Jost',sans-serif;font-size:13px;font-weight:500;
    box-shadow:0 8px 28px rgba(0,0,0,.22);z-index:9999;
    opacity:0;transition:opacity .25s,transform .25s;pointer-events:none;
    display:flex;align-items:center;gap:10px;white-space:nowrap;
  `;
  el.innerHTML = `<span style="font-size:16px">🛒</span>
    <span>Đã thêm <strong>${qty}</strong> × <em>${name}</em></span>`;
  document.body.appendChild(el);
  requestAnimationFrame(() => {
    el.style.opacity = '1'; el.style.transform = 'translateX(-50%) translateY(0)';
  });
  setTimeout(() => {
    el.style.opacity = '0'; el.style.transform = 'translateX(-50%) translateY(8px)';
    setTimeout(() => el.remove(), 280);
  }, 2600);
}

/* ── Thêm từ card ── */
(function initCardCartBtns() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.add-cart-btn');
    if (!btn) return;
    if (document.querySelector('[data-cart-app]') && btn.closest('[data-cart-items]')) return;
    e.stopPropagation();
    const productId = btn.dataset.productId || '0';
    const name      = btn.dataset.productName || btn.closest('article')?.querySelector('h3,h4')?.textContent?.trim() || 'Sản phẩm';
    const price     = parseInt(btn.dataset.productPrice || '0') || 0;
    const image     = btn.dataset.productImage || btn.closest('article')?.querySelector('img')?.src || '';
    if (!productId || productId === '0') return;
    addToCart({ variantId: null, productId, name, price, image, qty: 1 });
    btn.classList.add('added');
    setTimeout(() => btn.classList.remove('added'), 700);
  });
})();

/* ── Thêm từ product detail ── */
(function initDetailCartBtn() {
  const btn = document.getElementById('pdAddCart');
  if (!btn) return;
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);
  newBtn.addEventListener('click', () => {
    const container   = document.querySelector('.pd-layout');
    if (!container) return;
    const productId   = container.dataset.productId || '0';
    const name        = document.querySelector('.pd-name')?.textContent?.trim() || 'Sản phẩm';
    const priceText   = document.getElementById('pdVariantPrice')?.textContent || '0';
    const price       = parseInt(priceText.replace(/\D/g, '')) || 0;
    const image       = document.getElementById('pdMainImg')?.src || '';
    const qtyVal      = parseInt(document.getElementById('pdQtyVal')?.textContent || '1') || 1;
    const activePills = [...document.querySelectorAll('.pd-size-pill.active')];
    const variantParts= activePills.map(p => p.dataset.attrValue).filter(Boolean);
    const variantId   = variantParts.join('-') || 'default';
    const sku         = variantParts.join(' / ');
    addToCart({ variantId, productId, name: sku ? `${name} — ${sku}` : name, price, image, sku, qty: qtyVal });
    newBtn.classList.remove('bounce'); void newBtn.offsetWidth;
    newBtn.classList.add('bounce'); setTimeout(() => newBtn.classList.remove('bounce'), 450);
  });
})();

/* ═══════════════════════════════════════════════════════════
   TRANG GIỎ HÀNG
═══════════════════════════════════════════════════════════ */
(function initCartPage() {
  const wrap  = document.querySelector('[data-cart-items]');
  const empty = document.querySelector('[data-empty-state]');
  if (!wrap || !empty) return;

  const subtotalEl = document.querySelector('[data-subtotal]');
  const discountEl = document.querySelector('[data-discount]');
  const shippingEl = document.querySelector('[data-shipping]');
  const totalEl    = document.querySelector('[data-total]');
  const voucherMsg = document.querySelector('[data-voucher-message]');

  function calcSubtotal() {
    return getCart().filter(i => i.checked !== false)
      .reduce((s, i) => s + (i.price || 0) * (i.qty || 1), 0);
  }

  function updateSummary() {
    const sub  = calcSubtotal();
    const free = cartFreeShip || cartFirstOrder;
    const ship = (sub > 0 && !free) ? SHIP_FEE : 0;
    const disc = cartDiscount + cartPointsDiscount;
    const total = Math.max(0, sub - disc + ship);

    if (subtotalEl) subtotalEl.textContent = formatVnd(sub);
    if (discountEl) discountEl.textContent = disc > 0 ? `-${formatVnd(disc)}` : '-0₫';
    if (shippingEl) {
      shippingEl.innerHTML = (free && sub > 0)
        ? '<span style="color:#4B672D;font-weight:600;">Miễn phí</span>'
        : formatVnd(ship);
    }
    if (totalEl) totalEl.textContent = formatVnd(total);

    saveDiscountState();  // ← luôn lưu sau mỗi thay đổi
  }

  /* ── Freeship đơn đầu tiên ── */
  async function checkFirstOrder() {
    if (!isLoggedIn()) return;
    try {
      const res  = await fetch('/api/check-first-order/');
      const data = await res.json();
      if (data.is_first && data.freeship) {
        cartFirstOrder = true;
        showFreeshipBanner(data.message || '🎁 Đơn hàng đầu tiên — Miễn phí vận chuyển!');
        updateSummary();
      }
    } catch {}
  }

  function showFreeshipBanner(msg) {
    if (document.getElementById('_freeshipBanner')) return;
    const b = document.createElement('div');
    b.id = '_freeshipBanner';
    b.className = 'cart-freeship-banner';
    b.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="1" y="3" width="15" height="13"/>
        <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
        <circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
      </svg>
      <span>${msg}</span>
      <span class="freeship-tag">FREESHIP</span>
    `;
    const summary = document.querySelector('[data-summary]');
    if (summary) summary.insertBefore(b, summary.firstChild);
  }

  /* ── Build item HTML ── */
  function buildItem(item, idx) {
    const art = document.createElement('article');
    art.className = 'cart-item';
    art.dataset.cartIdx = String(idx);
    art.dataset.price   = String(item.price || 0);
    art.innerHTML = `
      <label class="cart-check-wrap">
        <input type="checkbox" class="cart-item-check" ${item.checked !== false ? 'checked' : ''} data-cart-check="${idx}">
        <span class="cart-checkmark"></span>
      </label>
      <div class="cart-img-wrap">
        <img src="${item.image || ''}" alt="${item.name || ''}" loading="lazy">
      </div>
      <div class="cart-item-info">
        <p class="cart-item-name">${item.name || 'Sản phẩm'}</p>
        <p class="cart-item-unit">${formatVnd(item.price || 0)}</p>
      </div>
      <div class="cart-qty">
        <button type="button" class="cart-qty-btn" data-action="minus">−</button>
        <span class="cart-qty-val">${item.qty || 1}</span>
        <button type="button" class="cart-qty-btn" data-action="plus">+</button>
      </div>
      <div class="cart-line-total" data-line-total>${formatVnd((item.price||0)*(item.qty||1))}</div>
      <button type="button" class="cart-remove" data-remove>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
        </svg>
      </button>
    `;
    return art;
  }

  function renderCart() {
    const cart = getCart();
    wrap.innerHTML = '';
    if (!cart.length) { empty.hidden = false; wrap.hidden = true; updateSummary(); return; }
    empty.hidden = true; wrap.hidden = false;

    const allChecked = cart.every(i => i.checked !== false);
    const header = document.createElement('div');
    header.className = 'cart-select-all-row';
    header.innerHTML = `
      <label class="cart-check-wrap">
        <input type="checkbox" id="cartSelectAll" ${allChecked ? 'checked' : ''}>
        <span class="cart-checkmark"></span>
      </label>
      <span class="cart-select-label">Chọn tất cả (${cart.length} sản phẩm)</span>
      <button class="cart-delete-selected" type="button">Xóa đã chọn</button>
    `;
    wrap.appendChild(header);
    cart.forEach((item, idx) => wrap.appendChild(buildItem(item, idx)));
    updateSummary();
  }

  /* ── Events ── */
  wrap.addEventListener('change', (e) => {
    if (e.target.matches('.cart-item-check')) {
      const idx = parseInt(e.target.dataset.cartCheck);
      const cart = getCart();
      if (cart[idx]) { cart[idx].checked = e.target.checked; saveCart(cart); }
      updateSummary();
      const sa = document.getElementById('cartSelectAll');
      if (sa) sa.checked = getCart().every(i => i.checked !== false);
    }
    if (e.target.matches('#cartSelectAll')) {
      const cart = getCart(); cart.forEach(i => i.checked = e.target.checked);
      saveCart(cart); renderCart();
    }
  });

  wrap.addEventListener('click', (e) => {
    if (e.target.closest('.cart-delete-selected')) {
      saveCart(getCart().filter(i => i.checked === false)); renderCart(); return;
    }
    const art = e.target.closest('.cart-item');
    if (!art) return;
    const idx = parseInt(art.dataset.cartIdx ?? '-1');

    if (e.target.matches('[data-action="plus"]')) {
      const cart = getCart();
      if (cart[idx]) { cart[idx].qty = (cart[idx].qty||1)+1; saveCart(cart); }
      art.querySelector('.cart-qty-val').textContent = String(cart[idx]?.qty||1);
      art.querySelector('[data-line-total]').textContent = formatVnd((cart[idx]?.price||0)*(cart[idx]?.qty||1));
      art.classList.add('pulse'); setTimeout(()=>art.classList.remove('pulse'),260);
      updateSummary();
    }
    if (e.target.matches('[data-action="minus"]')) {
      const cart = getCart();
      if (cart[idx]) { cart[idx].qty = Math.max(1,(cart[idx].qty||1)-1); saveCart(cart); }
      art.querySelector('.cart-qty-val').textContent = String(cart[idx]?.qty||1);
      art.querySelector('[data-line-total]').textContent = formatVnd((cart[idx]?.price||0)*(cart[idx]?.qty||1));
      art.classList.add('pulse'); setTimeout(()=>art.classList.remove('pulse'),260);
      updateSummary();
    }
    if (e.target.closest('[data-remove]')) {
      art.style.transition='opacity .3s,transform .3s'; art.style.opacity='0'; art.style.transform='translateX(30px)';
      setTimeout(()=>{ const cart=getCart(); cart.splice(idx,1); saveCart(cart); renderCart(); },320);
    }
  });

  /* ── Voucher ── */
  async function applyVoucher(code) {
    code = (code||'').trim().toUpperCase();
    if (!code) { if(voucherMsg) voucherMsg.textContent='Vui lòng nhập mã.'; return; }
    if (!isLoggedIn()) {
      if(voucherMsg) voucherMsg.innerHTML='Vui lòng <a href="/auth/" style="color:#4B672D;text-decoration:underline;">đăng nhập</a> để dùng ưu đãi.';
      return;
    }
    if(voucherMsg) voucherMsg.textContent='Đang kiểm tra…';
    try {
      const fd = new FormData(); fd.append('code',code); fd.append('subtotal',String(calcSubtotal()));
      const res  = await fetch('/api/apply-voucher/', {method:'POST', headers:{'X-CSRFToken':getCSRF()}, body:fd});
      const data = await res.json();
      if (!data.ok) { if(voucherMsg) voucherMsg.textContent=data.message||'Mã không hợp lệ.'; return; }

      cartFreeShip    = (data.type||'').includes('free');
      cartDiscount    = cartFreeShip ? 0 : Math.max(0, data.discount||0);
      cartVoucherCode = data.code;

      if(voucherMsg) voucherMsg.innerHTML=`<span style="color:#4B672D;font-weight:600;">✓ ${data.message}</span>`;

      /* Hiện voucher tag */
      const tag = document.getElementById('cartVoucherTag');
      const tagText = document.getElementById('cartVoucherTagText');
      if (tag && tagText) {
        tagText.textContent = `${data.code}${cartDiscount>0 ? ' — −'+formatVnd(cartDiscount) : ' — Freeship'}`;
        tag.style.display = 'flex';
      }

      /* Ẩn chip vừa dùng */
      document.querySelectorAll(`.cart-vc-apply[data-voucher-code="${data.code}"]`)
        .forEach(b => b.closest('.cart-voucher-chip')?.remove());

      /* Recalc điểm nếu đang dùng */
      if (cartPointsApplied) await applyPoints(false);
      updateSummary();
    } catch { if(voucherMsg) voucherMsg.textContent='Có lỗi xảy ra.'; }
  }

  document.querySelector('[data-apply-voucher]')?.addEventListener('click', () =>
    applyVoucher(document.querySelector('[data-voucher-input]')?.value||'')
  );
  document.querySelector('[data-voucher-input]')?.addEventListener('keydown', e => {
    if (e.key==='Enter') document.querySelector('[data-apply-voucher]')?.click();
  });
  document.addEventListener('click', e => {
    const btn = e.target.closest('.cart-vc-apply[data-voucher-code]');
    if (!btn) return;
    const input = document.querySelector('[data-voucher-input]');
    if (input) { input.value = btn.dataset.voucherCode; }
    applyVoucher(btn.dataset.voucherCode);
  });

  /* Remove voucher */
  document.getElementById('cartVoucherRemove')?.addEventListener('click', () => {
    cartFreeShip=false; cartDiscount=0; cartVoucherCode=null;
    const tag = document.getElementById('cartVoucherTag');
    if (tag) tag.style.display='none';
    const input = document.querySelector('[data-voucher-input]');
    if (input) input.value='';
    if (voucherMsg) voucherMsg.textContent='';
    if (cartPointsApplied) applyPoints(false).then(updateSummary);
    else updateSummary();
  });

  /* ── Điểm tích lũy ── */
  async function applyPoints(showToast = true) {
    const sub = calcSubtotal() - cartDiscount;
    if (sub <= 0) { cartPointsDiscount=0; cartPointsUsed=0; return; }
    const fd = new FormData(); fd.append('subtotal', String(sub));
    try {
      const res  = await fetch('/api/apply-points/', {method:'POST', headers:{'X-CSRFToken':getCSRF()}, body:fd});
      const data = await res.json();
      if (!data.ok) { cartPointsApplied=false; return; }
      cartPointsDiscount = data.discount    || 0;
      cartPointsUsed     = data.points_used || 0;
      const usedEl = document.getElementById('cartPointUsed');
      const discEl = document.getElementById('cartPointDiscount');
      if (usedEl) usedEl.textContent = `${cartPointsUsed.toLocaleString('vi-VN')} điểm`;
      if (discEl) discEl.textContent = `-${formatVnd(cartPointsDiscount)}`;
    } catch {}
  }

  document.getElementById('cartPointToggle')?.addEventListener('change', async (e) => {
    const detail = document.getElementById('cartPointDetail');
    if (!e.target.checked) {
      cartPointsApplied=false; cartPointsDiscount=0; cartPointsUsed=0;
      if(detail) detail.hidden=true; updateSummary(); return;
    }
    cartPointsApplied = true;
    await applyPoints();
    if(detail) detail.hidden=false;
    updateSummary();
  });

  /* Load điểm */
  async function loadPoints() {
    if (!isLoggedIn()) return;
    try {
      const res  = await fetch('/api/points/');
      const data = await res.json();
      if (data.ok) {
        const balEl = document.getElementById('cartPointBalance');
        if (balEl) balEl.textContent = `${(data.points||0).toLocaleString('vi-VN')} điểm`;
      }
    } catch {}
  }

  /* Checkout button */
  document.querySelector('[data-checkout]')?.addEventListener('click', function() {
    saveDiscountState();  // lưu trước khi sang checkout
    window.location.href = this.dataset.checkoutUrl || '/checkout/';
  });

  /* INIT */
  renderCart();
  checkFirstOrder();
  loadPoints();
})();

/* Badge */
document.addEventListener('DOMContentLoaded', updateCartBadge);
if (document.readyState !== 'loading') updateCartBadge();