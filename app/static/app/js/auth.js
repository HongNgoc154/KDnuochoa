/* =============================================================
   Ami Perfumery — auth.js
   Luxury login / register page interactions

   Modules:
   1. Particles      — floating ambient canvas dots
   2. ThemeToggle    — dark/light mode
   3. TabSwitch      — ink-bar tab + form slide transition
   4. EyeToggle      — show/hide password
   5. Validation     — realtime field validation
   6. StrengthMeter  — password strength indicator
   7. LoginSubmit    — login form with loading + success
   8. RegisterSubmit — register form with loading + success
   9. VisualCaption  — update caption text on mode switch
   ============================================================= */

/* ═══════════════════════════════════════════════════════════
   1. AMBIENT PARTICLES
   Tiny glowing dots float slowly upward with slight drift.
   Drawn on a canvas behind everything (z-index: 0).
   ═══════════════════════════════════════════════════════════ */
(function initParticles() {
  const canvas = document.getElementById('particleCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, particles;

  const PARTICLE_COUNT = 55;
  const COLORS = [
    'rgba(154,173,98,',
    'rgba(240,234,220,',
    'rgba(213,201,176,',
  ];

  class Particle {
    constructor() { this.reset(true); }
    reset(init = false) {
      this.x  = Math.random() * W;
      this.y  = init ? Math.random() * H : H + 10;
      this.r  = Math.random() * 2 + 0.5;
      this.vy = -(Math.random() * 0.4 + 0.15);   /* float upward */
      this.vx = (Math.random() - 0.5) * 0.2;     /* slight horizontal drift */
      this.alpha = Math.random() * 0.5 + 0.1;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      this.life = 0;
      this.maxLife = Math.random() * 300 + 200;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.life++;
      /* Fade in/out using life cycle */
      const progress = this.life / this.maxLife;
      if (progress < 0.15)      this.currentAlpha = this.alpha * (progress / 0.15);
      else if (progress > 0.75) this.currentAlpha = this.alpha * (1 - (progress - 0.75) / 0.25);
      else                      this.currentAlpha = this.alpha;
      if (this.life >= this.maxLife || this.y < -10) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `${this.color}${this.currentAlpha.toFixed(2)})`;
      /* Soft glow */
      ctx.shadowBlur = 8;
      ctx.shadowColor = `${this.color}0.3)`;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  const resize = () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  };
  const init = () => {
    resize();
    particles = Array.from({ length: PARTICLE_COUNT }, () => new Particle());
  };

  let raf;
  const loop = () => {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    raf = requestAnimationFrame(loop);
  };

  window.addEventListener('resize', resize, { passive: true });
  init();
  loop();

  /* Pause when tab hidden (performance) */
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else loop();
  });
})();

/* ═══════════════════════════════════════════════════════════
   2. THEME TOGGLE — dark / light
   ═══════════════════════════════════════════════════════════ */
(function initTheme() {
  const btn  = document.getElementById('themeToggle');
  const icon = document.getElementById('themeIcon');
  if (!btn) return;

  /* Load saved preference */
  const saved = localStorage.getItem('ami_theme');
  if (saved === 'dark') { document.body.classList.add('dark-mode'); icon.textContent = '☀'; }

  btn.addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark-mode');
    icon.textContent = isDark ? '☀' : '☽';
    localStorage.setItem('ami_theme', isDark ? 'dark' : 'light');
  });
})();

/* ═══════════════════════════════════════════════════════════
   3. TAB SWITCH + FORM TRANSITION
   Ink bar slides between tabs.
   Old form fades+slides out, new form slides in.
   ═══════════════════════════════════════════════════════════ */
