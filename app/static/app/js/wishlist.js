/* =============================================================
   Ami Perfumery — wishlist.js  (PHIÊN BẢN HOÀN CHỈNH)
   Include sau product.js / main.js trên mọi trang
   ============================================================= */

(function WishlistSystem() {
  'use strict';

  const TOGGLE_URL = '/toggle-favorite/';
  const STATUS_URL = (id) => `/wishlist-status/${id}/`;
  const AUTH_URL   = '/auth/';

  function isLoggedIn() {
    return (document.body.dataset.accountName || '').trim() !== '';
  }

  function redirectToLogin() {
    window.location.href = `${AUTH_URL}?next=${encodeURIComponent(window.location.href)}`;
  }

  function getCSRF() {
    return document.cookie.split('; ')
      .find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
  }

  /* ── Toast ── */
  function toast(msg, liked) {
    const old = document.getElementById('_wt');
    if (old) old.remove();
    const el = document.createElement('div');
    el.id = '_wt';
    el.style.cssText = `
      position:fixed;bottom:28px;left:50%;
      transform:translateX(-50%) translateY(12px);
      background:${liked ? '#4B672D' : '#555'};
      color:#fff;padding:11px 24px;border-radius:40px;
      font-family:'Jost',sans-serif;font-size:13px;font-weight:500;
      box-shadow:0 8px 24px rgba(0,0,0,.18);z-index:9999;
      opacity:0;transition:opacity .25s,transform .25s;pointer-events:none;
    `;
    el.textContent = msg;
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

  /* ── Cập nhật badge ── */
  function setBadge(count) {
    const n = Math.max(0, count);
    const sb = document.querySelector('.nav-item[data-tab="wishlist"] .nav-badge');
    if (sb) sb.textContent = String(n);
    document.querySelectorAll('[data-wishlist-badge]').forEach(b => b.textContent = String(n));
  }

  /* ── Gọi API ── */
  async function callToggle(productId) {
    const fd = new FormData();
    fd.append('product_id', productId);
    const res = await fetch(TOGGLE_URL, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRF() },
      body: fd,
    });
    return res.json();
  }

  /* ════════════════════════════════════════════════
     1. PRODUCT DETAIL — #pdWishBtn
  ════════════════════════════════════════════════ */
  function initDetailWishlist() {
    const btn   = document.getElementById('pdWishBtn');
    const heart = document.getElementById('pdWishHeart');
    const label = btn?.querySelector('.pd-wish-label');
    if (!btn || !heart) return;

    const productId = document.querySelector('.pd-layout')?.dataset?.productId;
    if (!productId) return;

    function setLiked(liked) {
      btn.classList.toggle('is-liked', liked);
      btn.setAttribute('aria-pressed', String(liked));
      heart.textContent = liked ? '♥' : '♡';
      heart.style.color = liked ? '#c0392b' : '';
      if (label) label.textContent = liked ? 'Đã yêu thích' : 'Yêu thích';
    }

    // Load trạng thái ban đầu từ server
    if (isLoggedIn()) {
      fetch(STATUS_URL(productId))
        .then(r => r.json())
        .then(d => setLiked(!!d.liked))
        .catch(() => {});
    }

    btn.addEventListener('click', async () => {
      if (!isLoggedIn()) { redirectToLogin(); return; }

      const wasLiked = btn.classList.contains('is-liked');
      setLiked(!wasLiked); // Optimistic UI

      // Animation
      btn.classList.remove('bursting', 'bounce');
      void btn.offsetWidth;
      btn.classList.add('bursting', 'bounce');
      setTimeout(() => btn.classList.remove('bursting', 'bounce'), 580);

      try {
        const data = await callToggle(productId);
        if (data.need_login) { redirectToLogin(); return; }
        if (data.ok) {
          const liked = data.action === 'added';
          setLiked(liked);
          if (data.wishlist_count !== undefined) setBadge(data.wishlist_count);
          toast(data.message, liked);
        } else {
          setLiked(wasLiked); // rollback
          toast(data.message || 'Có lỗi xảy ra.', false);
        }
      } catch {
        setLiked(wasLiked); // rollback
      }
    });
  }

  /* ════════════════════════════════════════════════
     2. CARD SẢN PHẨM — .favorite-btn[data-product-id]
  ════════════════════════════════════════════════ */
  function initCardWishlists() {
    const grid = document.querySelector('.product-grid');
    if (!grid) return;

    // Load trạng thái tất cả card
    if (isLoggedIn()) {
      grid.querySelectorAll('.favorite-btn[data-product-id]').forEach(btn => {
        fetch(STATUS_URL(btn.dataset.productId))
          .then(r => r.json())
          .then(d => { if (d.liked) setCardLiked(btn, true); })
          .catch(() => {});
      });
    }

    // Click delegate
    grid.addEventListener('click', async (e) => {
      const btn = e.target.closest('.favorite-btn[data-product-id]');
      if (!btn) return;
      e.stopPropagation();

      if (!isLoggedIn()) { redirectToLogin(); return; }

      const productId = btn.dataset.productId;
      const wasLiked  = btn.classList.contains('is-liked');
      setCardLiked(btn, !wasLiked); // Optimistic

      try {
        const data = await callToggle(productId);
        if (data.need_login) { redirectToLogin(); return; }
        if (data.ok) {
          const liked = data.action === 'added';
          setCardLiked(btn, liked);
          if (data.wishlist_count !== undefined) setBadge(data.wishlist_count);
          toast(data.message, liked);
        } else {
          setCardLiked(btn, wasLiked); // rollback
        }
      } catch {
        setCardLiked(btn, wasLiked);
      }
    });
  }

  function setCardLiked(btn, liked) {
    btn.classList.toggle('is-liked', liked);
    btn.setAttribute('aria-pressed', String(liked));
    const core = btn.querySelector('.heart-core');
    if (core) {
      core.textContent = liked ? '♥' : '♡';
      core.style.color = liked ? '#c0392b' : '';
    }
    btn.classList.remove('bursting', 'bounce');
    void btn.offsetWidth;
    btn.classList.add('bursting', 'bounce');
    setTimeout(() => btn.classList.remove('bursting', 'bounce'), 520);
  }

  /* ── Bootstrap ── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initDetailWishlist();
      initCardWishlists();
    });
  } else {
    initDetailWishlist();
    initCardWishlists();
  }

})();