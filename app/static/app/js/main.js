/* =============================================================
   Ami Perfumery — main.js (updated)
   ============================================================= */

/* ─── 1. HEADER & NAVBAR scroll ─── */
(function initHeaderScroll() {
  const header = document.getElementById('site-header');
  const navbar = document.getElementById('navbar');
  if (!header || !navbar) return;
  window.addEventListener('scroll', () => {
    const scrolled = window.scrollY > 60;
    header.classList.toggle('scrolled', scrolled);
    navbar.classList.toggle('scrolled', scrolled);
  }, { passive: true });
})();

/* ─── 2. HERO animation ─── */
window.addEventListener('load', () => {
  const hero = document.getElementById('hero');
  if (hero) setTimeout(() => hero.classList.add('loaded'), 100);
});

/* ─── 3. SCROLL REVEAL ─── */
(function initReveal() {
  const items = document.querySelectorAll('.reveal');
  if (!items.length) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -32px 0px' });
  items.forEach(el => obs.observe(el));
})();

/* ─── 4. CATEGORY ROWS reveal ─── */
(function initCatRows() {
  const catRows = document.querySelectorAll('[data-reveal-row]');
  if (!catRows.length) return;
  const rowObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        rowObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  catRows.forEach(el => rowObserver.observe(el));
})();

/* ─── 5. STORY SECTION in-view ─── */
(function initStory() {
  const storySection = document.getElementById('storySection');
  if (!storySection) return;
  const storyObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        storyObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  storyObserver.observe(storySection);
})();

/* ─── 6. HERO PARALLAX ─── */
(function initHeroParallax() {
  const heroBg = document.querySelector('.hero-bg');
  if (!heroBg) return;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y < window.innerHeight) {
      heroBg.style.transform = `scale(1) translateY(${y * 0.25}px)`;
    }
  }, { passive: true });
})();

/* ─── 7. ACCOUNT MENU DROPDOWN ─── */
(function initAccountMenu() {
  const menus = document.querySelectorAll('[data-account-menu]');
  if (!menus.length) return;

  const closeAll = () => {
    menus.forEach(menu => {
      menu.classList.remove('is-open');
      menu.querySelector('[data-account-trigger]')?.setAttribute('aria-expanded', 'false');
    });
  };

  menus.forEach(menu => {
    const trigger = menu.querySelector('[data-account-trigger]');
    if (!trigger) return;
    trigger.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = menu.classList.contains('is-open');
      closeAll();
      if (!isOpen) {
        menu.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('[data-account-menu]')) closeAll();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAll();
  });
})();

