(() => {
  /* ── Reveal khi scroll vào màn hình ── */
  const revealEls = [...document.querySelectorAll('.reveal')];
  if (revealEls.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const delayAttr = el.style.animationDelay || '0ms';
        const ms = parseInt(delayAttr) || 0;
        setTimeout(() => el.classList.add('in-view'), ms);
        observer.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -5% 0px' });
    revealEls.forEach((el) => observer.observe(el));
  }

  /* ── Tilt 3D nhẹ khi hover card ── */
  document.querySelectorAll('.brand-card').forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width - 0.5;
      const py = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform =
        `translateY(-7px) perspective(800px) rotateX(${(py * -5).toFixed(2)}deg) rotateY(${(px * 5).toFixed(2)}deg)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();


/// ── Tooltip theo chuột — gắn vào document để luôn theo kịp ──
const tooltip = document.createElement('div');
tooltip.className = 'bc-cursor-tooltip';
tooltip.style.cssText = `
  display: none;
  position: fixed;
  z-index: 9999;
  pointer-events: none;
  background: #fff;
  border: 1px solid rgba(75,103,45,0.15);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(43,56,28,0.14);
  padding: 16px 18px;
  width: 200px;
  text-align: center;
`;
document.body.appendChild(tooltip);

document.querySelectorAll('.brand-card').forEach((card) => {
  const name = card.querySelector('.bc-name')?.textContent?.trim() || '';
  const desc = card.querySelector('.bc-tooltip-desc')?.textContent?.trim() || '';
  const link = card.querySelector('.bc-tooltip-btn')?.href || '#';

  card.addEventListener('mouseenter', () => {
    tooltip.innerHTML = `
      <span style="display:block;font-family:'Cormorant Garamond',serif;font-size:16px;font-weight:500;color:#2a311e;margin-bottom:6px;letter-spacing:1px;">${name}</span>
      <span style="display:block;font-size:12px;color:#7a8260;line-height:1.6;margin-bottom:12px;">${desc}</span>
      <a href="${link}" style="font-size:10px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#4B672D;text-decoration:none;border-bottom:1px solid rgba(75,103,45,0.3);padding-bottom:2px;">XEM SẢN PHẨM →</a>
    `;
    tooltip.style.display = 'block';
  });

  card.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
  });
});

document.addEventListener('mousemove', (e) => {
  if (tooltip.style.display === 'none') return;

  const offset = 14;
  let x = e.clientX + offset;
  let y = e.clientY + offset;

  if (x + 220 > window.innerWidth)  x = e.clientX - 220 - offset;
  if (y + 160  > window.innerHeight) y = e.clientY - 160  - offset;

  tooltip.style.left = x + 'px';
  tooltip.style.top  = y + 'px';
});