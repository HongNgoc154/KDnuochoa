/* =============================================================
   Ami Perfumery — cart.js v3
   - Badge = số loại sản phẩm (không phải tổng qty)
   - Checkbox chọn từng sản phẩm
   - UI qty control đẹp hơn
   ============================================================= */

const CART_KEY = 'ami_cart_v2';

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

/* Badge = số loại sản phẩm khác nhau trong giỏ */
function updateCartBadge() {
  const cart  = getCart();
  const count = cart.length; // số dòng = số loại sản phẩm
  document.querySelectorAll('[data-cart-badge]').forEach(b => {
    b.textContent   = String(count);
    b.style.display = count > 0 ? '' : 'none';
  });
}

/* Thêm vào giỏ */
function addToCart({ variantId, productId, name, price, image, sku = '', qty = 1 }) {
  const cart = getCart();
  const key  = `${productId}-${variantId || 'default'}`;
  const idx  = cart.findIndex(i => i.key === key);
  if (idx >= 0) cart[idx].qty += qty;
  else cart.push({ key, variantId, productId, name, price, image, sku, qty, checked: true });
  saveCart(cart);
  showCartToast(name, qty);
}

/* Toast */
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
    el.style.opacity = '1';
    el.style.transform = 'translateX(-50%) translateY(0)';
  });
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(-50%) translateY(8px)';
    setTimeout(() => el.remove(), 280);
  }, 2600);
}

/* ── Thêm từ card (document-level) ── */
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
    const container = document.querySelector('.pd-layout');
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
    newBtn.classList.remove('bounce');
    void newBtn.offsetWidth;
    newBtn.classList.add('bounce');
    setTimeout(() => newBtn.classList.remove('bounce'), 450);
  });
})();

