/* =============================================================
   Ami Perfumery — product.js
   Tất cả logic tương tác cho trang chi tiết sản phẩm.

   Modules:
   1. Gallery        — thumbnail switching + image transition
   2. Magnifier      — smooth lens zoom với interpolation
   3. MobileSwipe    — touch swipe gallery
   4. StickyInfo     — scroll-based sticky + reveal
   5. Wishlist       — particle burst heart animation
   6. SizePills      — size selector
   7. Quantity       — qty +/–
   8. CartBtn        — add-to-cart micro-interaction
   9. Tabs           — animated ink-bar tab switching
   10. Bars          — animate longevity + review bars
   11. Carousels     — related + brand-more (arrow hover)
   12. Reveal        — IntersectionObserver scroll reveal
   ============================================================= */

/* ─── 1. GALLERY ───────────────────────────────────────────── */
(function initGallery() {
  const thumbBtns = [...document.querySelectorAll('.pd-thumb')];
  const mainImg   = document.getElementById('pdMainImg');
  const dots      = [...document.querySelectorAll('.pd-dot')];

  if (!mainImg || !thumbBtns.length) return;

  /* Image sources (full-size) — synced with thumbnail srcs */
  /* Image sources lấy trực tiếp từ thumbnail render bởi backend */
    const imageSrcs = thumbBtns.map((btn) => {
    const fullSrc = btn.dataset.full;
    const thumbImg = btn.querySelector('img');
    return fullSrc || thumbImg?.src;
  }).filter(Boolean);

  let current = 0;

  /* Switch to image by index */
  const goTo = (idx) => {
    if (idx === current || !imageSrcs[idx]) return;
    current = idx;

    /* Fade + subtle zoom transition */
    mainImg.classList.add('pd-img-fade');

    /* After CSS transition ends, swap src + remove fade class */
    setTimeout(() => {
      mainImg.src = imageSrcs[idx];
      mainImg.classList.remove('pd-img-fade');
    }, 200);

    /* Update active states */
    thumbBtns.forEach((btn, i) => btn.classList.toggle('active', i === idx));
    dots.forEach((dot, i) => dot.classList.toggle('active', i === idx));

    /* Update magnifier zoom pane background */
    updateZoomPaneBg(imageSrcs[idx]);
  };

  thumbBtns.forEach((btn, i) => {
    btn.addEventListener('click', () => goTo(i));
  });

  /* Expose goTo for mobile swipe */
  window._pdGalleryGoTo  = goTo;
  window._pdGalleryCount = imageSrcs.length;
  window._pdGalleryGet   = () => current;
})();