(function initTabs() {
  const tabBtns     = document.querySelectorAll('.auth-tab');
  const ink         = document.getElementById('tabInk');
  const formLogin   = document.getElementById('formLogin');
  const formReg     = document.getElementById('formRegister');
  const stage       = document.getElementById('authStage');
  const switchBtns  = document.querySelectorAll('.switch-btn');
  if (!ink || !formLogin || !formReg) return;

  let current = 'login';

  /* Position ink under a tab button */
  const moveInk = (btn) => {
    ink.style.left  = `${btn.offsetLeft}px`;
    ink.style.width = `${btn.offsetWidth}px`;
  };

  /* Switch to target form ('login' | 'register') */
  const switchTo = (target) => {
    if (target === current) return;

    const outForm = current === 'login' ? formLogin : formReg;
    const inForm  = target  === 'login' ? formLogin : formReg;
    const inTab   = target  === 'login'
      ? document.getElementById('tabLogin')
      : document.getElementById('tabRegister');

    /* Update tabs */
    tabBtns.forEach(b => {
      b.classList.toggle('active', b.dataset.form === target);
      b.setAttribute('aria-selected', String(b.dataset.form === target));
    });
    moveInk(inTab);

    /* Update stage class for visual panel parallax */
    stage?.classList.toggle('register-mode', target === 'register');

    /* Slide out → wait → hide, show + slide in */
    outForm.classList.add('slide-out');
    outForm.addEventListener('animationend', () => {
      outForm.classList.add('hidden');
      outForm.classList.remove('slide-out');
      inForm.classList.remove('hidden');
      inForm.classList.add('slide-in');
      inForm.addEventListener('animationend', () => {
        inForm.classList.remove('slide-in');
      }, { once: true });
    }, { once: true });

    /* Update visual caption */
    updateCaption(target);
    current = target;
  };

  /* Tab clicks */
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTo(btn.dataset.form));
  });

  /* Switch links inside forms */
  switchBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTo(btn.dataset.switch));
  });

  /* Init ink */
  const activeTab = document.querySelector('.auth-tab.active');
  if (activeTab) moveInk(activeTab);

  /* Expose for external use */
  window.authSwitchTo = switchTo;
})();

/* ═══════════════════════════════════════════════════════════
   4. EYE TOGGLE — show/hide password
   ═══════════════════════════════════════════════════════════ */
function initEyeToggle(btnId, inputId) {
  const btn   = document.getElementById(btnId);
  const input = document.getElementById(inputId);
  if (!btn || !input) return;

  const eyeOpen   = btn.querySelector('.eye-open');
  const eyeClosed = btn.querySelector('.eye-closed');

  btn.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    eyeOpen.style.display   = show ? 'none'         : '';
    eyeClosed.style.display = show ? ''             : 'none';
    btn.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
  });
}
initEyeToggle('lgEyeBtn', 'lgPass');
initEyeToggle('rgEyeBtn', 'rgPass');

/* ═══════════════════════════════════════════════════════════
   5. VALIDATION HELPERS
   Realtime + on-submit validation with luxury error display.
   ═══════════════════════════════════════════════════════════ */
const validators = {
  email: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? '' : 'Email không hợp lệ.',
  required: (v, label) => v.trim() ? '' : `${label || 'Trường này'} không được để trống.`,
  phone: (v) => /^(0|\+84)[0-9]{8,10}$/.test(v.replace(/\s/g,'')) ? '' : 'Số điện thoại không hợp lệ.',
  username: (v) => /^[a-zA-Z0-9_.]{4,20}$/.test(v.trim()) ? '' : 'Tên đăng nhập 4–20 ký tự, không dấu.',
  password: (v) => v.length >= 8 ? '' : 'Mật khẩu tối thiểu 8 ký tự.',
  password2: (v, pw) => v === pw ? '' : 'Mật khẩu không khớp.',
};

/* Show / clear field error */
function setError(groupId, errId, msg) {
  const group = document.getElementById(groupId);
  const err   = document.getElementById(errId);
  if (!group || !err) return;
  if (msg) {
    group.classList.add('has-error');
    err.textContent = msg;
  } else {
    group.classList.remove('has-error');
    err.textContent = '';
  }
  return !msg; /* true = valid */
}

