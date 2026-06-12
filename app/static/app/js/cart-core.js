/* cart-core.js — Load trên mọi trang qua base.html */

const CART_KEY      = 'ami_cart_v2';
const DISCOUNT_KEY  = 'ami_cart_discount';
const SHIP_FEE      = 30000;

let cartDiscount       = 0;
let cartFreeShip       = false;
let cartFirstOrder     = false;
let cartVoucherCode    = null;
let cartPointsDiscount = 0;
let cartPointsUsed     = 0;
let cartPointsApplied  = false;

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
function saveDiscountState() {
  localStorage.setItem(DISCOUNT_KEY, JSON.stringify({
    discount: cartDiscount, freeShip: cartFreeShip,
    firstOrder: cartFirstOrder, voucherCode: cartVoucherCode,
    pointsDiscount: cartPointsDiscount, pointsUsed: cartPointsUsed,
    pointsApplied: cartPointsApplied,
  }));
}
function updateCartBadge() {
  const count = getCart().length;
  document.querySelectorAll('[data-cart-badge]').forEach(b => {
    b.textContent   = String(count);
    b.style.display = count > 0 ? '' : 'none';
  });
}

/* ── Push thay đổi lên server ── */
function pushCartUpdate(variantId, qty, action = 'set') {
  if (!isLoggedIn()) return;
  if (!variantId || !/^\d+$/.test(String(variantId))) return;
  fetch('/api/cart/update/', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
    body:    JSON.stringify({ variantId, qty, action }),
  }).catch(() => {});
}

function addToCart({ variantId, productId, name, price, image, sku = '', qty = 1, stock = null }) {
  const cart     = getCart();
  const key      = `${productId}-${variantId || 'default'}`;
  const idx      = cart.findIndex(i => i.key === key);
  const stockQty = Number(stock || 0);
  const currentQty = idx >= 0 ? (cart[idx].qty || 0) : 0;

  if (stockQty > 0 && currentQty + qty > stockQty) {
    showCartToast('Số lượng tồn kho không đủ, vui lòng giảm bớt số lượng sản phẩm', 0);
    return false;
  }
  if (idx >= 0) {
    cart[idx].qty += qty;
    if (stockQty > 0) cart[idx].stock = stockQty;
  } else {
    cart.push({ key, variantId, productId, name, price, image, sku, qty, stock: stockQty || null, checked: true });
  }
  saveCart(cart);
  showCartToast(name, qty);

  const newQty = idx >= 0 ? cart[idx].qty : qty;
  if (variantId && /^\d+$/.test(String(variantId))) {
    pushCartUpdate(variantId, newQty, 'set');
  }
  return true;
}

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
  el.innerHTML = qty > 0
    ? `<span style="font-size:16px">🛒</span><span>Đã thêm <strong>${qty}</strong> × <em>${name}</em></span>`
    : `<span style="font-size:16px">⚠️</span><span>${name}</span>`;
  document.body.appendChild(el);
  requestAnimationFrame(() => {
    el.style.opacity = '1'; el.style.transform = 'translateX(-50%) translateY(0)';
  });
  setTimeout(() => {
    el.style.opacity = '0'; el.style.transform = 'translateX(-50%) translateY(8px)';
    setTimeout(() => el.remove(), 280);
  }, 2600);
}

(function initCardCartBtns() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.add-cart-btn');
    if (!btn) return;
    if (document.querySelector('[data-cart-app]') && btn.closest('[data-cart-items]')) return;
    e.stopPropagation();
    e.stopImmediatePropagation();
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

(function initDetailCartBtn() {
  if (document.getElementById('pdVariantsData')) return;
  const btn = document.getElementById('pdAddCart');
  if (!btn) return;
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);
  newBtn.addEventListener('click', () => {
    const container = document.querySelector('.pd-layout');
    if (!container) return;
    const productId  = container.dataset.productId || '0';
    const name       = document.querySelector('.pd-name')?.textContent?.trim() || 'Sản phẩm';
    const priceText  = document.getElementById('pdVariantPrice')?.textContent || '0';
    const price      = parseInt(priceText.replace(/\D/g, '')) || 0;
    const image      = document.getElementById('pdMainImg')?.src || '';
    const qtyVal     = parseInt(document.getElementById('pdQtyVal')?.textContent || '1') || 1;
    const activePills = [...document.querySelectorAll('.pd-size-pill.active')];
    const variantParts = activePills.map(p => p.dataset.attrValue).filter(Boolean);
    const sku        = variantParts.join(' / ');
    const selectedVariant = window.__pdSelectedVariant;
    const variantId = selectedVariant?.id
                      ? String(selectedVariant.id)
                      : (variantParts.join('-') || 'default');
    addToCart({ variantId, productId, name: sku ? `${name} — ${sku}` : name, price, image, sku, qty: qtyVal });
    newBtn.classList.remove('bounce'); void newBtn.offsetWidth;
    newBtn.classList.add('bounce'); setTimeout(() => newBtn.classList.remove('bounce'), 450);
  });
})();

document.addEventListener('DOMContentLoaded', updateCartBadge);
if (document.readyState !== 'loading') updateCartBadge();

/* ── Xử lý đăng xuất — xóa localStorage trước khi redirect ── */
function handleLogout(e) {
  e.preventDefault();
  // Xóa giỏ hàng và discount state khỏi localStorage
  localStorage.removeItem('ami_cart_v2');
  localStorage.removeItem('ami_cart_discount');
  // Redirect đến URL logout
  window.location.href = '/logout/';
}