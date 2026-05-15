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

  const xPercent = (tx / rect.width) * 100;
  const yPercent = (ty / rect.height) * 100;

  img.style.transformOrigin = `${xPercent}% ${yPercent}%`;

  img.style.transform = `scale(1.35)`;
});

  wrap.addEventListener('mouseleave', () => {
  isActive = false;

  img.style.transform = 'scale(1)';
  img.style.transformOrigin = 'center center';

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
/* ═══════════════════════════════════════════════════════
   Q&A JavaScript — Thêm vào product.js
   (Thay thế phần "QA FORM" cũ)
   ═══════════════════════════════════════════════════════ */

/* ─── Toggle form đặt câu hỏi ─────────────────────── */
function toggleAskForm() {
    const box = document.getElementById("qaAskBox");
    const btn = document.getElementById("qaAskToggleBtn");
    if (!box) return;
    const isOpen = box.classList.contains("open");
    box.classList.toggle("open", !isOpen);
    if (btn) {
        btn.innerHTML = isOpen
            ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Đặt câu hỏi`
            : `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Đóng`;
    }
    if (!isOpen) {
        setTimeout(() => document.getElementById("pdQaInput")?.focus(), 300);
    }
}

/* ─── Toggle form reply inline ─────────────────────── */
function toggleReplyForm(qid) {
    const form = document.getElementById(`qa-reply-${qid}`);
    if (!form) return;
    const hidden = form.hasAttribute("hidden");
    form.toggleAttribute("hidden", !hidden);
    if (hidden) {
        setTimeout(() => document.getElementById(`qa-reply-input-${qid}`)?.focus(), 50);
        // Điền initials người dùng vào avatar
        const miniAvatar = form.querySelector(".reply-mini-avatar");
        if (miniAvatar) {
            const accountName = document.body.dataset.accountName || "?";
            miniAvatar.textContent = accountName.slice(0, 1).toUpperCase();
        }
    }
}

/* ─── Submit câu hỏi mới ───────────────────────────── */
const qaForm = document.getElementById("pdQaForm");
if (qaForm) {
    qaForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("pdQaInput");
        const content = (input?.value || "").trim();
        if (!content) { showQaToast("Vui lòng nhập câu hỏi", "warn"); return; }

        const productId = document.querySelector(".pd-layout")?.dataset?.productId;
        const submitBtn = qaForm.querySelector(".pd-qa-submit");
        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Đang gửi…"; }

        const formData = new FormData();
        formData.append("product_id", productId);
        formData.append("content", content);

        try {
            const res = await fetch("/submit-question/", { method: "POST", body: formData });
            const data = await res.json();
            if (data.need_login) { window.location.href = "/auth/"; return; }
            if (data.ok) {
                showQaToast("Câu hỏi đã được gửi. Chuyên viên sẽ phản hồi sớm nhất!", "success");
                input.value = "";
                toggleAskForm();
                // Thêm card mới vào đầu list
                prependQuestionCard(data.question);
                // Cập nhật số đếm
                updateQaCount(1);
            }
        } catch (err) {
            showQaToast("Có lỗi xảy ra. Vui lòng thử lại.", "error");
        } finally {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Gửi câu hỏi"; }
        }
    });
}

/* ─── Submit reply (phản hồi sau câu trả lời admin) ── */
/* ═══════════════════════════════════════════════════════
   Hàm submitReply — thay thế trong qa_script.js
   Gửi parent_id lên /submit-question/ để lưu câu hỏi tiếp
   ═══════════════════════════════════════════════════════ */

async function submitReply(qid) {
    const textarea = document.getElementById(`qa-reply-input-${qid}`);
    const content = (textarea?.value || "").trim();
    if (!content) {
        showQaToast("Vui lòng nhập nội dung phản hồi", "warn");
        return;
    }

    const productId = document.querySelector(".pd-layout")?.dataset?.productId;
    const submitBtn = document.querySelector(`#qa-reply-${qid} .qa-reply-submit-btn`);

    // Hiện trạng thái loading
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span style="opacity:.6">Đang gửi…</span>`;
    }

    const formData = new FormData();
    formData.append("product_id", productId);
    formData.append("content", content);
    formData.append("parent_id", qid);   // <-- gửi parent_id là id của câu hỏi gốc

    try {
        const res = await fetch("/submit-question/", {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        if (data.need_login) {
            window.location.href = "/auth/";
            return;
        }

        if (data.ok) {
            // Đóng form reply
            toggleReplyForm(qid);
            textarea.value = "";

            // Hiển thị phản hồi vừa gửi ngay dưới answer của admin
            appendFollowUpReply(qid, data.question);

            showQaToast("Phản hồi đã được gửi. Chuyên viên sẽ xem xét sớm nhất!", "success");
        } else {
            showQaToast(data.message || "Có lỗi xảy ra.", "error");
        }

    } catch (err) {
        console.error(err);
        showQaToast("Có lỗi xảy ra. Vui lòng thử lại.", "error");
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                Gửi`;
        }
    }
}


/* ─── Hiển thị câu hỏi tiếp theo ngay dưới answer của admin ── */
function appendFollowUpReply(qid, q) {
    const card = document.getElementById(`qa-card-${qid}`);
    if (!card) return;

    const initial = (q.name || "K").slice(0, 1).toUpperCase();

    // Tạo block follow-up
    const block = document.createElement("div");
    block.className = "qa-followup-block";
    block.style.animation = "tabFadeIn .35s ease";
    block.innerHTML = `
      <div class="qa-followup-connector"></div>
      <div class="pd-qa-question qa-followup-question">
        <div class="pd-qa-avatar q-avatar">${initial}</div>
        <div class="pd-qa-content">
          <div class="pd-qa-top">
            <div class="qa-user-info">
              <span class="qa-username">${q.name}</span>
              <span class="pd-qa-date">${q.created_at}</span>
              <span class="qa-followup-label">Câu hỏi tiếp theo</span>
            </div>
            <span class="pd-qa-status pending">
              <span class="pending-dot"></span> Đang chờ
            </span>
          </div>
          <p class="pd-qa-text">${q.content}</p>
        </div>
      </div>
    `;

    // Chèn trước form reply (hoặc cuối card)
    const replyForm = document.getElementById(`qa-reply-${qid}`);
    if (replyForm) {
        card.insertBefore(block, replyForm);
    } else {
        card.appendChild(block);
    }
}

/* ─── Thêm card câu hỏi mới vào DOM ───────────────── */
function prependQuestionCard(q) {
    const list = document.getElementById("pdQaList");
    if (!list) return;
    // Xóa empty state nếu có
    const empty = list.querySelector(".qa-empty-state");
    if (empty) empty.remove();

    const initial = (q.name || "K").slice(0, 1).toUpperCase();
    const card = document.createElement("div");
    card.className = "pd-qa-card";
    card.id = `qa-card-${q.id}`;
    card.style.animation = "tabFadeIn .4s ease";
    card.innerHTML = `
      <div class="pd-qa-question">
        <div class="pd-qa-avatar q-avatar">${initial}</div>
        <div class="pd-qa-content">
          <div class="pd-qa-top">
            <div class="qa-user-info">
              <span class="qa-username">${q.name}</span>
              <span class="pd-qa-date">${q.created_at}</span>
            </div>
            <span class="pd-qa-status pending">
              <span class="pending-dot"></span> Đang chờ
            </span>
          </div>
          <p class="pd-qa-text">${q.content}</p>
        </div>
      </div>
      <div class="qa-no-answer-hint">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
        Câu hỏi đang chờ phản hồi từ chuyên viên tư vấn.
      </div>
    `;
    list.prepend(card);
}

/* ─── Cập nhật số đếm badge ────────────────────────── */
function updateQaCount(delta) {
    const badge = document.querySelector(".qa-count-badge");
    if (!badge) return;
    const match = badge.textContent.match(/\d+/);
    const current = match ? parseInt(match[0]) : 0;
    badge.textContent = `${current + delta} câu hỏi`;
}

/* ─── Toast notification ───────────────────────────── */
function showQaToast(msg, type = "success") {
    const existing = document.getElementById("qaToast");
    if (existing) existing.remove();
    const colors = {
        success: { bg: "#4B672D", text: "#fff" },
        warn:    { bg: "#f57f17", text: "#fff" },
        error:   { bg: "#c62828", text: "#fff" },
    };
    const c = colors[type] || colors.success;
    const toast = document.createElement("div");
    toast.id = "qaToast";
    toast.style.cssText = `
        position:fixed; bottom:28px; left:50%; transform:translateX(-50%) translateY(20px);
        background:${c.bg}; color:${c.text}; padding:12px 24px; border-radius:40px;
        font-family:'Jost',sans-serif; font-size:13px; font-weight:500; letter-spacing:.5px;
        box-shadow:0 8px 28px rgba(0,0,0,.18); z-index:9999;
        opacity:0; transition:opacity .3s, transform .3s;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateX(-50%) translateY(0)";
    });
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(-50%) translateY(10px)";
        setTimeout(() => toast.remove(), 350);
    }, 3200);
}

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


/* ─── 13. Reviews AJAX ─────────────────────────────────────── */
(function initReviews(){
  const submitBtn = document.getElementById('pdSubmitReview');
  const textarea = document.getElementById('pdReviewContent');
  const starBtns = [...document.querySelectorAll('.pd-star-btn')];
  const list = document.getElementById('pdReviewList');
  const root = document.querySelector('.pd-layout');
  if(!submitBtn || !textarea || !root) return;

  const productId = root.dataset.productId;
  const draftKey = `review_draft_${productId}`;
  let rating = 5;
  textarea.value = sessionStorage.getItem(draftKey) || '';

  const paintStars = () => starBtns.forEach(btn => btn.classList.toggle('active', Number(btn.dataset.star) <= rating));
  paintStars();
  starBtns.forEach(btn => btn.addEventListener('click', ()=>{ rating = Number(btn.dataset.star); paintStars(); }));
  textarea.addEventListener('input', ()=> sessionStorage.setItem(draftKey, textarea.value));

  const toast = (msg) => {
    const el=document.createElement('div'); el.className='pd-lux-toast'; el.textContent=msg; document.body.appendChild(el);
    setTimeout(()=>el.classList.add('show'),10); setTimeout(()=>{el.classList.remove('show'); setTimeout(()=>el.remove(),300)},2600);
  };

  submitBtn.addEventListener('click', async ()=>{
    const content = textarea.value.trim();
    if(!content){ toast('Vui lòng nhập nội dung đánh giá.'); return; }
    const fd = new FormData(); fd.append('product_id', productId); fd.append('rating', rating); fd.append('content', content);
    const res = await fetch('/submit-review/', {method:'POST', body:fd});
    const data = await res.json();
    if(!data.ok && data.need_login){
      sessionStorage.setItem(draftKey, content);
      sessionStorage.setItem(`${draftKey}_rating`, String(rating));
      window.location.href = `/auth/?next=${encodeURIComponent(window.location.pathname + '#tab-reviews')}`;
      return;
    }
    if(!data.ok){ toast(data.message || 'Không thể gửi đánh giá'); return; }

    const rv=data.review;
    const card = document.createElement('article');
    card.className='pd-review-card';
    card.innerHTML = `<div class="pd-rv-head"><div class="pd-rv-avatar">${rv.name[0].toUpperCase()}</div><div><strong class="pd-rv-name"></strong><span class="pd-rv-stars">${'★'.repeat(rv.rating)}${'☆'.repeat(5-rv.rating)}</span></div><time class="pd-rv-date">${rv.created_at}</time></div><p class="pd-rv-text"></p><small class="pd-rv-label">${rv.label || ''}</small>`;
    card.querySelector('.pd-rv-name').textContent = rv.name;
    card.querySelector('.pd-rv-text').textContent = rv.content;
    list.prepend(card);
    textarea.value=''; sessionStorage.removeItem(draftKey);
    toast(data.message || 'Cảm ơn bạn đã chia sẻ trải nghiệm cùng Ami Perfume.');
  });

  const savedRating = sessionStorage.getItem(`${draftKey}_rating`);
  if(savedRating){ rating = Number(savedRating) || 5; paintStars(); sessionStorage.removeItem(`${draftKey}_rating`); }
})();