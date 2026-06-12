

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
      const toDelete = getCart().filter(i => i.checked !== false);
      // Sync xóa từng item lên DB
      toDelete.forEach(item => {
        if (item.variantId && /^\d+$/.test(String(item.variantId))) {
          pushCartUpdate(item.variantId, 0, 'remove');
        }
      });
      saveCart(getCart().filter(i => i.checked === false));
      renderCart();
      return;
    }
    const art = e.target.closest('.cart-item');
    if (!art) return;
    const idx = parseInt(art.dataset.cartIdx ?? '-1');

    if (e.target.matches('[data-action="plus"]')) {
      const cart     = getCart();
      const item     = cart[idx];
      if (!item) return;

      const newQty     = (item.qty || 1) + 1;
      const localStock = Number(item.stock || 0);

      // Chặn ngay nếu local stock đã biết và vượt quá
      if (localStock > 0 && newQty > localStock) {
        showCartToast('Số lượng tồn kho không đủ, vui lòng giảm bớt số lượng sản phẩm', 0);
        return;
      }

      // Verify với server
      const variantId = (item.variantId && item.variantId !== 'default' && /^\d+$/.test(String(item.variantId)))
                        ? item.variantId : null;

      fetch('/api/check-stock/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
        body:    JSON.stringify({
          product_id: item.productId,
          variant_id: variantId,
          qty:        newQty,
        }),
      })
      .then(r => r.json())
      .then(data => {
        const latestCart = getCart();
        const latestIdx  = latestCart.findIndex(i => i.key === item.key);
        if (latestIdx < 0) return;

        const realStock = Number(data.stock || localStock);

        if (!data.ok) {
          // Cập nhật stock mới vào localStorage
          latestCart[latestIdx].stock = realStock;
          if (latestCart[latestIdx].qty > realStock) {
            latestCart[latestIdx].qty = realStock;
          }
          saveCart(latestCart);
          renderCart();
          showCartToast(
            data.message || 'Số lượng tồn kho không đủ, vui lòng giảm bớt số lượng sản phẩm',
            0
          );
          return;
        }

        // OK → cập nhật
        latestCart[latestIdx].qty   = newQty;
        latestCart[latestIdx].stock = realStock;
        saveCart(latestCart);
        pushCartUpdate(item.variantId, newQty);

        art.querySelector('.cart-qty-val').textContent = String(newQty);
        art.querySelector('[data-line-total]').textContent =
          formatVnd((latestCart[latestIdx].price || 0) * newQty);
        art.classList.add('pulse');
        setTimeout(() => art.classList.remove('pulse'), 260);
        updateSummary();
      })
      .catch(() => {
        // Lỗi mạng → vẫn cho tăng tạm thời
        const latestCart = getCart();
        const latestIdx  = latestCart.findIndex(i => i.key === item.key);
        if (latestIdx < 0) return;
        latestCart[latestIdx].qty = newQty;
        saveCart(latestCart);
        pushCartUpdate(item.variantId, newQty);
        art.querySelector('.cart-qty-val').textContent = String(newQty);
        updateSummary();
      });

      return; // async rồi, không xử lý sync nữa
    }
    if (e.target.matches('[data-action="minus"]')) {
      const cart = getCart();
      if (cart[idx]) {
        cart[idx].qty = Math.max(1, (cart[idx].qty || 1) - 1);
        saveCart(cart);
        // Sync lên DB
        pushCartUpdate(cart[idx].variantId, cart[idx].qty);
      }
      art.querySelector('.cart-qty-val').textContent = String(cart[idx]?.qty || 1);
      art.querySelector('[data-line-total]').textContent = formatVnd((cart[idx]?.price || 0) * (cart[idx]?.qty || 1));
      art.classList.add('pulse');
      setTimeout(() => art.classList.remove('pulse'), 260);
      updateSummary();
    }
    if (e.target.closest('[data-remove]')) {
      const cartItem = getCart()[idx];
      // Sync xóa lên DB
      if (cartItem?.variantId && /^\d+$/.test(String(cartItem.variantId))) {
        pushCartUpdate(cartItem.variantId, 0, 'remove');
      }
      art.style.transition = 'opacity .3s,transform .3s';
      art.style.opacity    = '0';
      art.style.transform  = 'translateX(30px)';
      setTimeout(() => {
        const cart = getCart();
        cart.splice(idx, 1);
        saveCart(cart);
        renderCart();
      }, 320);
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
    saveDiscountState();
    window.location.href = this.dataset.checkoutUrl || '/checkout/';
  });

  /* ── Sync giỏ hàng từ server (khi đã đăng nhập) ── */
  async function syncCartFromServer() {
  if (!isLoggedIn()) return;
  try {
    const res  = await fetch('/api/cart/');
    const data = await res.json();

    if (!data.ok) return;

    // Server là nguồn duy nhất — replace hoàn toàn localStorage
    const serverCart = data.items || [];

    // Giữ lại trạng thái checked từ local nếu có
    const localCart = getCart();
    const localCheckMap = {};
    localCart.forEach(i => { localCheckMap[i.key] = i.checked; });

    // Apply checked state từ local vào server cart
    const merged = serverCart.map(item => ({
      ...item,
      checked: localCheckMap[item.key] !== undefined
               ? localCheckMap[item.key]
               : true,
    }));

    // Sync item local chưa có trên server lên DB
    // (item thêm từ trình duyệt này nhưng chưa kịp sync)
    for (const localItem of localCart) {
      const onServer = serverCart.find(s => s.key === localItem.key);
      if (!onServer && localItem.variantId && /^\d+$/.test(String(localItem.variantId))) {
        // Push lên server
        fetch('/api/cart/update/', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
          body:    JSON.stringify({
            variantId: localItem.variantId,
            qty:       localItem.qty,
            action:    'set',
          }),
        }).catch(() => {});
        // Thêm vào merged để hiển thị ngay
        merged.push({ ...localItem });
      }
    }

    saveCart(merged);

  } catch (e) {
    console.warn('[cart] syncCartFromServer error:', e);
  }
}

  /* ── Push thay đổi lên server ── */
  // function pushCartUpdate(variantId, qty, action = 'set') {
  //   if (!isLoggedIn()) return;
  //   if (!variantId || !/^\d+$/.test(String(variantId))) return;
  //   fetch('/api/cart/update/', {
  //     method:  'POST',
  //     headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
  //     body:    JSON.stringify({ variantId, qty, action }),
  //   }).catch(() => {});
  // }

  /* ── Validate tồn kho từ server khi load trang giỏ ── */
  async function validateCartStock() {
    const cart = getCart();
    if (!cart.length) return;

    let changed   = false;
    const updated = [...cart];

    for (let i = 0; i < updated.length; i++) {
      const item = updated[i];

      const rawVariantId = item.variantId;
      const variantId    = (rawVariantId && rawVariantId !== 'default' && /^\d+$/.test(String(rawVariantId)))
                           ? rawVariantId : null;
      const productId    = item.productId || null;

      if (!variantId && !productId) continue;

      try {
        const res = await fetch('/api/check-stock/', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
          body:    JSON.stringify({ product_id: productId, variant_id: variantId, qty: 1 }),
        });

        if (res.status === 404) {
          updated.splice(i, 1); i--;
          changed = true;
          showCartToast(`"${item.name}" không còn tồn tại và đã được xóa khỏi giỏ.`, 0);
          continue;
        }

        const data      = await res.json();
        const realStock = Number(data.stock || 0);

        if (!data.ok || realStock <= 0) {
          updated.splice(i, 1); i--;
          changed = true;
          showCartToast(`"${item.name}" đã hết hàng và đã được xóa khỏi giỏ.`, 0);
          continue;
        }

        if (updated[i].stock !== realStock) {
          updated[i].stock = realStock;
          changed = true;
        }

        if (updated[i].qty > realStock) {
          updated[i].qty = realStock;
          changed = true;
          showCartToast(`Số lượng "${item.name}" đã được điều chỉnh còn ${realStock} do tồn kho thay đổi.`, 0);
        }

      } catch (e) {
        console.warn('[cart] validateCartStock bỏ qua item:', item.key, e);
      }
    }

    if (changed) {
      saveCart(updated);
      renderCart();
    }
  }

  /* ── INIT ── */
  syncCartFromServer().then(() => {
    renderCart();
    checkFirstOrder();
    loadPoints();
    validateCartStock();
  });

})();  // ← đóng IIFE initCartPage

/* ── Badge ── */
// document.addEventListener('DOMContentLoaded', updateCartBadge);
// if (document.readyState !== 'loading') updateCartBadge();

// /* ── Helpers cũ (giữ nguyên) ── */
// function removeCartItem(key) {
//   let cart = JSON.parse(localStorage.getItem('ami_cart') || '[]');
//   cart = cart.filter(i => i.key !== key);
//   localStorage.setItem('ami_cart', JSON.stringify(cart));
//   syncCartBadge();
// }

// function clearCart() {
//   localStorage.removeItem('ami_cart');
//   syncCartBadge();
// }

// function syncCartBadge() {
//   const cart = JSON.parse(localStorage.getItem('ami_cart') || '[]');
//   const total = cart.reduce((sum, i) => sum + Number(i.qty || 0), 0);
//   document.querySelectorAll('[data-cart-badge]').forEach(b => {
//     b.textContent = String(total);
//     b.style.display = total > 0 ? '' : 'none';
//   });
// }