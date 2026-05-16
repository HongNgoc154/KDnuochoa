/* =============================================================
   Ami Perfumery — checkout.js v4 (fixed)
   ============================================================= */

const CART_KEY     = 'ami_cart_v2';
const DISCOUNT_KEY = 'ami_cart_discount';
const SHIP_FEE     = 30000;

/* ── Đọc state từ localStorage ── */
function getCartItems() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)||'[]').filter(i=>i.checked!==false); }
  catch { return []; }
}
function getDiscountState() {
  try { return JSON.parse(localStorage.getItem(DISCOUNT_KEY)||'{}'); }
  catch { return {}; }
}

const ds             = getDiscountState();
const discount       = ds.discount       || 0;
const isFreeShip     = ds.freeShip       || false;
const isFirstOrder   = ds.firstOrder     || false;
const voucherCode    = ds.voucherCode    || null;
const pointsDiscount = ds.pointsDiscount || 0;
const pointsUsed     = ds.pointsUsed     || 0;
const pointsAppliedFlag = ds.pointsApplied || false;

const fmt = n => Math.round(n).toLocaleString('vi-VN') + '₫';

function getCSRF() {
  return document.cookie.split('; ')
    .find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

/* ── Tính tổng ── */
function calcSubtotal() {
  return getCartItems().reduce((s, i) => s + (i.price||0) * (i.qty||1), 0);
}

/* ── Toast ── */
function toast(msg, ok=true) {
  const old = document.getElementById('_coToast');
  if (old) old.remove();
  const el = document.createElement('div');
  el.id = '_coToast';
  el.style.cssText = `
    position:fixed;top:24px;right:24px;z-index:9999;
    padding:14px 20px;border-radius:14px;
    background:${ok ? 'rgba(44,51,36,.95)' : 'rgba(140,45,30,.95)'};
    color:#fff;font-family:'Jost',sans-serif;font-size:13px;font-weight:500;
    box-shadow:0 12px 36px rgba(0,0,0,.2);backdrop-filter:blur(6px);
    display:flex;align-items:center;gap:10px;
    opacity:0;transform:translateY(-8px);transition:opacity .25s,transform .25s;
  `;
  el.innerHTML = `<span style="font-size:16px">${ok ? '✨' : '⚠️'}</span><span>${msg}</span>`;
  document.body.appendChild(el);
  requestAnimationFrame(() => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-8px)';
    setTimeout(() => el.remove(), 280);
  }, 3200);
}

/* ── Render sản phẩm ── */
function renderCartItems() {
  const box = document.getElementById('coItems');
  if (!box) return;
  const items = getCartItems();
  box.innerHTML = '';
  if (!items.length) {
    box.innerHTML = `<div style="text-align:center;padding:20px;color:#9e9e8e;font-size:13px;">
      Giỏ hàng trống — <a href="/gio-hang/" style="color:#4B672D;">Quay lại giỏ hàng</a></div>`;
    return;
  }
  items.forEach(item => {
    const el = document.createElement('div');
    el.className = 'co-item';
    el.innerHTML = `
      <div class="co-item-img-wrap">
        <img class="co-item-img" src="${item.image||''}" alt="${item.name||''}">
        <span class="co-item-qty">${item.qty||1}</span>
      </div>
      <div style="flex:1;min-width:0;">
        <p class="co-item-name">${item.name||'Sản phẩm'}</p>
      </div>
      <span class="co-item-price">${fmt((item.price||0)*(item.qty||1))}</span>`;
    box.appendChild(el);
  });
}

/* ── Render tóm tắt tổng tiền ── */
function renderTotals() {
  const sub   = calcSubtotal();
  const free  = isFreeShip || isFirstOrder;
  const ship  = free ? 0 : (sub > 0 ? SHIP_FEE : 0);
  const disc  = discount + pointsDiscount;
  const total = Math.max(0, sub - disc + ship);
  const box   = document.getElementById('coTotals');
  if (!box) return;

  box.innerHTML = `
    <div class="co-total-row"><span>Tạm tính</span><span>${fmt(sub)}</span></div>
    ${voucherCode && discount > 0 ? `
    <div class="co-total-row" style="color:#4B672D;">
      <span>✓ Mã ${voucherCode}</span><span>−${fmt(discount)}</span>
    </div>` : ''}
    ${voucherCode && isFreeShip ? `
    <div class="co-total-row" style="color:#4B672D;">
      <span>✓ Mã ${voucherCode}</span><span>Freeship</span>
    </div>` : ''}
    ${pointsAppliedFlag ? `
    <div class="co-total-row" style="color:#c9a96e;">
      <span>💎 ${pointsUsed} điểm</span><span>−${fmt(pointsDiscount)}</span>
    </div>` : ''}
    <div class="co-total-row">
      <span>Phí vận chuyển</span>
      <span>${free ? '<span style="color:#4B672D;font-weight:600;">Miễn phí</span>' : fmt(ship)}</span>
    </div>
    ${isFirstOrder && free ? `<div style="font-size:10px;color:#4B672D;text-align:right;margin-top:-6px;opacity:.8;">✓ Ưu đãi đơn đầu tiên</div>` : ''}
    <hr style="border:none;border-top:1px solid rgba(91,103,75,.1);margin:10px 0;">
    <div class="co-total-row grand"><span>Tổng cộng</span><span>${fmt(total)}</span></div>
  `;
}