/* ─── 2. MAGNIFIER (Hover Zoom) ───────────────────────────── */
/*
  Principle:
  - Mouse enters the image wrap → show lens + zoom pane
  - On mousemove:
      1. Compute cursor position relative to image (0–1 range)
      2. Apply smooth interpolation (lerp) so lens/zoom pane
         lag slightly behind cursor for a luxury-feel
      3. Move .pd-lens to cursor position (CSS transform)
      4. Set background-position of zoom pane so it shows the
         corresponding zoomed region
  - Mouse leaves → hide both elements
*/
(function initMagnifier() {
  const wrap     = document.querySelector('.pd-main-img-wrap');
  const img      = document.getElementById('pdMainImg');
  const lens     = document.getElementById('pdLens');
  const zoomPane = document.getElementById('pdZoomPane');
  if (!wrap || !img || !lens || !zoomPane) return;

  const ZOOM   = 2.8;   /* zoom factor */
  const LERP_F = 0.12;  /* interpolation factor: lower = smoother/slower */

  /* Target and current interpolated positions */
  let tx = 0, ty = 0;   /* target (raw cursor) */
  let cx = 0, cy = 0;   /* current (interpolated) */
  let rafId = null;
  let isActive = false;

  /* Set background-image of zoom pane */
  const updateZoomPaneBg = (src) => {
    zoomPane.style.backgroundImage = `url(${src})`;
    zoomPane.style.backgroundSize  = `${img.offsetWidth * ZOOM}px ${img.offsetHeight * ZOOM}px`;
  };

  /* Expose for gallery switching */
  window.updateZoomPaneBg = updateZoomPaneBg;

  /* Lerp animation loop */
  const animate = () => {
    if (!isActive) return;

    /* Smooth lerp towards target */
    cx += (tx - cx) * LERP_F;
    cy += (ty - cy) * LERP_F;

    /* Move lens */
    lens.style.left = `${cx}px`;
    lens.style.top  = `${cy}px`;

    /* Compute bg-position for zoom pane
       The zoom pane shows a zoomed region centred on (cx, cy) of the original image.
       bg-position shifts so that cx/cy maps to the center of the pane.
    */
    const rect   = wrap.getBoundingClientRect();
    const xRatio = cx / rect.width;
    const yRatio = cy / rect.height;

    const bgX = -(xRatio * img.offsetWidth  * ZOOM - zoomPane.offsetWidth  / 2);
    const bgY = -(yRatio * img.offsetHeight * ZOOM - zoomPane.offsetHeight / 2);

    zoomPane.style.backgroundPosition = `${bgX}px ${bgY}px`;

    rafId = requestAnimationFrame(animate);
  };

  wrap.addEventListener('mouseenter', () => {
    /* Only activate on desktop (pointer:fine) */
    if (!window.matchMedia('(pointer:fine)').matches) return;
    isActive = true;
    wrap.classList.add('zoom-active');
    updateZoomPaneBg(document.getElementById('pdMainImg').src);
    rafId = requestAnimationFrame(animate);
  });

  wrap.addEventListener('mousemove', (e) => {
    if (!isActive) return;
    const rect = wrap.getBoundingClientRect();
    tx = e.clientX - rect.left;
    ty = e.clientY - rect.top;
  });

  wrap.addEventListener('mouseleave', () => {
    isActive = false;
    wrap.classList.remove('zoom-active');
    cancelAnimationFrame(rafId);
  });
})();

/* Helper exposed for gallery src switch */
function updateZoomPaneBg(src) {
  if (window.updateZoomPaneBg) window.updateZoomPaneBg(src);
}

/* ─── 3. MOBILE SWIPE ──────────────────────────────────────── */
(function initMobileSwipe() {
  const wrap = document.querySelector('.pd-main-img-wrap');
  if (!wrap) return;

  let startX = 0;
  let moved  = false;

  wrap.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
    moved  = false;
  }, { passive: true });

  wrap.addEventListener('touchmove', () => { moved = true; }, { passive: true });

  wrap.addEventListener('touchend', (e) => {
    if (!moved) return;
    const dx    = e.changedTouches[0].clientX - startX;
    const count = window._pdGalleryCount || 1;
    const cur   = window._pdGalleryGet ? window._pdGalleryGet() : 0;
    const goTo  = window._pdGalleryGoTo;
    if (!goTo) return;

    if (dx < -40 && cur < count - 1) goTo(cur + 1);
    if (dx >  40 && cur > 0)         goTo(cur - 1);
  }, { passive: true });
})();

/* ─── 4. STICKY INFO REVEAL ────────────────────────────────── */
(function initStickyReveal() {
  const revealEls = document.querySelectorAll('.reveal-up');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.05 });
  revealEls.forEach(el => obs.observe(el));
})();

/* ─── 5. WISHLIST — Particle burst ─────────────────────────── */
/*
  On click:
  1. Toggle .is-liked → CSS updates heart fill + scale
  2. Add .bounce → keyframe: scale 1→1.45→0.9→1.2
  3. Add .bursting → ::before pseudo element: 6-directional
     box-shadow that expands via @keyframes heartBurst
  4. Remove both classes after 580ms
*/
(function initWishlist() {
  const btn   = document.getElementById('pdWishBtn');
  const heart = document.getElementById('pdWishHeart');
  if (!btn || !heart) return;

  btn.addEventListener('click', () => {
    const liked = btn.classList.toggle('is-liked');
    btn.setAttribute('aria-pressed', String(liked));
    heart.textContent = liked ? '♥' : '♡';

    btn.classList.remove('bursting', 'bounce');
    void btn.offsetWidth;          /* force reflow to re-trigger animation */
    btn.classList.add('bursting', 'bounce');
    setTimeout(() => btn.classList.remove('bursting', 'bounce'), 580);
  });
})();

