/* AMI PERFUMERY — Admin JS */
(function () {
  'use strict';

  // ── Toast notification ──
  window.showToast = function (msg, ok) {
    var t = document.getElementById('ami-toast');
    if (!t) return;
    t.textContent = msg;
    t.style.borderColor = ok === false ? 'rgba(184,50,50,.3)' : 'rgba(235,246,196,.2)';
    t.classList.add('show');
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(function () { t.classList.remove('show'); }, 3400);
  };

  // ── Alert auto-dismiss ──
  setTimeout(function () {
    document.querySelectorAll('.ami-alert').forEach(function (el) {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 500);
    });
  }, 5000);

  // ── Sidebar mobile toggle ──
  var toggleBtn = document.getElementById('sidebarToggle');
  var sidebar   = document.getElementById('ami-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
    // Close on outside click
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Row click to navigate (if not checkbox) ──
  document.querySelectorAll('#result_list tbody tr').forEach(function (row) {
    var link = row.querySelector('td a');
    if (!link) return;
    row.style.cursor = 'pointer';
    row.addEventListener('click', function (e) {
      if (e.target.type === 'checkbox' || e.target.tagName === 'A' || e.target.tagName === 'INPUT') return;
      link.click();
    });
  });

  // ── Select all checkbox ──
  var selectAll = document.getElementById('action-toggle');
  if (selectAll) {
    selectAll.addEventListener('change', function () {
      document.querySelectorAll('input[name="_selected_action"]').forEach(function (cb) {
        cb.checked = selectAll.checked;
        cb.closest('tr').classList.toggle('selected', cb.checked);
      });
    });
  }

  // ── Per-row checkbox highlight ──
  document.querySelectorAll('input[name="_selected_action"]').forEach(function (cb) {
    cb.addEventListener('change', function () {
      this.closest('tr').classList.toggle('selected', this.checked);
    });
  });

  // ── Confirm delete ──
  document.querySelectorAll('a.deletelink, a[href*="/delete/"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      if (!confirm('Xác nhận xóa bản ghi này?')) e.preventDefault();
    });
  });

})();