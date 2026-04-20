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