/* ─── 8. ARTICLES "XEM THÊM" ─── */
(function initArticlesSeeMore() {
  const btnSeeMore = document.getElementById('btnSeeMoreArticles');
  const teaserBlock = document.getElementById('articlesTeaserBlock');
  if (!btnSeeMore) return;

  // Đếm số bài viết trong grid
  const grid = document.getElementById('articlesGrid');
  const allCards = grid ? grid.querySelectorAll('.article-card') : [];
  const extraCards = grid ? grid.querySelectorAll('.article-extra') : [];

  // Chỉ hiện teaser block nếu có bài viết ẩn (tức là có > 3 bài hiển thị ban đầu)
  if (extraCards.length === 0) {
    if (teaserBlock) teaserBlock.style.display = 'none';
    return;
  }

  let expanded = false;

  btnSeeMore.addEventListener('click', () => {
    expanded = !expanded;
    extraCards.forEach(card => {
      card.style.display = expanded ? '' : 'none';
      if (expanded) {
        // Kích hoạt reveal animation cho các bài mới hiện
        requestAnimationFrame(() => {
          card.classList.add('visible');
        });
      } else {
        card.classList.remove('visible');
      }
    });

    // Cập nhật nút
    const btnSpan = btnSeeMore.querySelector('span');
    if (btnSpan) {
      btnSpan.textContent = expanded ? 'Thu gọn bài viết' : 'Xem thêm bài viết';
    }
    btnSeeMore.classList.toggle('expanded', expanded);

    // Nếu thu gọn, cuộn về đầu section
    if (!expanded) {
      const articlesSection = document.querySelector('.articles-section');
      if (articlesSection) {
        articlesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });
})();

/* ─── 9. CATEGORY PAGE ─── */
const isCategoryPage = document.body.classList.contains('category-page');
if (isCategoryPage) {

  /* Filter sidebar */
  const openFilterBtn = document.getElementById('openFilter');
  const closeFilterBtn = document.getElementById('closeFilter');
  const filterOverlay = document.getElementById('filterOverlay');
  const filterForm = document.getElementById('filterForm');
  const resetFiltersBtn = document.getElementById('resetFilters');
  const brandSearch = document.getElementById('brandSearch');
  const brandOptions = document.getElementById('brandOptions');
  const priceRange = document.getElementById('priceRange');
  const priceValue = document.getElementById('priceValue');
  const cards = [...document.querySelectorAll('.product-card')];
  const productResult = document.getElementById('productResult');
  const favoriteCount = document.getElementById('favoriteCount');

  const closeFilter = () => {
    document.body.classList.remove('filter-open');
    document.getElementById('filterSidebar')?.setAttribute('aria-hidden', 'true');
  };

  openFilterBtn?.addEventListener('click', () => {
    document.body.classList.add('filter-open');
    document.getElementById('filterSidebar')?.setAttribute('aria-hidden', 'false');
  });
  closeFilterBtn?.addEventListener('click', closeFilter);
  filterOverlay?.addEventListener('click', closeFilter);

  const formatVnd = value => `${Number(value).toLocaleString('vi-VN')}₫`;
  if (priceRange && priceValue) {
    const updatePrice = () => { priceValue.textContent = formatVnd(priceRange.value); };
    updatePrice();
    priceRange.addEventListener('input', updatePrice);
  }

  brandSearch?.addEventListener('input', () => {
    const keyword = brandSearch.value.trim().toLowerCase();
    [...brandOptions.querySelectorAll('label')].forEach(label => {
      label.hidden = !label.textContent.toLowerCase().includes(keyword);
    });
  });

  const applyFilters = () => {
    const formData = new FormData(filterForm);
    const selectedScents = formData.getAll('scent');
    const selectedBrands = formData.getAll('brand');
    const selectedConcentrations = formData.getAll('concentration');
    const maxPrice = Number(priceRange?.value || 8000000);
    let visibleCount = 0;
    cards.forEach(card => {
      const visible =
        (!selectedScents.length || selectedScents.includes(card.dataset.scent)) &&
        (!selectedBrands.length || selectedBrands.includes(card.dataset.brand)) &&
        (!selectedConcentrations.length || selectedConcentrations.includes(card.dataset.concentration)) &&
        Number(card.dataset.price) <= maxPrice;
      card.hidden = !visible;
      if (visible) visibleCount++;
    });
    if (productResult) productResult.textContent = `Hiển thị ${visibleCount} sản phẩm cao cấp.`;
  };

  filterForm?.addEventListener('submit', e => {
    e.preventDefault();
    applyFilters();
    closeFilter();
  });

  resetFiltersBtn?.addEventListener('click', () => {
    filterForm?.reset();
    if (brandSearch) brandSearch.value = '';
    brandSearch?.dispatchEvent(new Event('input'));
    priceRange?.dispatchEvent(new Event('input'));
    applyFilters();
  });

  /* Favorite buttons */
  const updateFavoriteCount = () => {
    const count = document.querySelectorAll('.favorite-btn.is-liked').length;
    if (favoriteCount) favoriteCount.textContent = String(count);
  };

  document.querySelectorAll('.favorite-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const isLiked = btn.classList.toggle('is-liked');
      btn.setAttribute('aria-pressed', String(isLiked));
      const heartCore = btn.querySelector('.heart-core');
      if (heartCore) heartCore.textContent = isLiked ? '♥' : '♡';
      btn.classList.remove('bursting', 'bounce');
      void btn.offsetWidth;
      btn.classList.add('bursting', 'bounce');
      setTimeout(() => btn.classList.remove('bursting', 'bounce'), 520);
      updateFavoriteCount();
    });
  });

  /* Add to cart */
  document.querySelectorAll('.add-cart-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.disabled) return;
      const card = btn.closest('.product-card');
      card?.classList.remove('shake');
      btn.classList.remove('bounce');
      void btn.offsetWidth;
      card?.classList.add('shake');
      btn.classList.add('bounce');
      setTimeout(() => {
        card?.classList.remove('shake');
        btn.classList.remove('bounce');
      }, 450);
    });
  });

  /* Product card click → detail page */
  const productGrid = document.querySelector('.product-grid');
  const productDetailUrl = productGrid?.dataset.productDetailUrl;
  const shouldIgnore = target =>
    target.closest('.product-actions') || target.closest('button') || target.closest('a');

  if (productGrid && productDetailUrl) {
    productGrid.addEventListener('click', e => {
      const card = e.target.closest('.product-card');
      if (!card || shouldIgnore(e.target)) return;
      window.location.href = card.dataset.detailUrl || productDetailUrl;
    });
    productGrid.addEventListener('keydown', e => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const card = e.target.closest('.product-card');
      if (!card || shouldIgnore(e.target)) return;
      e.preventDefault();
      window.location.href = card.dataset.detailUrl || productDetailUrl;
    });
  }

  /* Category hero parallax */
  const categoryHeroVideo = document.querySelector('.category-hero-video');
  if (categoryHeroVideo) {
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y < window.innerHeight) {
        categoryHeroVideo.style.transform = `scale(1.02) translateY(${y * 0.08}px)`;
      }
    }, { passive: true });
  }

  /* Edge carousels */
  const initEdgeCarousel = carousel => {
    const track = carousel.querySelector('[data-carousel-track]');
    const leftArrow = carousel.querySelector('.edge-arrow-left');
    const rightArrow = carousel.querySelector('.edge-arrow-right');
    if (!track || !leftArrow || !rightArrow) return;

    const stepRatio = Number(carousel.dataset.step || 0.8);
    const scrollStep = () => track.clientWidth * stepRatio;

    const updateArrowState = () => {
      const maxScroll = track.scrollWidth - track.clientWidth - 2;
      leftArrow.disabled = track.scrollLeft <= 2;
      rightArrow.disabled = track.scrollLeft >= maxScroll;
    };

    carousel.addEventListener('mousemove', e => {
      const rect = carousel.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const edgeZone = Math.min(90, rect.width * 0.18);
      carousel.classList.toggle('show-left', x < edgeZone && !leftArrow.disabled);
      carousel.classList.toggle('show-right', x > rect.width - edgeZone && !rightArrow.disabled);
    });
    carousel.addEventListener('mouseleave', () => {
      carousel.classList.remove('show-left', 'show-right');
    });
    leftArrow.addEventListener('click', () => track.scrollBy({ left: -scrollStep(), behavior: 'smooth' }));
    rightArrow.addEventListener('click', () => track.scrollBy({ left: scrollStep(), behavior: 'smooth' }));
    track.addEventListener('scroll', updateArrowState, { passive: true });
    updateArrowState();
  };
  document.querySelectorAll('[data-carousel]').forEach(initEdgeCarousel);

  /* Review auto-scroll */
  const reviewTrack = document.getElementById('reviewsGrid');
  if (reviewTrack) {
    const reviewCards = [...reviewTrack.querySelectorAll('.review-card')].filter(el => !el.hidden);
    let autoScrollTimer;
    const refreshFocus = () => {
      const centerPoint = reviewTrack.getBoundingClientRect().left + reviewTrack.clientWidth / 2;
      let closest = null;
      let minDistance = Infinity;
      reviewCards.forEach(card => {
        const rect = card.getBoundingClientRect();
        const dist = Math.abs(rect.left + rect.width / 2 - centerPoint);
        if (dist < minDistance) { minDistance = dist; closest = card; }
        card.classList.remove('in-focus');
      });
      if (closest) closest.classList.add('in-focus');
    };
    const startAutoScroll = () => {
      stopAutoScroll();
      autoScrollTimer = setInterval(() => {
        reviewTrack.scrollBy({ left: 1, behavior: 'auto' });
        if (reviewTrack.scrollLeft + reviewTrack.clientWidth >= reviewTrack.scrollWidth - 1) {
          reviewTrack.scrollTo({ left: 0, behavior: 'smooth' });
        }
        refreshFocus();
      }, 30);
    };
    const stopAutoScroll = () => clearInterval(autoScrollTimer);
    reviewTrack.addEventListener('mouseenter', stopAutoScroll);
    reviewTrack.addEventListener('mouseleave', startAutoScroll);
    reviewTrack.addEventListener('scroll', refreshFocus, { passive: true });
    refreshFocus();
    startAutoScroll();
  }

  applyFilters();
  updateFavoriteCount();
}