/* ─── 6. SIZE PILLS ────────────────────────────────────────── */
/* ─── 6. VARIANT PILLS ─────────────────────────────────────── */
(function initVariantPills() {
  const pills = [...document.querySelectorAll('.pd-size-pill')];
  const priceEl = document.getElementById('pdVariantPrice');
  const metaEl = document.getElementById('pdVariantMeta');
  const stockEl = document.getElementById('pdStockStatus');
  const variantsNode = document.getElementById('pdVariantsData');

  if (!pills.length || !variantsNode) return;

  let variants = [];
  try {
    variants = JSON.parse(variantsNode.textContent || '[]');
  } catch {
    variants = [];
  }

  const selectedAttrs = {};
  pills.forEach((pill) => {
    const attr = pill.dataset.attrName;
    const value = pill.dataset.attrValue;
    if (pill.classList.contains('active') && attr && value) {
      selectedAttrs[attr] = value;
    }
  });

  const isMatch = (variant) => {
    const attrs = variant.attributes || {};
    return Object.entries(selectedAttrs).every(([name, value]) => attrs[name] === value);
  };

  const applyVariant = () => {
    const matched = variants.find(isMatch) || variants[0];
    if (!matched) return;
    if (priceEl) priceEl.textContent = matched.price || 'Liên hệ';
    if (metaEl) metaEl.textContent = `${matched.sku || 'SKU'} · Còn ${matched.stock || 0}`;
    if (stockEl) {
      const inStock = Number(matched.stock || 0) > 0;
      stockEl.textContent = inStock ? '● Còn hàng' : '● Hết hàng';
      stockEl.classList.toggle('in-stock', inStock);
    }
  };

  pills.forEach((pill) => {
    pill.addEventListener('click', () => {
      const attr = pill.dataset.attrName;
      const value = pill.dataset.attrValue;
      if (!attr || !value) return;

      pills
        .filter((p) => p.dataset.attrName === attr)
        .forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      selectedAttrs[attr] = value;
      applyVariant();
    });
  });
  applyVariant();
})();

/* ─── 7. QUANTITY ──────────────────────────────────────────── */
(function initQuantity() {
  const minusBtn = document.getElementById('pdQtyMinus');
  const plusBtn  = document.getElementById('pdQtyPlus');
  const valEl    = document.getElementById('pdQtyVal');
  if (!minusBtn || !plusBtn || !valEl) return;

  let qty = 1;
  const update = () => {
    valEl.textContent = qty;
    minusBtn.disabled = qty <= 1;
  };

  minusBtn.addEventListener('click', () => { if (qty > 1) { qty--; update(); } });
  plusBtn.addEventListener('click',  () => { qty++; update(); });
  update();
})();

/* ─── 8. CART BUTTON ───────────────────────────────────────── */
/*
  On click:
  - Add .bounce to button → CSS keyframe: scale 1→.95→1.04→1
*/
(function initCartBtn() {
  const btn = document.getElementById('pdAddCart');
  if (!btn) return;

  btn.addEventListener('click', () => {
    btn.classList.remove('bounce');
    void btn.offsetWidth;
    btn.classList.add('bounce');
    setTimeout(() => btn.classList.remove('bounce'), 450);
  });
})();

