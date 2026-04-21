/* =============================================================
   Ami Perfumery — main.js
   Tất cả logic JavaScript của trang web
   ============================================================= */

/* ─── 1. HEADER & NAVBAR: Đổi style khi scroll ─── */
const header = document.getElementById('site-header');
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
  const scrolled = window.scrollY > 60;
  header.classList.toggle('scrolled', scrolled);
  navbar.classList.toggle('scrolled', scrolled);
});

/* ─── 2. HERO: Animation load khi trang khởi động ─── */
window.addEventListener('load', () => {
  const hero = document.getElementById('hero');
  if (hero) setTimeout(() => hero.classList.add('loaded'), 100);
});

/* ─── 3. SCROLL REVEAL: Các phần tử có class .reveal ─── */
const reveals = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.12,
  rootMargin: '0px 0px -40px 0px'
});
reveals.forEach(el => revealObserver.observe(el));

/* ─── 4. CATEGORIES: Scroll reveal từng row (slide in) ─── */
const catRows = document.querySelectorAll('[data-reveal-row]');
const rowObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      rowObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
catRows.forEach(el => rowObserver.observe(el));

/* ─── 5. STORY SECTION: Kích hoạt animation stagger khi vào viewport ─── */
const storySection = document.getElementById('storySection');
if (storySection) {
  const storyObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        storyObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  storyObserver.observe(storySection);
}

/* ─── 6. PARALLAX: Ảnh nền Hero di chuyển chậm hơn scroll ─── */
const heroBg = document.querySelector('.hero-bg');
if (heroBg) {
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y < window.innerHeight) {
      heroBg.style.transform = `scale(1) translateY(${y * 0.25}px)`;
    }
  }, { passive: true });
}

(function initReveal() {
  const items = document.querySelectorAll('.reveal');
  const obs   = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -32px 0px' });
  items.forEach(el => obs.observe(el));
})();

/* ─── 7. CATEGORY PAGE: advanced carousel + premium micro interactions ─── */
const isCategoryPage = document.body.classList.contains('category-page');
if (isCategoryPage) {
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

  const formatVnd = (value) => `${Number(value).toLocaleString('vi-VN')}₫`;
  if (priceRange && priceValue) {
    const updatePrice = () => {
      priceValue.textContent = formatVnd(priceRange.value);
    };
    updatePrice();
    priceRange.addEventListener('input', updatePrice);
  }

  brandSearch?.addEventListener('input', () => {
    const keyword = brandSearch.value.trim().toLowerCase();
    [...brandOptions.querySelectorAll('label')].forEach((label) => {
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
    cards.forEach((card) => {
      const matchedScent = !selectedScents.length || selectedScents.includes(card.dataset.scent);
      const matchedBrand = !selectedBrands.length || selectedBrands.includes(card.dataset.brand);
      const matchedConcentration = !selectedConcentrations.length || selectedConcentrations.includes(card.dataset.concentration);
      const matchedPrice = Number(card.dataset.price) <= maxPrice;
      const visible = matchedScent && matchedBrand && matchedConcentration && matchedPrice;
      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    if (productResult) {
      productResult.textContent = `Hiển thị ${visibleCount} sản phẩm cao cấp.`;
    }
  };

  filterForm?.addEventListener('submit', (event) => {
    event.preventDefault();
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

  // Fireworks effect note:
  // We toggle .bursting and .bounce classes briefly so CSS pseudo-element can render
  // six radial particles around the heart icon without additional DOM/canvas.
  const updateFavoriteCount = () => {
    const count = document.querySelectorAll('.favorite-btn.is-liked').length;
    if (favoriteCount) favoriteCount.textContent = String(count);
  };

  document.querySelectorAll('.favorite-btn').forEach((btn) => {
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

  // Shake animation note:
  // Card and cart button each receive temporary classes to create a short tactile feedback.
  document.querySelectorAll('.add-cart-btn').forEach((btn) => {
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

  const productGrid = document.querySelector('.product-grid');
  const productDetailUrl = productGrid?.dataset.productDetailUrl;
  const shouldIgnoreCardRedirect = (eventTarget) => (
    eventTarget.closest('.product-actions') || eventTarget.closest('button') || eventTarget.closest('a')
  );

  if (productGrid && productDetailUrl) {
    productGrid.addEventListener('click', (event) => {
      const card = event.target.closest('.product-card');
      if (!card || shouldIgnoreCardRedirect(event.target)) return;
      window.location.href = productDetailUrl;
    });

    productGrid.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      const card = event.target.closest('.product-card');
      if (!card || shouldIgnoreCardRedirect(event.target)) return;
      event.preventDefault();
      window.location.href = productDetailUrl;
    });
  }

  const categoryHero = document.querySelector('.category-hero-video');
  if (categoryHero) {
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y < window.innerHeight) {
        categoryHero.style.transform = `scale(1.02) translateY(${y * 0.08}px)`;
      }
    }, { passive: true });
  }

  const segment = document.body.dataset.segment || 'all';
  document.querySelectorAll('.review-card').forEach((review) => {
    const segments = (review.dataset.segment || '').split(' ');
    review.hidden = !(segments.includes(segment) || segments.includes('all'));
  });

  // Arrow hover detection note:
  // We observe mouse position near the left/right edge of each carousel container
  // and only reveal the corresponding arrow for a cleaner luxury UI.
  const initEdgeCarousel = (carousel) => {
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

    carousel.addEventListener('mousemove', (event) => {
      const rect = carousel.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const edgeZone = Math.min(90, rect.width * 0.18);
      carousel.classList.toggle('show-left', x < edgeZone && !leftArrow.disabled);
      carousel.classList.toggle('show-right', x > rect.width - edgeZone && !rightArrow.disabled);
    });
    carousel.addEventListener('mouseleave', () => {
      carousel.classList.remove('show-left', 'show-right');
    });

    leftArrow.addEventListener('click', () => {
      track.scrollBy({ left: -scrollStep(), behavior: 'smooth' });
    });
    rightArrow.addEventListener('click', () => {
      track.scrollBy({ left: scrollStep(), behavior: 'smooth' });
    });

    track.addEventListener('scroll', updateArrowState, { passive: true });
    updateArrowState();
  };

  document.querySelectorAll('[data-carousel]').forEach(initEdgeCarousel);

  const reviewTrack = document.getElementById('reviewsGrid');
  if (reviewTrack) {
    const reviewCards = [...reviewTrack.querySelectorAll('.review-card')].filter((el) => !el.hidden);
    let autoScrollTimer;

    const refreshFocus = () => {
      const centerPoint = reviewTrack.getBoundingClientRect().left + reviewTrack.clientWidth / 2;
      let closest = null;
      let minDistance = Infinity;
      reviewCards.forEach((card) => {
        const rect = card.getBoundingClientRect();
        const cardCenter = rect.left + rect.width / 2;
        const distance = Math.abs(centerPoint - cardCenter);
        if (distance < minDistance) {
          minDistance = distance;
          closest = card;
        }
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

  (function initHeader() {
  const header = document.getElementById('site-header');
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    const scrolled = window.scrollY > 60;
    header?.classList.toggle('scrolled', scrolled);
    navbar?.classList.toggle('scrolled', scrolled);
  }, { passive: true });
})();
}