/* ── Payment method ── */
document.getElementById('payCards')?.addEventListener('click', e => {
  const card = e.target.closest('.pay-card');
  if (!card) return;

  // Reset tất cả
  document.querySelectorAll('.pay-card').forEach(c => {
    c.classList.remove('selected');
    const check = c.querySelector('.pay-check');
    if (check) check.textContent = '';
    const radio = c.querySelector('input[type=radio]');
    if (radio) radio.checked = false;
  });

  // Chọn card hiện tại
  card.classList.add('selected');
  const check = card.querySelector('.pay-check');
  if (check) check.textContent = '✓';
  const radio = card.querySelector('input[type=radio]');
  if (radio) radio.checked = true;
});

/* ── Place order ── */
document.getElementById('placeOrderBtn')?.addEventListener('click', async () => {
  // Validate form
  const fields = [
    { id: 'coName',  errId: 'coNameErr',  label: 'Họ và tên' },
    { id: 'coPhone', errId: 'coPhoneErr', label: 'Số điện thoại' },
    { id: 'coEmail', errId: 'coEmailErr', label: 'Email' },
    { id: 'coAddr',  errId: 'coAddrErr',  label: 'Địa chỉ' },
  ];
  let valid = true;
  fields.forEach(f => {
    const el  = document.getElementById(f.id);
    const err = document.getElementById(f.errId);
    if (el && !el.value.trim()) {
      if (err) err.textContent = `Vui lòng nhập ${f.label}.`;
      el.closest('.co-field')?.classList.add('has-error');
      valid = false;
    } else {
      if (err) err.textContent = '';
      el?.closest('.co-field')?.classList.remove('has-error');
    }
  });
  if (!valid) { toast('Vui lòng điền đầy đủ thông tin giao hàng.', false); return; }

  const items = getCartItems().map(i => ({
    productId: i.productId,
    variantId: i.variantId || null,
    name:  i.name,
    price: i.price  || 0,
    qty:   i.qty    || 1,
  }));
  if (!items.length) { toast('Giỏ hàng trống.', false); return; }

  const sub     = calcSubtotal();
  const free    = isFreeShip || isFirstOrder;
  const ship    = free ? 0 : (sub > 0 ? SHIP_FEE : 0);
  const disc    = discount + pointsDiscount;
  const total   = Math.max(0, sub - disc + ship);
  const payment = document.querySelector('input[name="payment"]:checked')?.value || 'cod';

  const payload = {
    name:    document.getElementById('coName')?.value?.trim()  || '',
    phone:   document.getElementById('coPhone')?.value?.trim() || '',
    email:   document.getElementById('coEmail')?.value?.trim() || '',
    address: document.getElementById('coAddr')?.value?.trim()  || '',
    note:    document.getElementById('coNote')?.value?.trim()  || '',
    payment, items,
    subtotal: sub,
    discount,
    voucher_code:     voucherCode    || '',
    points_used:      pointsUsed,
    points_discount:  pointsDiscount,
    shipping: ship,
    total,
    is_first_order: isFirstOrder,
  };

  const btn = document.getElementById('placeOrderBtn');
  btn.classList.add('loading');
  btn.disabled = true;

  try {
    const res  = await fetch('/api/place-order/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (!data.ok) {
      toast(data.message || 'Đặt hàng thất bại.', false);
      btn.classList.remove('loading');
      btn.disabled = false;
      return;
    }

    // Xóa giỏ hàng + discount
    localStorage.removeItem(CART_KEY);
    localStorage.removeItem(DISCOUNT_KEY);

    // Nếu server trả về redirect → VNPAY / MoMo / PayPal
    if (data.redirect) {
      window.location.href = data.redirect;
      return;
    }

    // COD: hiện overlay thành công
    btn.classList.remove('loading');
    btn.disabled = false;
    const overlay = document.getElementById('successOverlay');
    const orderId = document.getElementById('successOrderId');
    if (orderId) orderId.textContent = data.order_id || `AMI-${Date.now().toString().slice(-6)}`;
    if (overlay) overlay.style.display = 'flex';

  } catch (err) {
    toast('Có lỗi xảy ra. Vui lòng thử lại.', false);
    btn.classList.remove('loading');
    btn.disabled = false;
  }
});

/* ── INIT ── */
renderCartItems();
renderTotals();