/* ─── 9. TABS — Animated ink bar ───────────────────────────── */
/*
  Ink bar principle:
  - Measure left/width of the active tab button
  - Set inline style on .pd-tab-ink
  - CSS transitions handle the slide animation
  - Panel switching: hide current panel (hidden attr), show new, trigger animation
*/
(function initTabs() {
  const tabBtns  = document.querySelectorAll('.pd-tab-btn');
  const panels   = document.querySelectorAll('.pd-tab-panel');
  const ink      = document.getElementById('pdTabInk');
  if (!tabBtns.length || !ink) return;

  const moveInk = (btn) => {
    ink.style.left  = `${btn.offsetLeft}px`;
    ink.style.width = `${btn.offsetWidth}px`;
  };

  /* Init ink to active tab */
  const activeBtn = document.querySelector('.pd-tab-btn.active');
  if (activeBtn) moveInk(activeBtn);

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.tab;

      /* Update button states */
      tabBtns.forEach(b => {
        b.classList.toggle('active', b === btn);
        b.setAttribute('aria-selected', String(b === btn));
      });

      /* Slide ink */
      moveInk(btn);

      /* Switch panels: fade + slide via CSS animation */
      panels.forEach(panel => {
        const isTarget = panel.id === `tab-${targetId}`;
        if (isTarget) {
          panel.removeAttribute('hidden');
          /* Trigger bar animations when reviews tab opens */
          if (targetId === 'reviews') animateBars('.pd-rv-bar');
          if (targetId === 'detail')  {/* bars already animated on load */}
        } else {
          panel.setAttribute('hidden', '');
        }
      });
    });
  });

  /* Resize: re-position ink */
  window.addEventListener('resize', () => {
    const active = document.querySelector('.pd-tab-btn.active');
    if (active) moveInk(active);
  });
})();

/* ─── 10. BARS ANIMATION ───────────────────────────────────── */
/*
  Animate width of .pd-lon-bar and .pd-rv-bar
  using data-fill attribute (0–100).
  Called once bars enter viewport, or when tab opens.
*/
function animateBars(selector) {
  document.querySelectorAll(selector).forEach(bar => {
    const fill = bar.dataset.fill || 0;
    setTimeout(() => {
      bar.style.width = `${fill}%`;
    }, 100);
  });
}

(function initBars() {
  /* Longevity bars on main page */
  const lonObs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { animateBars('.pd-lon-bar'); lonObs.disconnect(); }
    });
  }, { threshold: 0.3 });
  const lonSection = document.querySelector('.pd-longevity');
  if (lonSection) lonObs.observe(lonSection);
})();

/* ─── 11. CAROUSELS (Related + Brand More) ─────────────────── */
/*
  Same arrow-hover detection pattern as category.js.
  Mouse near left/right edge (18% zone) → show arrow.
*/
function initArrowCarousel(wrap, track, leftBtn, rightBtn, stepRatio = 0.75, edgeRatio = 0.18) {
  if (!wrap || !track || !leftBtn || !rightBtn) return;

  const updateDisabled = () => {
    const max = track.scrollWidth - track.clientWidth - 2;
    leftBtn.disabled  = track.scrollLeft <= 2;
    rightBtn.disabled = track.scrollLeft >= max;
  };

  wrap.addEventListener('mousemove', (e) => {
    const rect  = wrap.getBoundingClientRect();
    const x     = e.clientX - rect.left;
    const edge  = rect.width * edgeRatio;
    wrap.classList.toggle('show-left',  x < edge && !leftBtn.disabled);
    wrap.classList.toggle('show-right', x > rect.width - edge && !rightBtn.disabled);
  });

  wrap.addEventListener('mouseleave', () => {
    wrap.classList.remove('show-left', 'show-right');
  });

  leftBtn.addEventListener('click', () => {
    track.scrollBy({ left: -(track.clientWidth * stepRatio), behavior: 'smooth' });
  });
  rightBtn.addEventListener('click', () => {
    track.scrollBy({ left:  track.clientWidth * stepRatio,  behavior: 'smooth' });
  });

  track.addEventListener('scroll', updateDisabled, { passive: true });
  updateDisabled();
}

(function initCarousels() {
  initArrowCarousel(
    document.getElementById('relatedWrap'),
    document.getElementById('relatedTrack'),
    document.getElementById('relatedLeft'),
    document.getElementById('relatedRight')
  );
  initArrowCarousel(
    document.getElementById('brandMoreWrap'),
    document.getElementById('brandMoreTrack'),
    document.getElementById('brandMoreLeft'),
    document.getElementById('brandMoreRight')
  );
})();

