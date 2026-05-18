(() => {
  const form = document.querySelector('[data-contact-form]');
  const toast = document.querySelector('[data-contact-toast]');
  const confettiCanvas = document.querySelector('[data-confetti]');

  // Scroll reveal animation.
  const reveals = [...document.querySelectorAll('.reveal')];
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.16 });
  reveals.forEach((node) => observer.observe(node));

  document.querySelectorAll('[data-faq]').forEach((faq) => {
    faq.querySelector('.faq-q')?.addEventListener('click', () => faq.classList.toggle('open'));
  });

  const reviewItems = [...document.querySelectorAll('.review-item')];
  if (reviewItems.length) {
    let i = 0;
    setInterval(() => {
      reviewItems[i].classList.remove('is-active');
      i = (i + 1) % reviewItems.length;
      reviewItems[i].classList.add('is-active');
    }, 3200);
  }

  const validateField = (field) => {
    const valid = field.value.trim().length > 1 && (field.type !== 'email' || /.+@.+\..+/.test(field.value));
    field.classList.toggle('input-error', !valid);
    return valid;
  };

  form?.querySelectorAll('input, textarea').forEach((field) => {
    field.addEventListener('input', () => validateField(field));
  });

  const launchConfetti = () => {
    if (!confettiCanvas) return;
    const ctx = confettiCanvas.getContext('2d');
    confettiCanvas.width = confettiCanvas.offsetWidth;
    confettiCanvas.height = confettiCanvas.offsetHeight;
    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * confettiCanvas.width,
      y: -20,
      vy: 2 + Math.random() * 2,
      vx: -1 + Math.random() * 2,
      s: 2 + Math.random() * 4,
    }));

    let ticks = 0;
    const frame = () => {
      ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        ctx.fillStyle = ['#5f6f52', '#d6c9a7', '#f3eee2'][Math.floor(Math.random() * 3)];
        ctx.fillRect(p.x, p.y, p.s, p.s);
      });
      ticks += 1;
      if (ticks < 55) requestAnimationFrame(frame);
      else ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
    };
    frame();
  };

  form?.addEventListener('submit', (event) => {
    event.preventDefault();
    const fields = [...form.querySelectorAll('input, textarea')];
    const allValid = fields.every(validateField);
    if (!allValid) return;
    toast?.classList.add('is-show');
    launchConfetti();
    form.reset();
    setTimeout(() => toast?.classList.remove('is-show'), 2600);
  });

  document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
    const body = document.body;
    const dark = body.classList.toggle('dark');
    body.classList.toggle('light', !dark);
  });

  const heroVideo = document.querySelector('[data-contact-parallax] video');
  if (heroVideo) {
    window.addEventListener('scroll', () => {
      heroVideo.style.transform = `scale(1.04) translateY(${Math.min(40, window.scrollY * 0.06)}px)`;
    }, { passive: true });
  }
})();
