/**
 * phieunhap.js — app/static/admin/js/phieunhap.js
 * Layout mới: Trái = phiếu tổng thể | Phải = thao tác
 */
(function () {
  'use strict';

  /* ── State ── */
  let rows        = [];   // [{bien_the_id, san_pham, sku, gia_nhap, so_luong, is_new}]
  let newProducts = [];   // [{ten_san_pham, thuong_hieu, bien_the:[...]}]
  let selSpId     = null;
  let selSpName   = '';
  let btNewIdx    = 0;

  /* ── Init ── */
  function init() {
    // Nạp chi tiết cũ (khi edit phiếu đã có)
    if (window.PN_CHI_TIET && PN_CHI_TIET.length) {
      PN_CHI_TIET.forEach(ct => rows.push({
        bien_the_id: ct.bien_the_id,
        san_pham:    ct.san_pham,
        thuong_hieu: ct.thuong_hieu || '',
        sku:         ct.sku,
        gia_nhap:    ct.gia_nhap,
        so_luong:    ct.so_luong,
        is_new:      false,
      }));
      renderTable(); updateSummary();
    }

    // Search box
    const s = document.getElementById('pn_sp_search');
    if (s) {
      s.addEventListener('input', debounce(onSearch, 280));
      s.addEventListener('keydown', e => { if (e.key === 'Escape') closeDD(); });
    }
    document.addEventListener('click', e => {
      if (!e.target.closest('.pn-search-wrap')) closeDD();
    });

    // Sync NCC ngay khi load (nếu đang edit)
    pnSyncNcc();
    pnSyncTT();
  }

  /* ══════════════════════════════════════
     SYNC PHIẾU TRÁI ← FORM PHẢI
  ══════════════════════════════════════ */
  window.pnSyncNcc = function () {
    const sel  = document.getElementById('pn_ncc');
    const opt  = sel.selectedOptions[0];
    const name = opt && opt.dataset.name ? opt.dataset.name : '—';
    setText('ph_ncc_display', name);
  };

  window.pnSyncTT = function () {
    const val = document.getElementById('pn_tt').value;
    const map = {
      draft:     ['draft',     '📝 Nháp'],
      confirmed: ['confirmed', '✅ Xác nhận'],
      done:      ['done',      '✔ Hoàn tất'],
      cancelled: ['cancelled', '✖ Huỷ'],
    };
    const [cls, label] = map[val] || ['draft', '📝 Nháp'];
    const el = document.getElementById('ph_tt_display');
    if (el) el.innerHTML = `<span class="pn-status ${cls}">${label}</span>`;
  };

  window.pnSyncGhiChu = function () {
    const v = (document.getElementById('pn_ghichu').value || '').trim();
    setText('ph_ghichu_display', v || '—');
  };

  /* ══════════════════════════════════════
     TÌM SẢN PHẨM
  ══════════════════════════════════════ */
  function onSearch() {
    const q = (document.getElementById('pn_sp_search').value || '').trim().toLowerCase();
    const dd = document.getElementById('pn_dropdown');
    hide('pn_not_found'); hide('pn_bt_section');

    if (q.length < 1) { dd.style.display = 'none'; return; }

    const hits = PN_SP_LIST.filter(s => s.TenSanPham.toLowerCase().includes(q)).slice(0, 10);
    dd.innerHTML = '';

    if (!hits.length) {
      dd.innerHTML = `<li class="pn-dropdown-empty">Không tìm thấy — nhập để thêm mới</li>`;
      dd.style.display = 'block';
      // Hiện nút thêm mới
      document.getElementById('pn_nf_name').textContent = document.getElementById('pn_sp_search').value.trim();
      show('pn_not_found');
      return;
    }

    hits.forEach(sp => {
      const li = document.createElement('li');
      li.innerHTML = `<span>${sp.TenSanPham}</span><small>${sp['id_ThuongHieu__TenThuongHieu'] || ''}</small>`;
      li.addEventListener('click', () => onSelectSp(sp));
      dd.appendChild(li);
    });
    dd.style.display = 'block';
  }

  function closeDD() {
    const dd = document.getElementById('pn_dropdown');
    if (dd) dd.style.display = 'none';
  }

  async function onSelectSp(sp) {
    document.getElementById('pn_sp_search').value = sp.TenSanPham;
    closeDD(); hide('pn_not_found');
    selSpId = sp.id_SanPham; selSpName = sp.TenSanPham;

    // Load biến thể
    const btSel = document.getElementById('pn_bt_select');
    btSel.innerHTML = '<option value="">⏳ Đang tải...</option>';
    btSel.disabled = true;
    show('pn_bt_section');

    try {
      const res = await fetch(`${PN_BT_URL}?sp_id=${sp.id_SanPham}`);
      const data = await res.json();
      btSel.innerHTML = '<option value="">— Chọn biến thể —</option>';
      if (data.ok && data.data.length) {
        data.data.forEach(bt => {
          const o = document.createElement('option');
          o.value = bt.id;
          o.dataset.info = JSON.stringify(bt);
          o.textContent = `${bt.sku}  |  ${fmtP(bt.gia_nhap)}  |  Tồn: ${bt.ton_kho}`;
          btSel.appendChild(o);
        });
        btSel.disabled = false;
      } else {
        btSel.innerHTML = '<option value="">Không có biến thể</option>';
      }
    } catch {
      btSel.innerHTML = '<option value="">Lỗi tải</option>';
    }
    hide('pn_bt_preview');
  }

  window.pnOnBtChange = function () {
    const sel = document.getElementById('pn_bt_select');
    const opt = sel.selectedOptions[0];
    const prev = document.getElementById('pn_bt_preview');
    if (!opt || !opt.dataset.info) { prev.style.display = 'none'; return; }

    const info = JSON.parse(opt.dataset.info);
    document.getElementById('pn_gianhap').value = info.gia_nhap || 0;

    prev.style.display = 'block';
    prev.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
        <div><span style="color:#999;font-size:10px;display:block;">SKU</span><strong>${info.sku}</strong></div>
        <div><span style="color:#999;font-size:10px;display:block;">Tồn kho</span>
          <strong style="color:${info.ton_kho < 10 ? '#c62828' : '#2e7d32'}">${info.ton_kho}</strong></div>
        <div><span style="color:#999;font-size:10px;display:block;">Giá nhập</span><strong>${fmtP(info.gia_nhap)}</strong></div>
        <div><span style="color:#999;font-size:10px;display:block;">Giá bán</span><strong>${fmtP(info.gia_ban)}</strong></div>
        ${info.attrs ? `<div style="grid-column:1/-1"><span style="color:#999;font-size:10px;display:block;">Thuộc tính</span>${info.attrs}</div>` : ''}
      </div>`;
  };

  /* ══════════════════════════════════════
     THÊM DÒNG VÀO PHIẾU
  ══════════════════════════════════════ */
  window.pnAddRow = function () {
    const btSel  = document.getElementById('pn_bt_select');
    const btId   = parseInt(btSel.value, 10);
    const sl     = parseInt(document.getElementById('pn_soluong').value, 10) || 1;
    const gn     = parseFloat(document.getElementById('pn_gianhap').value) || 0;

    if (!btId)   { alert('Vui lòng chọn biến thể!'); return; }
    if (sl <= 0) { alert('Số lượng phải > 0!'); return; }

    const opt  = btSel.selectedOptions[0];
    const info = opt.dataset.info ? JSON.parse(opt.dataset.info) : {};

    rows.push({
      bien_the_id: btId,
      san_pham:    selSpName,
      sku:         info.sku || opt.textContent,
      gia_nhap:    gn, so_luong: sl,
      is_new:      false,
    });

    renderTable(); updateSummary();

    // Reset form bên phải
    document.getElementById('pn_sp_search').value = '';
    btSel.innerHTML = '<option value="">— Chọn biến thể —</option>';
    btSel.disabled = true;
    document.getElementById('pn_soluong').value = 1;
    document.getElementById('pn_gianhap').value = 0;
    document.getElementById('pn_bt_preview').style.display = 'none';
    hide('pn_bt_section'); hide('pn_not_found');
    selSpId = null; selSpName = '';
  };

  /* ══════════════════════════════════════
     RENDER BẢNG PHIẾU (bên trái)
  ══════════════════════════════════════ */
  function renderTable() {
    const tbody = document.getElementById('ph_tbody');
    const emptyRow = document.getElementById('ph_empty_row');

    if (!rows.length) {
      tbody.innerHTML = '';
      tbody.appendChild(emptyRow);
      emptyRow.style.display = '';
      return;
    }
    if (emptyRow) emptyRow.style.display = 'none';
    tbody.innerHTML = '';

    rows.forEach((r, i) => {
      const tt = r.gia_nhap * r.so_luong;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="color:#aaa;font-size:11px;">${i + 1}</td>
        <td>
          <strong style="font-size:13px;">${r.san_pham}</strong>
          ${r.is_new ? '<span class="pn-badge-new">MỚI</span>' : ''}
          ${r.thuong_hieu ? `<br><small style="color:#888;">${r.thuong_hieu}</small>` : ''}
        </td>
        <td><code style="background:#f0f4ea;padding:2px 7px;border-radius:4px;font-size:11px;">${r.sku}</code></td>
        <td class="r">
          <input type="number" value="${r.gia_nhap}" min="0" style="width:100px;"
            onchange="pnUpdRow(${i},'gia_nhap',this.value)">
        </td>
        <td class="r">
          <input type="number" value="${r.so_luong}" min="1" style="width:64px;"
            onchange="pnUpdRow(${i},'so_luong',this.value)">
        </td>
        <td class="r num" id="row_tt_${i}">${fmtP(tt)}</td>
        <td>
          <button class="pn-btn pn-btn-d" onclick="pnDelRow(${i})">✕</button>
        </td>`;
      tbody.appendChild(tr);
    });
  }

  window.pnUpdRow = function (i, field, val) {
    rows[i][field] = parseFloat(val) || 0;
    const el = document.getElementById(`row_tt_${i}`);
    if (el) el.textContent = fmtP(rows[i].gia_nhap * rows[i].so_luong);
    updateSummary();
  };
  window.pnDelRow = function (i) {
    rows.splice(i, 1);
    renderTable(); updateSummary();
  };

  function updateSummary() {
    const existRows = rows.filter(r => !r.is_new);
    const newRows   = rows.filter(r => r.is_new);
    let total = 0, qty = 0;
    rows.forEach(r => { total += r.gia_nhap * r.so_luong; qty += r.so_luong; });

    setText('ph_tong', fmtP(total));
    setText('ph_qty_summary', `${existRows.length} sản phẩm hiện có · ${newRows.length} mới · ${qty} đơn vị`);
  }

  /* ══════════════════════════════════════
     SẢN PHẨM MỚI — accordion
  ══════════════════════════════════════ */
  let pendingNewName = '';

  window.pnShowNewProduct = function () {
    pendingNewName = document.getElementById('pn_sp_search').value.trim();
    document.getElementById('pn_np_ten').value      = pendingNewName;
    document.getElementById('pn_np_name_title').textContent = pendingNewName;
    document.getElementById('pn_np_brand').value    = '';
    document.getElementById('pn_np_bt_list').innerHTML = '';
    show('pn_new_sp_form');
    hide('pn_not_found');
    document.getElementById('pn_acc_body').classList.remove('hidden');
    document.getElementById('pn_acc_chevron').textContent = '▼';
    pnAddNewBT();
  };

  window.pnToggleAcc = function () {
    const body    = document.getElementById('pn_acc_body');
    const chevron = document.getElementById('pn_acc_chevron');
    const h = body.classList.toggle('hidden');
    chevron.textContent = h ? '▶' : '▼';
  };

  window.pnCancelNew = function () {
    hide('pn_new_sp_form');
    document.getElementById('pn_sp_search').value = '';
    selSpId = null; selSpName = '';
  };

  window.pnAddNewBT = function () {
    const idx = btNewIdx++;
    const c   = document.getElementById('pn_np_bt_list');
    const d   = document.createElement('div');
    d.className = 'pn-bt-item';
    d.id = `np_bt_${idx}`;
    d.innerHTML = `
      <button class="pn-bt-rm" onclick="document.getElementById('np_bt_${idx}').remove()">✕</button>
      <div class="pn-row" style="margin-bottom:8px;">
        <div class="pn-f">
          <label>Thuộc tính (VD: Dung tích)</label>
          <input type="text" class="np-attr-ten" placeholder="Dung tích">
        </div>
        <div class="pn-f">
          <label>Giá trị (VD: 50ml)</label>
          <input type="text" class="np-attr-val" placeholder="50ml">
        </div>
      </div>
      <div class="pn-row pn-row-3">
        <div class="pn-f">
          <label>SKU</label>
          <input type="text" class="np-sku" placeholder="SKU-001">
        </div>
        <div class="pn-f">
          <label>Giá nhập (₫)</label>
          <input type="number" class="np-gnhap" min="0" value="0">
        </div>
        <div class="pn-f">
          <label>Giá bán (₫)</label>
          <input type="number" class="np-gban" min="0" value="0">
        </div>
        <div class="pn-f">
          <label>Số lượng nhập</label>
          <input type="number" class="np-sl" min="1" value="1">
        </div>
      </div>`;
    c.appendChild(d);
  };

  window.pnConfirmNew = function () {
    const ten   = document.getElementById('pn_np_ten').value.trim();
    const brand = document.getElementById('pn_np_brand').value.trim();
    if (!ten) { alert('Tên sản phẩm trống!'); return; }

    const items = document.querySelectorAll('#pn_np_bt_list .pn-bt-item');
    if (!items.length) { alert('Thêm ít nhất 1 biến thể!'); return; }

    const bien_the = [];
    for (const item of items) {
      const atTen = item.querySelector('.np-attr-ten').value.trim();
      const atVal = item.querySelector('.np-attr-val').value.trim();
      const sku   = item.querySelector('.np-sku').value.trim();
      const gn    = parseFloat(item.querySelector('.np-gnhap').value) || 0;
      const gb    = parseFloat(item.querySelector('.np-gban').value)  || 0;
      const sl    = parseInt(item.querySelector('.np-sl').value)       || 1;
      bien_the.push({
        sku:    sku || `${ten}-${atVal || 'VAR'}`,
        attrs:  atTen && atVal ? [{ ten_thuoc_tinh: atTen, gia_tri: atVal }] : [],
        gia_nhap: gn, gia_ban: gb, so_luong: sl,
      });
      // Thêm vào rows để hiện trên phiếu
      rows.push({
        bien_the_id: null,          // chưa có ID thật (lưu sau)
        san_pham:    ten,
        thuong_hieu: brand,
        sku:         sku || atVal || 'NEW',
        gia_nhap:    gn,
        so_luong:    sl,
        is_new:      true,
        _np_idx:     newProducts.length,
      });
    }
    newProducts.push({ ten_san_pham: ten, thuong_hieu: brand, bien_the });

    renderTable(); updateSummary();

    // Thu gọn accordion
    document.getElementById('pn_acc_body').classList.add('hidden');
    document.getElementById('pn_acc_chevron').textContent = '▶';
    document.getElementById('pn_np_name_title').textContent = `${ten} ✔`;

    // Reset search
    document.getElementById('pn_sp_search').value = '';
    hide('pn_not_found');
  };

  /* ══════════════════════════════════════
     LƯU PHIẾU
  ══════════════════════════════════════ */
  window.pnSave = async function (forceTT) {
    const tt    = forceTT || document.getElementById('pn_tt').value;
    const nccId = parseInt(document.getElementById('pn_ncc').value) || null;
    const msg   = document.getElementById('ph_save_msg');

    const rowPayload = rows
      .filter(r => !r.is_new && r.bien_the_id)
      .map(r => ({ bien_the_id: r.bien_the_id, so_luong: r.so_luong, gia_nhap: r.gia_nhap }));

    msg.innerHTML = '⏳ Đang lưu...';

    try {
      const res  = await fetch(PN_SAVE_URL, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({
          phieu_id:     PN_PHIEU_ID,
          ncc_id:       nccId,
          trang_thai:   tt,
          rows:         rowPayload,
          new_products: newProducts,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        msg.innerHTML = `<span style="color:#2e7d32;">✔ Đã lưu phiếu <strong>${data.ma_phieu}</strong></span>`;
        setText('ph_ma_display', `Mã phiếu: ${data.ma_phieu}`);
        setTimeout(() => { window.location.href = '../'; }, 1400);
      } else {
        msg.innerHTML = `<span style="color:#c62828;">✖ ${data.error}</span>`;
      }
    } catch (e) {
      msg.innerHTML = `<span style="color:#c62828;">✖ Lỗi kết nối</span>`;
    }
  };

  /* ── Helpers ── */
  function fmtP(n) { return Math.round(parseFloat(n) || 0).toLocaleString('vi-VN') + '₫'; }
  function setText(id, v) { const e = document.getElementById(id); if (e) e.textContent = v; }
  function show(id) { const e = document.getElementById(id); if (e) e.style.display = ''; }
  function hide(id) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }
  function getCsrf() {
    const c = document.cookie.split(';').find(x => x.trim().startsWith('csrftoken='));
    return c ? decodeURIComponent(c.trim().slice('csrftoken='.length)) : '';
  }
  function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init();
})();