/* ─── 12. SCROLL REVEAL (sections) ─────────────────────────── */
(function initReveal() {
  const sections = document.querySelectorAll('.reveal-section');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.08 });
  sections.forEach(s => obs.observe(s));
})();

/* ─── HEADER SCROLL ─────────────────────────────────────────── */
(function initHeader() {
  const header = document.getElementById('site-header');
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    const s = window.scrollY > 60;
    header?.classList.toggle('scrolled', s);
    navbar?.classList.toggle('scrolled', s);
  }, { passive: true });
  /* Product page: header is always scrolled (dark logo) */
  header?.classList.add('scrolled');
})();

/* ─── QA FORM ───────────────────────────────────────────────── */
(function initQaForm() {
  const form  = document.getElementById('pdQaForm');
  const input = document.getElementById('pdQaInput');
  const list  = document.getElementById('pdQaList');
  if (!form || !input || !list) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    const item = document.createElement('div');
    item.className = 'pd-qa-item';
    item.innerHTML = `
      <div class="pd-qa-q">
        <span class="pd-qa-icon">Q</span>
        <p>${text}</p>
      </div>
      <div class="pd-qa-a">
        <span class="pd-qa-icon ans">A</span>
        <p>Cảm ơn câu hỏi của bạn. Chúng tôi sẽ phản hồi trong thời gian sớm nhất.</p>
      </div>
    `;
    list.appendChild(item);
    input.value = '';

    /* Scroll to new item */
    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
})();

/* ─── 13. PDP DATA ACTIONS ────────────────────────────────── */
(function initPdpActions() {
  const addBtn = document.getElementById('pdAddCart');
  const buyBtn = document.querySelector('.pd-btn-buy');
  const wishBtn = document.getElementById('pdWishBtn');
  const qtyEl = document.getElementById('pdQtyVal');
  const priceEl = document.getElementById('pdVariantPrice');
  const metaEl = document.getElementById('pdVariantMeta');
  const container = document.querySelector('.pd-layout');
  if (!container) return;

  const getSelectedVariant = () => {
    const raw = (metaEl?.textContent || '').split('·')[0].trim();
    return raw || 'SKU';
  };

  const toast = (msg) => {
    const node = document.createElement('div');
    node.className = 'pd-toast';
    node.textContent = msg;
    document.body.appendChild(node);
    setTimeout(() => node.classList.add('show'), 20);
    setTimeout(() => {
      node.classList.remove('show');
      setTimeout(() => node.remove(), 260);
    }, 1700);
  };

  const updateCartBadge = (cart) => {
    const total = cart.reduce((sum, i) => sum + Number(i.qty || 0), 0);
    const icon = document.querySelector('.header-icons .icon-btn');
    if (!icon) return;
    let badge = icon.querySelector('.cart-badge');
    if (!badge && total > 0) {
      badge = document.createElement('span');
      badge.className = 'cart-badge';
      icon.appendChild(badge);
    }
    if (badge) badge.textContent = String(total);
  };

  const addToCart = () => {
    const qty = Number(qtyEl?.textContent || 1);
    const productId = container.dataset.productId || '0';
    const key = `${productId}-${getSelectedVariant()}`;
    const cart = JSON.parse(localStorage.getItem('ami_cart') || '[]');
    const found = cart.find(i => i.key === key);
    if (found) found.qty += qty;
    else cart.push({ key, productId, qty, price: priceEl?.textContent || '' });
    localStorage.setItem('ami_cart', JSON.stringify(cart));
    updateCartBadge(cart);
    toast('Đã thêm vào giỏ hàng');
  };

  addBtn?.addEventListener('click', addToCart);
  buyBtn?.addEventListener('click', () => {
    addToCart();
    window.location.href = '/cart/';
  });

  wishBtn?.addEventListener('click', () => {
    const productId = container.dataset.productId || '0';
    const wl = new Set(JSON.parse(localStorage.getItem('ami_wishlist') || '[]'));
    wl.add(productId);
    localStorage.setItem('ami_wishlist', JSON.stringify([...wl]));
    toast('Đã thêm vào danh sách yêu thích');
  });
})();