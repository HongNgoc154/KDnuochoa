/**
 * AMI PERFUMERY — Chat Widget JS
 * File: app/static/app/js/chat.js
 *
 * Chức năng:
 * - Toggle mở/đóng chat panel
 * - Gửi tin nhắn → POST /api/chatbot/
 * - Hiển thị bubble bot + user
 * - Hiển thị product card có ảnh (từ suggestions trả về bởi API)
 * - Quick reply buttons
 * - Typing indicator
 * - Multi-turn conversation history
 */

(function () {
  'use strict';

  /* ── DOM refs ── */
  const chat         = document.getElementById('amiChat');
  const trigger      = document.getElementById('chatTrigger');
  const panel        = document.getElementById('chatPanel');
  const closeBtn     = document.getElementById('chatClose');
  const messages     = document.getElementById('chatMessages');
  const inputEl      = document.getElementById('chatInput');
  const sendBtn      = document.getElementById('chatSend');
  const typing       = document.getElementById('chatTyping');
  const badge        = document.getElementById('chatBadge');
  const quickReplies = document.getElementById('chatQuickReplies');

  if (!chat || !trigger) return;

  /* ── State ── */
  let isOpen      = false;
  let isLoading   = false;
  let chatHistory = [];
  let hasUnread   = false;

  /* ─────────────────────────────────────────
     TOGGLE
  ───────────────────────────────────────── */
  function openChat() {
    isOpen = true;
    chat.classList.add('ami-chat--open');
    panel.removeAttribute('aria-hidden');
    trigger.querySelector('.ami-chat__trigger-icon--close').removeAttribute('hidden');
    trigger.querySelector('.ami-chat__trigger-icon--chat').setAttribute('hidden', '');
    badge.setAttribute('hidden', '');
    hasUnread = false;
    setTimeout(() => inputEl.focus(), 320);
    scrollToBottom();
  }

  function closeChat() {
    isOpen = false;
    chat.classList.remove('ami-chat--open');
    panel.setAttribute('aria-hidden', 'true');
    trigger.querySelector('.ami-chat__trigger-icon--chat').removeAttribute('hidden');
    trigger.querySelector('.ami-chat__trigger-icon--close').setAttribute('hidden', '');
  }

  trigger.addEventListener('click', () => isOpen ? closeChat() : openChat());
  closeBtn.addEventListener('click', closeChat);

  document.addEventListener('click', (e) => {
    if (isOpen && !chat.contains(e.target)) closeChat();
  });

  /* ─────────────────────────────────────────
     SCROLL
  ───────────────────────────────────────── */
  function scrollToBottom() {
    requestAnimationFrame(() => { messages.scrollTop = messages.scrollHeight; });
  }

  /* ─────────────────────────────────────────
     MESSAGES
  ───────────────────────────────────────── */
  function appendUserMsg(text) {
    const row = document.createElement('div');
    row.className = 'ami-chat__msg ami-chat__msg--user';
    row.innerHTML = `<div class="ami-chat__bubble">${escHtml(text)}</div>`;
    messages.appendChild(row);
    scrollToBottom();
  }

  function appendBotMsg(text) {
    const row = document.createElement('div');
    row.className = 'ami-chat__msg ami-chat__msg--bot';
    const formatted = escHtml(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    row.innerHTML = `<div class="ami-chat__bubble">${formatted}</div>`;
    messages.appendChild(row);
    scrollToBottom();
  }

  /* ─────────────────────────────────────────
     PRODUCT CARDS — dùng image + price từ API
  ───────────────────────────────────────── */
  function appendProductCards(suggestions) {
    if (!suggestions || !suggestions.length) return;

    const products = suggestions.filter(s => s.type === 'product');
    if (!products.length) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'ami-chat__msg ami-chat__msg--bot';

    const strip = document.createElement('div');
    strip.className = 'ami-chat__suggestions';

    products.forEach(s => {
      const card = document.createElement('a');
      card.className = 'ami-chat__product-card';
      card.href = `/product/${s.id}/`;
      card.target = '_blank';
      card.rel = 'noopener';

      // Ảnh sản phẩm
      const imgHtml = s.image
        ? `<img class="ami-chat__product-img" src="${escAttr(s.image)}" alt="${escAttr(s.name)}" loading="lazy" onerror="this.style.display='none'">`
        : `<div class="ami-chat__product-img-placeholder">🌸</div>`;

      // Giá
      const priceHtml = s.price
        ? `<p class="ami-chat__product-price">${escHtml(s.price)}</p>`
        : '';

      card.innerHTML = `
        ${imgHtml}
        <div class="ami-chat__product-info">
          <p class="ami-chat__product-brand">${escHtml(s.brand || '')}</p>
          <p class="ami-chat__product-name">${escHtml(s.name || '')}</p>
          ${priceHtml}
        </div>
      `;
      strip.appendChild(card);
    });

    if (!strip.children.length) return;
    wrapper.appendChild(strip);
    messages.appendChild(wrapper);
    scrollToBottom();
  }

  /* ─────────────────────────────────────────
     GỬI TIN NHẮN
  ───────────────────────────────────────── */
  async function sendMessage(text) {
    text = (text || inputEl.value).trim();
    if (!text || isLoading) return;

    // Ẩn quick replies sau lần gửi đầu
    if (quickReplies && quickReplies.parentNode) quickReplies.remove();

    appendUserMsg(text);
    inputEl.value = '';
    sendBtn.disabled = true;
    isLoading = true;

    typing.removeAttribute('hidden');
    scrollToBottom();

    try {
      const res = await fetch('/api/chatbot/', {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  getCsrf(),
        },
        body: JSON.stringify({ message: text, history: chatHistory }),
      });

      const data = await res.json();
      typing.setAttribute('hidden', '');

      if (data.ok) {
        chatHistory = data.history || [];
        appendBotMsg(data.reply || 'Xin lỗi, tôi chưa hiểu. Bạn có thể nói rõ hơn không?');
        appendProductCards(data.suggestions);

        if (!isOpen) {
          hasUnread = true;
          badge.removeAttribute('hidden');
        }
      } else {
        appendBotMsg('Có lỗi xảy ra. Vui lòng thử lại nhé! 🙏');
      }
    } catch (err) {
      typing.setAttribute('hidden', '');
      appendBotMsg('Mất kết nối. Vui lòng kiểm tra internet và thử lại.');
      console.error('[AmiChat]', err);
    }

    isLoading = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }

  /* ─────────────────────────────────────────
     EVENTS
  ───────────────────────────────────────── */
  sendBtn.addEventListener('click', () => sendMessage());
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // Quick reply & dynamic suggestion clicks
  messages.addEventListener('click', (e) => {
    const btn = e.target.closest('.ami-chat__quick-btn');
    if (btn && btn.dataset.msg) sendMessage(btn.dataset.msg);
  });

  /* ─────────────────────────────────────────
     BADGE — hiện sau 3s để thu hút chú ý
  ───────────────────────────────────────── */
  setTimeout(() => {
    if (!isOpen && !hasUnread) {
      badge.removeAttribute('hidden');
      hasUnread = true;
    }
  }, 3000);

  /* ─────────────────────────────────────────
     UTILS
  ───────────────────────────────────────── */
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function escAttr(str) {
    return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function getCsrf() {
    const c = document.cookie.split(';').find(x => x.trim().startsWith('csrftoken='));
    return c ? decodeURIComponent(c.trim().slice('csrftoken='.length)) : '';
  }

})();