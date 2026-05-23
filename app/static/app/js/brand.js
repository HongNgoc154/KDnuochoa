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