/* Attach realtime validation */
function realtimeValidate(inputEl, validate, groupId, errId) {
  if (!inputEl) return;
  const run = () => {
    const msg = validate(inputEl.value);
    setError(groupId, errId, msg);
  };
  inputEl.addEventListener('blur',  run);
  inputEl.addEventListener('input', () => {
    /* Only clear error while typing; full check on blur */
    if (document.getElementById(groupId)?.classList.contains('has-error')) run();
  });
}

/* Login realtime */
realtimeValidate(document.getElementById('lgEmail'), validators.email, 'lgEmailGroup', 'lgEmailErr');
realtimeValidate(document.getElementById('lgPass'),  (v) => validators.required(v,'Mật khẩu'), 'lgPassGroup', 'lgPassErr');

/* Register realtime */
realtimeValidate(document.getElementById('rgName'),   (v) => validators.required(v,'Họ tên'), 'rgNameGroup', 'rgNameErr');
realtimeValidate(document.getElementById('rgEmail'),  validators.email, 'rgEmailGroup', 'rgEmailErr');
realtimeValidate(document.getElementById('rgPhone'),  validators.phone, 'rgPhoneGroup', 'rgPhoneErr');
realtimeValidate(document.getElementById('rgUser'),   validators.username, 'rgUserGroup', 'rgUserErr');
realtimeValidate(document.getElementById('rgPass'),   validators.password, 'rgPassGroup', 'rgPassErr');
realtimeValidate(document.getElementById('rgPass2'),  (v) => {
  return validators.password2(v, document.getElementById('rgPass')?.value || '');
}, 'rgPass2Group', 'rgPass2Err');

/* ═══════════════════════════════════════════════════════════
   6. PASSWORD STRENGTH METER
   Scores password on length, variety of chars, complexity.
   Updates the colour bar + label in realtime.
   ═══════════════════════════════════════════════════════════ */
(function initStrengthMeter() {
  const input  = document.getElementById('rgPass');
  const bar    = document.getElementById('strengthBar');
  const label  = document.getElementById('strengthLabel');
  if (!input || !bar || !label) return;

  const score = (pw) => {
    let s = 0;
    if (pw.length >= 8)  s++;
    if (pw.length >= 12) s++;
    if (/[A-Z]/.test(pw)) s++;
    if (/[0-9]/.test(pw)) s++;
    if (/[^A-Za-z0-9]/.test(pw)) s++;
    return s;
  };

  const levels = [
    { level: '',       text: '' },
    { level: 'weak',   text: 'Yếu' },
    { level: 'fair',   text: 'Trung bình' },
    { level: 'good',   text: 'Tốt' },
    { level: 'strong', text: 'Mạnh' },
  ];

  input.addEventListener('input', () => {
    const pw = input.value;
    if (!pw) { bar.dataset.level = ''; bar.style.width = '0'; label.textContent = ''; return; }
    const s = Math.min(score(pw), 4);
    const l = levels[s];
    bar.dataset.level  = l.level;
    label.textContent  = l.text;
    /* label color */
    const colorMap = { '': '', weak: '#c0392b', fair: '#e67e22', good: '#f1c40f', strong: '#4a7c4e' };
    label.style.color = colorMap[l.level] || '';
  });
})();

/* ═══════════════════════════════════════════════════════════
   7. LOGIN SUBMIT
   ═══════════════════════════════════════════════════════════ */
(function initLogin() {
  const form   = document.getElementById('loginForm');
  const btn    = document.getElementById('lgSubmit');
  if (!form || !btn) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailVal = document.getElementById('lgEmail')?.value || '';
    const passVal  = document.getElementById('lgPass')?.value  || '';

    const v1 = setError('lgEmailGroup', 'lgEmailErr', validators.email(emailVal));
    const v2 = setError('lgPassGroup',  'lgPassErr',  validators.required(passVal,'Mật khẩu'));

    if (!v1 || !v2) return;

    /* Loading state */
    btn.classList.add('loading');
    btn.disabled = true;

    /* Simulate API call (replace with real fetch) */
    await fakeRequest(1400);

    btn.classList.remove('loading');
    btn.disabled = false;

    showSuccess('Chào mừng trở lại!', 'Đang chuyển hướng trang chủ…');
  });
})();

