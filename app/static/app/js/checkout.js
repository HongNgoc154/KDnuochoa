/* =============================================================
   checkout.js (inlined)
   ============================================================= */
const CART_ITEMS = [
  { name: 'Dior Sauvage Elixir', brand: 'Dior', img: 'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=200&q=80', qty: 1, price: 4200000 },
  { name: 'Bleu de Chanel EDP', brand: 'Chanel', img: 'https://images.unsplash.com/photo-1619994403073-2cec5a97dd6d?auto=format&fit=crop&w=200&q=80', qty: 2, price: 3800000 },
];

const fmt = n => n.toLocaleString('vi-VN') + '₫';
const SHIP_FEE = 30000;
const isLoggedIn = !!window.CHECKOUT_AUTH?.isLoggedIn;
const memberVouchers = JSON.parse(document.getElementById('voucherData')?.textContent || '[]');
let appliedVoucher = null;
let appliedDiscount = 0;
let freeShip = false;

function toast(msg, ok = true) {
  const el = document.createElement('div');
  el.textContent = msg;
  el.style.cssText = `position:fixed;top:20px;right:20px;z-index:9999;padding:12px 16px;border-radius:14px;background:${ok ? 'rgba(87,98,56,.95)' : 'rgba(140,45,30,.95)'};color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.2);backdrop-filter: blur(6px);`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2400);
}
/* Render cart items */
const coItems = document.getElementById('coItems');
CART_ITEMS.forEach(item => {
  const el = document.createElement('div');
  el.className = 'co-item';
  el.innerHTML = `<div class="co-item-img-wrap"><img class="co-item-img" src="${item.img}" alt="${item.name}"><span class="co-item-qty">${item.qty}</span></div><div style="flex:1"><p class="co-item-brand">${item.brand}</p><p class="co-item-name">${item.name}</p></div><span class="co-item-price">${fmt(item.price * item.qty)}</span>`;
  coItems.appendChild(el);
});

/* Compute + render totals */
function subtotal() { return CART_ITEMS.reduce((s, i) => s + i.price * i.qty, 0); }
function renderTotals() {
  const sub = subtotal();
  const ship = freeShip ? 0 : SHIP_FEE;
  const total = Math.max(0, sub - appliedDiscount + ship);
  document.getElementById('coTotals').innerHTML = `<div class="co-total-row"><span>Tạm tính</span><span>${fmt(sub)}</span></div>${appliedVoucher ? `<div class="co-total-row discount"><span>Giảm giá (${appliedVoucher})</span><span>−${fmt(appliedDiscount)}</span></div>` : ''}<div class="co-total-row"><span>Phí vận chuyển</span><span>${ship === 0 ? 'Miễn phí' : fmt(ship)}</span></div><div class="co-total-row grand"><span>Tổng cộng</span><span>${fmt(total)}</span></div>`;
}
renderTotals();

  function renderMemberVouchers() {
  const box = document.getElementById('coMemberVouchers');
  if (!box) return;
  box.innerHTML = '';
  memberVouchers.filter(v => v.status === 'Còn hiệu lực').forEach(v => {
    const card = document.createElement('div');
    card.className = 'co-member-card';
    card.innerHTML = `<span class="badge">${v.exclusive_badge}</span><div class="code">${v.code}</div><div class="meta">${v.description || v.name}</div><div class="meta">HSD: ${v.expiry || '--'} • ĐH tối thiểu: ${fmt(v.minimum_order || 0)}</div><button class="btn-apply apply-now" data-code="${v.code}">Áp dụng ngay</button>`;
    box.appendChild(card);
  });
}
renderMemberVouchers();

async function applyVoucher(code) {
  if (!isLoggedIn) {
    toast('Vui lòng đăng nhập để sử dụng ưu đãi thành viên.', false);
    return;
  }
  const fd = new FormData();
  fd.append('code', code);
  fd.append('subtotal', String(subtotal()));
  const res = await fetch('/api/apply-voucher/', { method: 'POST', body: fd });
  const data = await res.json();
  if (!data.ok) return toast(data.message, false);

  appliedVoucher = data.code;
  freeShip = data.type.includes('free');
  appliedDiscount = freeShip ? 0 : (data.discount || 0);
  document.getElementById('voucherTagText').textContent = data.code;
  document.getElementById('voucherTag').classList.add('show');
  renderTotals();
  toast(data.message, true);
}


/* Voucher apply */
document.getElementById('applyVoucher')?.addEventListener('click', () => {
  const code = document.getElementById('voucherInput').value.trim().toUpperCase();
  if (!code) return;
  applyVoucher(code);
});
document.getElementById('coMemberVouchers')?.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-code]');
  if (!btn) return;
  document.getElementById('voucherInput').value = btn.dataset.code;
  applyVoucher(btn.dataset.code);
});
document.getElementById('removeVoucher')?.addEventListener('click', () => {
  appliedVoucher = null; appliedDiscount = 0; freeShip = false;
  document.getElementById('voucherTag').classList.remove('show');
  
  renderTotals();
});

