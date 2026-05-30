/**
 * AMI PERFUMERY — ai_sections.js
 * ================================
 * Quản lý các section AI Recommendation:
 * 1. "Dành cho bạn" (Recommended For You)
 * 2. "Sản phẩm đã xem gần đây" (Recently Viewed)
 *
 * Tự động track view khi user ở trang chi tiết sản phẩm.
 * Hoạt động cho cả Guest (session) và Registered User (DB).
 */

(function () {
  'use strict';

  /* ─────────────────────────────────────────────────────
     HELPERS
  ───────────────────────────────────────────────────── */
  function getCsrf() {
    const c = document.cookie.split(';').find(x => x.trim().startsWith('csrftoken='));
    return c ? decodeURIComponent(c.trim().slice('csrftoken='.length)) : '';
  }

  function escHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /** Tạo product card HTML — đồng nhất style với existing cards */
  function buildProductCard(item) {
    const card = document.createElement('a');
    card.href = '/product/' + item.id + '/';
    card.className = 'ami-ai-card';
    card.setAttribute('data-ai-source', item.source || 'ai');

    card.innerHTML = `
      <div class="ami-ai-card__media">
        <img src="${escHtml(item.primary_image)}"
             alt="${escHtml(item.name)}"
             loading="lazy"
             onerror="this.src='/static/app/img/placeholder.jpg'">
      </div>
      <div class="ami-ai-card__body">
        <p class="ami-ai-card__brand">${escHtml(item.brand)}</p>
        <h3 class="ami-ai-card__name">${escHtml(item.name)}</h3>
        <p class="ami-ai-card__price">${escHtml(item.price)}</p>
      </div>`;

    // Track click
    card.addEventListener('click', () => {
      fetch('/api/ai/track-click/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body:    JSON.stringify({ product_id: item.id, source: item.source || 'ai_section' }),
      }).catch(() => {});
    });

    return card;
  }

  /** Render danh sách cards vào container */
  function renderSection(sectionEl, trackEl, products, source) {
    if (!sectionEl || !trackEl || !products || !products.length) {
      if (sectionEl) sectionEl.style.display = 'none';
      return;
    }
    trackEl.innerHTML = '';
    products.forEach(item => {
      item.source = source;
      trackEl.appendChild(buildProductCard(item));
    });
    sectionEl.style.display = 'block';

    // Arrow scroll
    const leftBtn  = sectionEl.querySelector('[data-scroll-left]');
    const rightBtn = sectionEl.querySelector('[data-scroll-right]');
    const outer    = trackEl.parentElement;
    if (leftBtn && outer)
      leftBtn.addEventListener('click', () => outer.scrollBy({ left: -320, behavior: 'smooth' }));
    if (rightBtn && outer)
      rightBtn.addEventListener('click', () => outer.scrollBy({ left:  320, behavior: 'smooth' }));
  }


  /* ═══════════════════════════════════════════════════
     1. TRACK VIEW — trang chi tiết sản phẩm
  ══════════════════════════════════════════════════ */
  const productMatch = window.location.pathname.match(/\/product\/(\d+)\//);
  if (productMatch) {
    const productId  = parseInt(productMatch[1]);
    const enterTime  = Date.now();

    // Lưu vào session (cho guest_ai_profile context chatbot)
    sessionStorage.setItem('current_product_id', productId);

    // Ghi nhận view ngay khi load trang
    fetch('/api/ai/track-view/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body:    JSON.stringify({ product_id: productId, time_spent: 0 }),
    }).catch(() => {});

    // Ghi nhận time_spent khi rời trang
    window.addEventListener('beforeunload', () => {
      const secs = Math.round((Date.now() - enterTime) / 1000);
      navigator.sendBeacon('/api/ai/track-view/',
        new Blob([JSON.stringify({
          product_id: productId,
          time_spent: secs,
        })], { type: 'application/json' })
      );
    });
  }


  /* ═══════════════════════════════════════════════════
     2. "DÀNH CHO BẠN" — Home page + Category page
  ══════════════════════════════════════════════════ */
  const forYouSection = document.getElementById('aiForYouSection');
  const forYouTrack   = document.getElementById('aiForYouTrack');

  if (forYouSection && forYouTrack) {
    const currentId = productMatch ? parseInt(productMatch[1]) : null;

    fetch('/api/recommend/personal/' + (currentId ? `?current=${currentId}` : ''))
      .then(r => r.json())
      .then(data => {
        if (data.ok && data.products && data.products.length) {
          // Đổi tiêu đề section tùy loại
          const titleEl = forYouSection.querySelector('.ami-ai-section__title');
          if (titleEl) {
            titleEl.textContent = data.type === 'personalized'
              ? '✨ Dành riêng cho bạn'
              : '🔥 Sản phẩm nổi bật';
          }
          renderSection(forYouSection, forYouTrack, data.products, 'for_you');
        } else {
          forYouSection.style.display = 'none';
        }
      })
      .catch(() => { if (forYouSection) forYouSection.style.display = 'none'; });
  }


  /* ═══════════════════════════════════════════════════
     3. "SẢN PHẨM ĐÃ XEM GẦN ĐÂY" — Home + Product page
  ══════════════════════════════════════════════════ */
  const recentSection = document.getElementById('aiRecentSection');
  const recentTrack   = document.getElementById('aiRecentTrack');

  if (recentSection && recentTrack) {
    const excludeId = productMatch ? parseInt(productMatch[1]) : null;
    const url = '/api/ai/recently-viewed/' + (excludeId ? `?exclude=${excludeId}` : '');

    fetch(url)
      .then(r => r.json())
      .then(data => {
        if (data.ok && data.products && data.products.length >= 2) {
          renderSection(recentSection, recentTrack, data.products, 'recently_viewed');
        } else {
          recentSection.style.display = 'none';
        }
      })
      .catch(() => { if (recentSection) recentSection.style.display = 'none'; });
  }


  /* ═══════════════════════════════════════════════════
     4. CHATBOT — truyền session_id để track conversation
  ══════════════════════════════════════════════════ */
  // Tạo/lấy chat session ID cho lần mở web này
  if (!sessionStorage.getItem('ami_chat_session')) {
    sessionStorage.setItem('ami_chat_session', 'cs_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8));
  }

  // Expose toàn cục để chat.js dùng
  window.amiChatSessionId = sessionStorage.getItem('ami_chat_session');

})();