(() => {
  const revealElements = [...document.querySelectorAll('.reveal')];

  // Scroll animation note:
  // IntersectionObserver adds .in-view once, giving subtle fade/translate reveal.
  if (revealElements.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.14, rootMargin: '0px 0px -8% 0px' });

    revealElements.forEach((item) => observer.observe(item));
  }

  const bentoGrid = document.querySelector('[data-bento-grid]');
  const pagination = document.querySelector('[data-pagination]');
  const tabs = [...document.querySelectorAll('[data-blog-tabs] .blog-tab')];

  if (bentoGrid && pagination) {
    const cards = [...bentoGrid.querySelectorAll('[data-bento-item]')];
    let activeFilter = 'all';
    let page = 1;
    const pageSize = 4;

    // Pagination logic note:
    // We filter cards by selected tab category, then paginate client-side to keep
    // editorial bento rhythm while avoiding page reload.
    const renderPagination = (totalPages) => {
      pagination.innerHTML = '';
      for (let i = 1; i <= totalPages; i += 1) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `page-btn ${i === page ? 'is-active' : ''}`;
        button.textContent = String(i);
        button.addEventListener('click', () => {
          page = i;
          applyFilterAndPaging();
        });
        pagination.appendChild(button);
      }
    };

    const applyFilterAndPaging = () => {
      const filtered = cards.filter((card) => activeFilter === 'all' || card.dataset.category === activeFilter);
      const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
      if (page > totalPages) page = 1;

      cards.forEach((card) => { card.hidden = true; });
      filtered.slice((page - 1) * pageSize, page * pageSize).forEach((card) => { card.hidden = false; });

      renderPagination(totalPages);
    };

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        tabs.forEach((item) => item.classList.remove('is-active'));
        tab.classList.add('is-active');
        activeFilter = tab.dataset.filter || 'all';
        page = 1;
        applyFilterAndPaging();
      });
    });

    applyFilterAndPaging();
  }

  document.querySelectorAll('[data-mini-carousel]').forEach((carousel) => {
    const track = carousel.querySelector('[data-mini-track]');
    const prev = carousel.querySelector('[data-mini-prev]');
    const next = carousel.querySelector('[data-mini-next]');
    if (!track) return;

    const step = () => track.clientWidth * 0.78;
    prev?.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    next?.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
  });

  const survey = document.querySelector('[data-survey]');
  const surveyMessage = document.querySelector('[data-survey-message]');
  if (survey && surveyMessage) {
    survey.addEventListener('click', (event) => {
      const target = event.target.closest('.survey-btn');
      if (!target) return;

      survey.querySelectorAll('.survey-btn').forEach((btn) => btn.classList.remove('is-picked'));
      target.classList.add('is-picked');
      const type = target.dataset.feedback;
      surveyMessage.textContent = type === 'helpful'
        ? 'Cảm ơn bạn! Ami sẽ tiếp tục tạo nội dung hữu ích hơn.'
        : 'Tuyệt vời! Đội ngũ tư vấn đang chờ bạn trên Zalo.';
    });
  }

  const heroImage = document.querySelector('[data-article-parallax] img');
  if (heroImage) {
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      heroImage.style.transform = `scale(1.05) translateY(${Math.min(48, y * 0.08)}px)`;
    }, { passive: true });
  }
})();