/* ══════════════════════════════════════════════════════════
   TRANG GIỎ HÀNG
══════════════════════════════════════════════════════════ */
(function initCartPage() {
  const wrap  = document.querySelector('[data-cart-items]');
  const empty = document.querySelector('[data-empty-state]');
  if (!wrap || !empty) return;

  const subtotalEl = document.querySelector('[data-subtotal]');
  const discountEl = document.querySelector('[data-discount]');
  const shippingEl = document.querySelector('[data-shipping]');
  const totalEl    = document.querySelector('[data-total]');
  let discount = 0;

  /* Tính tổng chỉ các item được check */
  function updateSummary() {
    const cart = getCart();
    const subtotal = cart
      .filter(i => i.checked !== false)
      .reduce((s, i) => s + (i.price || 0) * (i.qty || 1), 0);
    const shipping = subtotal > 0 ? 30000 : 0;
    if (subtotalEl) subtotalEl.textContent = formatVnd(subtotal);
    if (discountEl) discountEl.textContent = `-${formatVnd(discount)}`;
    if (shippingEl) shippingEl.textContent = formatVnd(shipping);
    if (totalEl)    totalEl.textContent    = formatVnd(Math.max(0, subtotal - discount + shipping));
  }

  /* Render 1 cart item */
  function buildItem(item, idx) {
    const checked = item.checked !== false;
    const art = document.createElement('article');
    art.className = 'cart-item';
    art.dataset.cartIdx = String(idx);
    art.dataset.price   = String(item.price || 0);
    art.innerHTML = `
      <!-- Checkbox -->
      <label class="cart-check-wrap" title="Chọn sản phẩm">
        <input type="checkbox" class="cart-item-check" ${checked ? 'checked' : ''}
               data-cart-check="${idx}">
        <span class="cart-checkmark"></span>
      </label>

      <!-- Ảnh -->
      <div class="cart-img-wrap">
        <img src="${item.image || ''}" alt="${item.name || ''}" loading="lazy">
      </div>

      <!-- Info -->
      <div class="cart-item-info">
        <p class="cart-item-name">${item.name || 'Sản phẩm'}</p>
        <p class="cart-item-unit">${formatVnd(item.price || 0)}</p>
      </div>

      <!-- Qty control -->
      <div class="cart-qty">
        <button type="button" class="cart-qty-btn" data-action="minus" aria-label="Giảm">−</button>
        <span class="cart-qty-val">${item.qty || 1}</span>
        <button type="button" class="cart-qty-btn" data-action="plus" aria-label="Tăng">+</button>
      </div>

      <!-- Line total -->
      <div class="cart-line-total" data-line-total>
        ${formatVnd((item.price || 0) * (item.qty || 1))}
      </div>

      <!-- Remove -->
      <button type="button" class="cart-remove" data-remove title="Xóa">
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

    if (cart.length === 0) {
      empty.hidden = false; wrap.hidden = true;
      updateSummary(); return;
    }
    empty.hidden = true; wrap.hidden = false;

    /* Select-all header */
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

  /* Events */
  wrap.addEventListener('change', (e) => {
    /* Checkbox từng item */
    if (e.target.matches('.cart-item-check')) {
      const idx  = parseInt(e.target.dataset.cartCheck);
      const cart = getCart();
      if (cart[idx]) { cart[idx].checked = e.target.checked; saveCart(cart); }
      updateSummary();
      // Cập nhật select-all
      const all = getCart().every(i => i.checked !== false);
      const sa  = document.getElementById('cartSelectAll');
      if (sa) sa.checked = all;
    }
    /* Select all */
    if (e.target.matches('#cartSelectAll')) {
      const cart = getCart();
      cart.forEach(i => i.checked = e.target.checked);
      saveCart(cart); renderCart();
    }
  });

  wrap.addEventListener('click', (e) => {
    /* Delete selected */
    if (e.target.closest('.cart-delete-selected')) {
      const cart = getCart().filter(i => i.checked === false);
      saveCart(cart); renderCart(); return;
    }

    const art = e.target.closest('.cart-item');
    if (!art) return;
    const idx = parseInt(art.dataset.cartIdx ?? '-1');

    if (e.target.matches('[data-action="plus"]')) {
      const cart = getCart();
      if (cart[idx]) { cart[idx].qty = (cart[idx].qty || 1) + 1; saveCart(cart); }
      const valEl = art.querySelector('.cart-qty-val');
      if (valEl) valEl.textContent = String(cart[idx]?.qty || 1);
      const lt = art.querySelector('[data-line-total]');
      if (lt) lt.textContent = formatVnd((cart[idx]?.price || 0) * (cart[idx]?.qty || 1));
      art.classList.add('pulse'); setTimeout(() => art.classList.remove('pulse'), 260);
      updateSummary();
    }
    if (e.target.matches('[data-action="minus"]')) {
      const cart = getCart();
      if (cart[idx]) {
        cart[idx].qty = Math.max(1, (cart[idx].qty || 1) - 1);
        saveCart(cart);
      }
      const valEl = art.querySelector('.cart-qty-val');
      if (valEl) valEl.textContent = String(cart[idx]?.qty || 1);
      const lt = art.querySelector('[data-line-total]');
      if (lt) lt.textContent = formatVnd((cart[idx]?.price || 0) * (cart[idx]?.qty || 1));
      art.classList.add('pulse'); setTimeout(() => art.classList.remove('pulse'), 260);
      updateSummary();
    }
    if (e.target.closest('[data-remove]')) {
      art.style.transition = 'opacity .3s, transform .3s';
      art.style.opacity = '0'; art.style.transform = 'translateX(30px)';
      setTimeout(() => {
        const cart = getCart(); cart.splice(idx, 1); saveCart(cart); renderCart();
      }, 320);
    }
  });

  /* Voucher */
  document.querySelector('[data-apply-voucher]')?.addEventListener('click', () => {
    const code = document.querySelector('[data-voucher-input]')?.value.trim().toUpperCase();
    const msg  = document.querySelector('[data-voucher-message]');
    discount = code === 'AMI10' ? 300000 : 0;
    if (msg) msg.textContent = code === 'AMI10' ? '🎉 Giảm 300.000₫ thành công' : 'Mã không hợp lệ.';
    updateSummary();
  });

  document.querySelector('[data-checkout]')?.addEventListener('click', function () {
    window.location.href = this.dataset.checkoutUrl || '/checkout/';
  });

  renderCart();
})();

/* Badge khi load */
document.addEventListener('DOMContentLoaded', updateCartBadge);
if (document.readyState !== 'loading') updateCartBadge();