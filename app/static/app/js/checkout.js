/* =============================================================
   checkout.js (inlined)
   ============================================================= */
const CART_ITEMS = [
  { name: 'Dior Sauvage Elixir', brand: 'Dior', img: 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=200&q=80', qty: 1, price: 4200000 },
  { name: 'Bleu de Chanel EDP', brand: 'Chanel', img: 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=200&q=80', qty: 2, price: 3800000 },
];

const VOUCHERS = {
  'WELCOME20': { label: 'WELCOME20 — Giảm 20%', discount: 0.2, type: 'pct' },
  'VIP50K':    { label: 'VIP50K — Giảm 50.000₫',  discount: 50000, type: 'flat' },
  'FREESHIP':  { label: 'FREESHIP — Miễn phí ship', discount: 30000, type: 'ship' },
};

let appliedVoucher = null;
const SHIP_FEE = 30000;

const fmt = n => n.toLocaleString('vi-VN') + '₫';

/* Render cart items */
const coItems = document.getElementById('coItems');
CART_ITEMS.forEach(item => {
  const el = document.createElement('div');
  el.className = 'co-item';
  el.innerHTML = `
    <div class="co-item-img-wrap">
      <img class="co-item-img" src="${item.img}" alt="${item.name}" loading="lazy">
      <span class="co-item-qty">${item.qty}</span>
    </div>
    <div style="flex:1">
      <p class="co-item-brand">${item.brand}</p>
      <p class="co-item-name">${item.name}</p>
    </div>
    <span class="co-item-price">${fmt(item.price * item.qty)}</span>
  `;
  coItems.appendChild(el);
});

/* Compute + render totals */
function renderTotals() {
  const subtotal = CART_ITEMS.reduce((s, i) => s + i.price * i.qty, 0);
  let discount   = 0;
  let ship       = SHIP_FEE;
  let discLabel  = null;

  if (appliedVoucher) {
    const v = VOUCHERS[appliedVoucher];
    if (v.type === 'pct')  { discount = subtotal * v.discount; discLabel = `-${v.discount*100}%`; }
    if (v.type === 'flat') { discount = v.discount; discLabel = `-${fmt(v.discount)}`; }
    if (v.type === 'ship') { ship = 0; discLabel = 'Miễn phí'; }
  }

  const total = subtotal - discount + ship;
  const totals = document.getElementById('coTotals');
  totals.innerHTML = `
    <div class="co-total-row"><span>Tạm tính</span><span>${fmt(subtotal)}</span></div>
    ${discount ? `<div class="co-total-row discount"><span>Giảm giá (${appliedVoucher})</span><span>−${fmt(discount)}</span></div>` : ''}
    <div class="co-total-row"><span>Phí vận chuyển</span><span>${ship === 0 ? 'Miễn phí' : fmt(ship)}</span></div>
    <div class="co-total-row grand"><span>Tổng cộng</span><span>${fmt(total)}</span></div>
  `;
}
renderTotals();

/* Voucher apply */
document.getElementById('applyVoucher')?.addEventListener('click', () => {
  const code = document.getElementById('voucherInput').value.trim().toUpperCase();
  if (!code) return;
  if (VOUCHERS[code]) {
    appliedVoucher = code;
    const tag = document.getElementById('voucherTag');
    document.getElementById('voucherTagText').textContent = VOUCHERS[code].label;
    tag.classList.add('show');
    renderTotals();
  } else {
    document.getElementById('voucherInput').style.borderColor = 'rgba(192,57,43,.5)';
    setTimeout(() => document.getElementById('voucherInput').style.borderColor = '', 1500);
  }
});
document.getElementById('removeVoucher')?.addEventListener('click', () => {
  appliedVoucher = null;
  document.getElementById('voucherTag').classList.remove('show');
  document.getElementById('voucherInput').value = '';
  renderTotals();
});

/* Payment selection */
document.getElementById('payCards')?.addEventListener('click', e => {
  const card = e.target.closest('.pay-card');
  if (!card) return;
  document.querySelectorAll('.pay-card').forEach(c => {
    c.classList.remove('selected');
    c.querySelector('.pay-check').textContent = '';
  });
  card.classList.add('selected');
  card.querySelector('.pay-check').textContent = '✓';
  card.querySelector('input').checked = true;
});

/* Validation */
const validators = {
  name:    v => v.trim().length >= 2 ? '' : 'Vui lòng nhập họ tên đầy đủ.',
  phone:   v => /^(0|\+84)[0-9]{8,10}$/.test(v.replace(/\s/g,'')) ? '' : 'Số điện thoại không hợp lệ.',
  email:   v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? '' : 'Email không hợp lệ.',
  country: v => v ? '' : 'Vui lòng chọn quốc gia.',
  addr:    v => v.trim().length >= 10 ? '' : 'Vui lòng nhập địa chỉ đầy đủ.',
};

const fields = [
  { input: 'coName',    error: 'coNameErr',    group: 'coNameField',    rule: 'name' },
  { input: 'coPhone',   error: 'coPhoneErr',   group: 'coPhoneField',   rule: 'phone' },
  { input: 'coEmail',   error: 'coEmailErr',   group: 'coEmailField',   rule: 'email' },
  { input: 'coCountry', error: 'coCountryErr', group: 'coCountryField', rule: 'country' },
  { input: 'coAddr',    error: 'coAddrErr',    group: 'coAddrField',    rule: 'addr' },
];

fields.forEach(({ input, error, group, rule }) => {
  const el = document.getElementById(input);
  const errEl = document.getElementById(error);
  const grp   = document.getElementById(group);
  if (!el) return;
  const check = () => {
    const msg = validators[rule](el.value);
    errEl.textContent = msg;
    grp.classList.toggle('error', !!msg);
    return !msg;
  };
  el.addEventListener('blur', check);
  el.addEventListener('input', () => { if (grp.classList.contains('error')) check(); });
});

/* Place order */
document.getElementById('placeOrderBtn')?.addEventListener('click', async () => {
  let valid = true;
  fields.forEach(({ input, error, group, rule }) => {
    const el  = document.getElementById(input);
    const err = document.getElementById(error);
    const grp = document.getElementById(group);
    if (!el) return;
    const msg = validators[rule](el.value);
    err.textContent = msg;
    grp.classList.toggle('error', !!msg);
    if (msg) valid = false;
  });
  if (!valid) { document.getElementById('coNameField')?.scrollIntoView({ behavior: 'smooth', block: 'center' }); return; }

  const btn = document.getElementById('placeOrderBtn');
  btn.classList.add('loading'); btn.disabled = true;
  await new Promise(r => setTimeout(r, 1800));
  btn.classList.remove('loading');

  const orderId = 'AMI-2025-' + String(Math.floor(Math.random()*900)+100);
  document.getElementById('successOrderId').textContent = orderId;
  document.getElementById('successOverlay').classList.add('show');
});
