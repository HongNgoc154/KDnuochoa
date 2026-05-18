(() => {
  const brandTrack = document.querySelector('[data-brand-track]');
  const sliderWrap = document.querySelector('[data-brand-slider]');

  // Slider logic note:
  // This converts wheel/arrow input into smooth horizontal motion while keeping
  // native scroll-snap, creating a cinematic inertia-like movement.
  if (brandTrack && sliderWrap) {
    const cards = [...brandTrack.querySelectorAll('[data-brand-card]')];
    const prevBtn = sliderWrap.querySelector('[data-brand-prev]');
    const nextBtn = sliderWrap.querySelector('[data-brand-next]');
    const step = () => Math.max(320, brandTrack.clientWidth * 0.62);

    const updateCenterState = () => {
      const center = brandTrack.scrollLeft + (brandTrack.clientWidth / 2);
      let nearestCard = null;
      let nearestDistance = Number.POSITIVE_INFINITY;

      cards.forEach((card) => {
        const cardCenter = card.offsetLeft + (card.clientWidth / 2);
        const distance = Math.abs(cardCenter - center);
        card.classList.toggle('is-side', distance > card.clientWidth * 0.65);
        if (distance < nearestDistance) {
          nearestDistance = distance;
          nearestCard = card;
        }
      });

      cards.forEach((card) => card.classList.toggle('is-center', card === nearestCard));
    };

    let momentum = 0;
    let rafId = null;
    const animateMomentum = () => {
      if (Math.abs(momentum) < 0.5) {
        momentum = 0;
        rafId = null;
        return;
      }
      brandTrack.scrollLeft += momentum;
      momentum *= 0.92;
      updateCenterState();
      rafId = requestAnimationFrame(animateMomentum);
    };

    brandTrack.addEventListener('wheel', (event) => {
      if (Math.abs(event.deltaY) < Math.abs(event.deltaX)) return;
      event.preventDefault();
      momentum += event.deltaY * 0.26;
      if (!rafId) rafId = requestAnimationFrame(animateMomentum);
    }, { passive: false });

    prevBtn?.addEventListener('click', () => {
      brandTrack.scrollBy({ left: -step(), behavior: 'smooth' });
    });
    nextBtn?.addEventListener('click', () => {
      brandTrack.scrollBy({ left: step(), behavior: 'smooth' });
    });

    brandTrack.addEventListener('scroll', () => requestAnimationFrame(updateCenterState), { passive: true });
    window.addEventListener('resize', updateCenterState);
    setTimeout(updateCenterState, 80);

    // Tilt effect note:
    // Reads pointer position inside each card and maps it to rotateX/rotateY for
    // a subtle 3D poster feel. Values reset smoothly on mouse leave.
    cards.forEach((card) => {
      const link = card.querySelector('.brand-poster-link');
      if (!link) return;

      card.addEventListener('mousemove', (event) => {
        const rect = card.getBoundingClientRect();
        const px = (event.clientX - rect.left) / rect.width;
        const py = (event.clientY - rect.top) / rect.height;
        const tiltY = (px - 0.5) * 10;
        const tiltX = (0.5 - py) * 10;
        link.style.setProperty('--tilt-x', `${tiltX.toFixed(2)}deg`);
        link.style.setProperty('--tilt-y', `${tiltY.toFixed(2)}deg`);
      });

      card.addEventListener('mouseleave', () => {
        link.style.setProperty('--tilt-x', '0deg');
        link.style.setProperty('--tilt-y', '0deg');
      });
    });

    document.querySelectorAll('.brand-poster-link').forEach((link) => {
      link.addEventListener('click', (event) => {
        const href = link.getAttribute('href');
        if (!href) return;
        event.preventDefault();
        document.body.classList.add('brand-leaving');
        setTimeout(() => { window.location.href = href; }, 240);
      });
    });
  }

  // Section reveal note:
  // IntersectionObserver toggles .in-view for staggered fade/translate storytelling.
  const reveals = [...document.querySelectorAll('.reveal')];
  if (reveals.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.16, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach((node) => observer.observe(node));
  }

  const hero = document.querySelector('[data-parallax] img');
  if (hero) {
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      hero.style.transform = `scale(1.06) translateY(${Math.min(60, y * 0.09)}px)`;
    }, { passive: true });
  }
})();
