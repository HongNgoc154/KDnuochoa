(() => {
  const cartItemsWrap = document.querySelector('[data-cart-items]');
  const emptyState = document.querySelector('[data-empty-state]');
  const subtotalEl = document.querySelector('[data-subtotal]');
  const discountEl = document.querySelector('[data-discount]');
  const shippingEl = document.querySelector('[data-shipping]');
  const totalEl = document.querySelector('[data-total]');
  const voucherInput = document.querySelector('[data-voucher-input]');
  const voucherMessage = document.querySelector('[data-voucher-message]');
  let discount = 0;

  const formatVnd = (value) => `${Math.round(value).toLocaleString('vi-VN')}₫`;

  const updateTotals = () => {
    const items = [...document.querySelectorAll('.cart-item')];
    const subtotal = items.reduce((sum, item) => {
      const price = Number(item.dataset.price || 0);
      const qty = Number(item.querySelector('input')?.value || 1);
      const line = price * qty;
      item.querySelector('[data-line-total]').textContent = formatVnd(line);
      return sum + line;
    }, 0);

    const shipping = subtotal > 0 ? 30000 : 0;
    subtotalEl.textContent = formatVnd(subtotal);
    discountEl.textContent = `-${formatVnd(discount)}`;
    shippingEl.textContent = formatVnd(shipping);
    totalEl.textContent = formatVnd(Math.max(0, subtotal - discount + shipping));

    const empty = items.length === 0;
    emptyState.hidden = !empty;
    cartItemsWrap.hidden = empty;
  };

  // Quantity / remove micro interactions.
  cartItemsWrap?.addEventListener('click', (event) => {
    const item = event.target.closest('.cart-item');
    if (!item) return;

    const input = item.querySelector('input');
    if (event.target.matches('[data-action="plus"]')) {
      input.value = Number(input.value) + 1;
      item.classList.add('pulse');
    }
    if (event.target.matches('[data-action="minus"]')) {
      input.value = Math.max(1, Number(input.value) - 1);
      item.classList.add('pulse');
    }

    if (event.target.matches('[data-remove]')) {
      item.classList.add('removing');
      setTimeout(() => {
        item.remove();
        updateTotals();
      }, 320);
      return;
    }

    setTimeout(() => item.classList.remove('pulse'), 260);
    updateTotals();
  });

  cartItemsWrap?.addEventListener('input', (event) => {
    if (!event.target.matches('input[type="number"]')) return;
    event.target.value = Math.max(1, Number(event.target.value || 1));
    updateTotals();
  });

  document.querySelector('[data-apply-voucher]')?.addEventListener('click', () => {
    const code = voucherInput?.value.trim().toUpperCase();
    if (code === 'AMI10') {
      discount = 300000;
      voucherMessage.textContent = 'Áp dụng mã thành công ✨';
    } else {
      discount = 0;
      voucherMessage.textContent = 'Mã không hợp lệ.';
    }
    updateTotals();
  });

  const countdownEl = document.querySelector('[data-countdown]');
  if (countdownEl) {
    let remain = 14 * 60 + 59;
    setInterval(() => {
      remain = Math.max(0, remain - 1);
      const m = String(Math.floor(remain / 60)).padStart(2, '0');
      const s = String(remain % 60).padStart(2, '0');
      countdownEl.textContent = `${m}:${s}`;
    }, 1000);
  }

  document.querySelectorAll('[data-mini-track], [data-suggest-track]').forEach((track) => {
    const wrap = track.closest('section, .mini-carousel, .cart-suggestions');
    const prev = wrap?.querySelector('[data-suggest-prev], [data-mini-prev]');
    const next = wrap?.querySelector('[data-suggest-next], [data-mini-next]');
    const step = () => track.clientWidth * 0.75;
    prev?.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    next?.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
  });

  document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('[data-checkout]');
  if (!btn) return;

  btn.addEventListener('click', (event) => {
    window.location.href = btn.dataset.checkoutUrl;
  });

    document.body.classList.add('checking-out');
    setTimeout(() => {
      window.location.href = event.currentTarget.dataset.checkoutUrl || '/checkout/';
    }, 260);
  });

  updateTotals();
})();