/* ═══════════════════════════════════════════════════════════
   8. REGISTER SUBMIT
   ═══════════════════════════════════════════════════════════ */
(function initRegister() {
  const form = document.getElementById('registerForm');
  const btn  = document.getElementById('rgSubmit');
  if (!form || !btn) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const vals = {
      name:  document.getElementById('rgName')?.value  || '',
      email: document.getElementById('rgEmail')?.value || '',
      phone: document.getElementById('rgPhone')?.value || '',
      user:  document.getElementById('rgUser')?.value  || '',
      pw:    document.getElementById('rgPass')?.value  || '',
      pw2:   document.getElementById('rgPass2')?.value || '',
    };

    const checks = [
      setError('rgNameGroup',  'rgNameErr',  validators.required(vals.name,'Họ tên')),
      setError('rgEmailGroup', 'rgEmailErr', validators.email(vals.email)),
      setError('rgPhoneGroup', 'rgPhoneErr', validators.phone(vals.phone)),
      setError('rgUserGroup',  'rgUserErr',  validators.username(vals.user)),
      setError('rgPassGroup',  'rgPassErr',  validators.password(vals.pw)),
      setError('rgPass2Group', 'rgPass2Err', validators.password2(vals.pw2, vals.pw)),
    ];

    if (checks.some(v => !v)) return;

    btn.classList.add('loading');
    btn.disabled = true;

    await fakeRequest(1800);

    btn.classList.remove('loading');
    btn.disabled = false;

    showSuccess('Tài khoản đã được tạo!', 'Chào mừng bạn đến với Ami Perfumery…');
  });
})();

/* ═══════════════════════════════════════════════════════════
   9. VISUAL CAPTION UPDATE
   Changes the editorial text on the image panel when
   switching between login and register modes.
   ═══════════════════════════════════════════════════════════ */
const captions = {
  login: {
    line1: 'Mỗi mùi hương',
    line2:  'là một câu chuyện',
    img:   'https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=1000&q=90',
  },
  register: {
    line1: 'Khám phá',
    line2:  'phiên bản riêng của bạn',
    img:   'https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=1000&q=90',
  },
};

function updateCaption(mode) {
  const c    = captions[mode] || captions.login;
  const l1   = document.getElementById('visualLine1');
  const l2   = document.getElementById('visualLine2');
  const img  = document.getElementById('visualImg');
  if (!l1 || !l2) return;

  /* Fade out, change, fade in */
  [l1, l2].forEach(el => { el.style.opacity = '0'; el.style.transform = 'translateY(8px)'; });
  if (img) { img.style.opacity = '0'; img.style.transition = 'opacity .4s ease'; }

  setTimeout(() => {
    l1.textContent = c.line1;
    l2.querySelector('em').textContent = c.line2;
    if (img) img.src = c.img;
    [l1, l2].forEach((el, i) => {
      el.style.transition = `opacity .5s ease ${i * 0.06}s, transform .5s ease ${i * 0.06}s`;
      el.style.opacity    = '';
      el.style.transform  = '';
    });
    if (img) { img.style.opacity = '1'; }
  }, 280);
}

/* ─── HELPERS ─── */

/* Simulate async request */
function fakeRequest(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/* Show success overlay then redirect */
function showSuccess(title, sub) {
  const overlay = document.getElementById('successOverlay');
  const titleEl = document.getElementById('successTitle');
  const subEl   = document.getElementById('successSub');
  if (!overlay) return;

  if (titleEl) titleEl.textContent = title;
  if (subEl)   subEl.textContent   = sub;

  overlay.setAttribute('aria-hidden', 'false');
  overlay.classList.add('visible');

  /* Redirect after animation (replace with real URL) */
  setTimeout(() => {
    window.location.href = '/';
  }, 2600);
}