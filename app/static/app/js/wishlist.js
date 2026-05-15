/* =============================================================
   WISHLIST — wishlist.js
   Dùng chung cho tất cả trang: product detail, category, home
   Include file này sau main.js / product.js
   ============================================================= */

(function WishlistSystem() {
  'use strict';

  const TOGGLE_URL  = '/toggle-wishlist/';
  const STATUS_URL  = (id) => `/wishlist-status/${id}/`;
  const AUTH_URL    = '/auth/';

  /* ── Kiểm tra đã đăng nhập chưa ── */
  function isLoggedIn() {
    return (document.body.dataset.accountName || '').trim() !== '';
  }

  /* ── Redirect đến trang đăng nhập, sau khi login quay lại ── */
  function redirectToLogin() {
    window.location.href = `${AUTH_URL}?next=${encodeURIComponent(window.location.href)}`;
  }

  /* ── Toast nhẹ ── */
  function showWishToast(msg, liked) {
    const old = document.getElementById('_wishToast');
    if (old) old.remove();
    const t = document.createElement('div');
    t.id = '_wishToast';
    t.style.cssText = `
      position:fixed;bottom:28px;left:50%;
      transform:translateX(-50%) translateY(16px);
      background:${liked ? '#4B672D' : '#5a5a5a'};
      color:#fff;padding:11px 22px;border-radius:40px;
      font-family:'Jost',sans-serif;font-size:13px;font-weight:500;
      box-shadow:0 8px 28px rgba(0,0,0,.18);z-index:9999;
      opacity:0;transition:opacity .28s,transform .28s;pointer-events:none;
    `;
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(() => {
      t.style.opacity = '1';
      t.style.transform = 'translateX(-50%) translateY(0)';
    });
    setTimeout(() => {
      t.style.opacity = '0';
      t.style.transform = 'translateX(-50%) translateY(10px)';
      setTimeout(() => t.remove(), 300);
    }, 2600);
  }

  /* ── Cập nhật badge "Yêu thích" trong sidebar profile ── */
  function updateWishBadge(delta) {
    const badge = document.querySelector('.nav-item[data-tab="wishlist"] .nav-badge');
    if (!badge) return;
    const current = parseInt(badge.textContent) || 0;
    const next = Math.max(0, current + delta);
    badge.textContent = String(next);
  }

  /* ── Gọi API toggle ── */
  async function callToggle(productId) {
    const fd = new FormData();
    fd.append('product_id', productId);
    const res  = await fetch(TOGGLE_URL, { method: 'POST', body: fd });
    return res.json();
  }

  /* ════════════════════════════════════════════════
     1. PRODUCT DETAIL PAGE — #pdWishBtn
     ════════════════════════════════════════════════ */
  function initProductDetailWishlist() {
    const btn   = document.getElementById('pdWishBtn');
    const heart = document.getElementById('pdWishHeart');
    const label = btn?.querySelector('.pd-wish-label');
    if (!btn || !heart) return;

    const productId = document.querySelector('.pd-layout')?.dataset?.productId;
    if (!productId) return;

    /* Set trạng thái ban đầu */
    function setLiked(liked) {
      btn.classList.toggle('is-liked', liked);
      btn.setAttribute('aria-pressed', String(liked));
      heart.textContent  = liked ? '♥' : '♡';
      heart.style.color  = liked ? '#c0392b' : '';
      if (label) label.textContent = liked ? 'Đã yêu thích' : 'Yêu thích';
    }

    /* Load trạng thái từ server */
    if (isLoggedIn()) {
      fetch(STATUS_URL(productId))
        .then(r => r.json())
        .then(d => setLiked(d.liked))
        .catch(() => {});
    }

    /* Click */
    btn.addEventListener('click', async () => {
      if (!isLoggedIn()) { redirectToLogin(); return; }

      /* Optimistic UI */
      const wasLiked = btn.classList.contains('is-liked');
      setLiked(!wasLiked);

      try {
        const data = await callToggle(productId);
        if (data.need_login) { redirectToLogin(); return; }
        if (data.ok) {
          const liked = data.action === 'added';
          setLiked(liked);
          updateWishBadge(liked ? 1 : -1);
          showWishToast(data.message, liked);
        } else {
          setLiked(wasLiked); /* rollback */
        }
      } catch {
        setLiked(wasLiked); /* rollback */
      }
    });
  }

  /* ════════════════════════════════════════════════
     2. CARD SẢN PHẨM — .favorite-btn trên category/home
        Mỗi card có data-product-id="{{ item.id }}"
     ════════════════════════════════════════════════ */
  function initCardWishlists() {
    const grid = document.querySelector('.product-grid');
    if (!grid) return;

    /* Load trạng thái tất cả card nếu đã đăng nhập */
    if (isLoggedIn()) {
      grid.querySelectorAll('.favorite-btn[data-product-id]').forEach(btn => {
        const pid = btn.dataset.productId;
        fetch(STATUS_URL(pid))
          .then(r => r.json())
          .then(d => { if (d.liked) setCardLiked(btn, true); })
          .catch(() => {});
      });
    }

    /* Delegate click */
    grid.addEventListener('click', async (e) => {
      const btn = e.target.closest('.favorite-btn');
      if (!btn) return;
      e.stopPropagation(); /* không trigger card click */

      if (!isLoggedIn()) { redirectToLogin(); return; }

      const productId = btn.dataset.productId;
      if (!productId) return;

      const wasLiked = btn.classList.contains('is-liked');
      setCardLiked(btn, !wasLiked); /* Optimistic */

      try {
        const data = await callToggle(productId);
        if (data.need_login) { redirectToLogin(); return; }
        if (data.ok) {
          const liked = data.action === 'added';
          setCardLiked(btn, liked);
          updateWishBadge(liked ? 1 : -1);
          showWishToast(data.message, liked);
        } else {
          setCardLiked(btn, wasLiked); /* rollback */
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
    /* Animation */
    btn.classList.remove('bursting', 'bounce');
    void btn.offsetWidth;
    btn.classList.add('bursting', 'bounce');
    setTimeout(() => btn.classList.remove('bursting', 'bounce'), 520);
  }

  /* ── Bootstrap ── */
  document.addEventListener('DOMContentLoaded', () => {
    initProductDetailWishlist();
    initCardWishlists();
  });

  /* Nếu DOM đã sẵn sàng (script load sau DOMContentLoaded) */
  if (document.readyState !== 'loading') {
    initProductDetailWishlist();
    initCardWishlists();
  }

})();