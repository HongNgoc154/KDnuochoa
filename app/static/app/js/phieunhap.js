/**
 * phieunhap.js v3.1 — fix hien bang bien the sau khi chon SP
 */
(function () {
  'use strict';

  let rows        = [];
  let newProducts = [];
  let selSpId     = null;
  let selSpName   = '';
  let btNewIdx    = 0;

  /* ── Init ── */
  function init() {
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
    pnSyncNcc();
    pnSyncTT();
  }

  /* ══════════════════════════════════════
     COMBOBOX SAN PHAM
  ══════════════════════════════════════ */
  window.pnFilterCombo = function () {
    const q   = (document.getElementById('pn_sp_filter').value || '').toLowerCase().trim();
    const sel = document.getElementById('pn_sp_select');
    if (!sel) return;
    let visible = 0;
    Array.from(sel.options).forEach(function(opt) {
      if (opt.value === '__new__') { opt.style.display = ''; return; }
      if (!opt.value) { opt.style.display = q ? 'none' : ''; return; }
      var match = !q
        || (opt.dataset.name  || '').toLowerCase().indexOf(q) >= 0
        || (opt.dataset.brand || '').toLowerCase().indexOf(q) >= 0;
      opt.style.display = match ? '' : 'none';
      if (match) visible++;
    });
    var nf   = document.getElementById('pn_not_found');
    var nfNm = document.getElementById('pn_nf_name');
    if (q && visible === 0) {
      if (nfNm) nfNm.textContent = document.getElementById('pn_sp_filter').value.trim();
      if (nf)   nf.style.display = '';
    } else {
      if (nf)   nf.style.display = 'none';
    }
  };

  /* Khi chon 1 option — dung onclick thay vi onchange de chac chan chay */
  window.pnOnComboSelect = function () {
    var sel = document.getElementById('pn_sp_select');
    var val = sel.value;

    if (!val) return;

    if (val === '__new__') {
      sel.value = '';
      pnShowNewProduct();
      return;
    }

    var opt    = sel.options[sel.selectedIndex];
    selSpId    = parseInt(val, 10);
    selSpName  = opt.dataset.name || opt.textContent.split('\u00b7')[0].trim();
    var brand  = opt.dataset.brand || '';

    /* Hien chip da chon */
    var chosen = document.getElementById('pn_sp_chosen');
    var chName = document.getElementById('pn_sp_chosen_name');
    if (chosen) chosen.style.display = 'flex';
    if (chName) chName.textContent   = selSpName + (brand ? ' \u00b7 ' + brand : '');

    /* An combobox */
    var filter = document.getElementById('pn_sp_filter');
    if (filter) filter.style.display = 'none';
    sel.style.display = 'none';
    hide('pn_not_found');

    /* Load bang bien the */
    loadBienTheBang(selSpId, selSpName);
  };

  window.pnClearCombo = function () {
    selSpId = null; selSpName = '';
    var sel    = document.getElementById('pn_sp_select');
    var filter = document.getElementById('pn_sp_filter');
    var chosen = document.getElementById('pn_sp_chosen');
    if (sel)    { sel.value = ''; sel.style.display = 'block'; }
    if (filter) { filter.value = ''; filter.style.display = ''; pnFilterCombo(); }
    if (chosen) chosen.style.display = 'none';
    hide('pn_bt_bang_section');
    hide('pn_not_found');
  };

  /* ══════════════════════════════════════
     BANG BIEN THE
  ══════════════════════════════════════ */
  function loadBienTheBang(spId, spName) {
    var section = document.getElementById('pn_bt_bang_section');
    var tbody   = document.getElementById('pn_bt_bang_tbody');
    var title   = document.getElementById('pn_bt_bang_title');

    if (!section || !tbody) {
      console.error('[PN] Khong tim thay #pn_bt_bang_section hoac #pn_bt_bang_tbody');
      return;
    }

    if (title) title.textContent = spName;

    /* Hien section ngay — hien loading */
    section.style.display = '';
    tbody.innerHTML =
      '<tr><td colspan="6" style="text-align:center;padding:20px;color:#999;">' +
      '\u23f3 \u0110ang t\u1ea3i bi\u1ebfn th\u1ec3...</td></tr>';

    /* Kiem tra URL */
    if (typeof PN_BT_URL === 'undefined' || !PN_BT_URL) {
      tbody.innerHTML =
        '<tr><td colspan="6" style="text-align:center;padding:12px;color:#c62828;">' +
        'L\u1ed7i: PN_BT_URL ch\u01b0a \u0111\u01b0\u1ee3c \u0111\u1ecbnh ngh\u0129a!</td></tr>';
      return;
    }

    var url = PN_BT_URL + '?sp_id=' + spId;

    fetch(url)
      .then(function(res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function(data) {
        tbody.innerHTML = '';

        if (!data.ok || !data.data || !data.data.length) {
          tbody.innerHTML =
            '<tr><td colspan="6" style="text-align:center;padding:16px;' +
            'color:#aaa;font-style:italic;">' +
            'S\u1ea3n ph\u1ea9m ch\u01b0a c\u00f3 bi\u1ebfn th\u1ec3</td></tr>';
          return;
        }

        data.data.forEach(function(bt) {
          var tr = document.createElement('tr');
          tr.dataset.btId = bt.id;
          tr.dataset.sku  = bt.sku || '';

          var tonKhoColor = (bt.ton_kho < 10) ? '#c62828' : '#2e7d32';
          var attrsHtml   = bt.attrs
            ? '<div style="font-size:10px;color:#888;margin-top:2px;">' + bt.attrs + '</div>'
            : '';

          tr.innerHTML =
            '<td>' +
              '<code style="background:#f0f4ea;padding:2px 7px;border-radius:4px;font-size:11px;">'
              + bt.sku + '</code>' + attrsHtml +
            '</td>' +
            '<td style="text-align:right;font-size:12px;color:#666;">' + fmtP(bt.gia_ban) + '</td>' +
            '<td style="text-align:right;">' +
              '<span style="color:' + tonKhoColor + ';font-weight:600;font-size:12px;">' + bt.ton_kho + '</span>' +
            '</td>' +
            '<td style="text-align:right;">' +
              '<input type="number" class="bt-gia-nhap bt-input" min="0" value="' + (bt.gia_nhap || 0) + '"' +
              ' oninput="pnUpdBtTT(this)">' +
            '</td>' +
            '<td style="text-align:right;">' +
              '<input type="number" class="bt-so-luong bt-input bt-sl" min="0" value="0"' +
              ' oninput="pnUpdBtTT(this)">' +
            '</td>' +
            '<td class="bt-tt" style="text-align:right;font-weight:600;color:#4B672D;font-size:12px;">0\u20ab</td>';

          tbody.appendChild(tr);
        });
      })
      .catch(function(err) {
        console.error('[PN] loadBienTheBang error:', err);
        tbody.innerHTML =
          '<tr><td colspan="6" style="text-align:center;padding:12px;color:#c62828;">' +
          'L\u1ed7i t\u1ea3i bi\u1ebfn th\u1ec3: ' + err.message + '</td></tr>';
      });
  }

  window.pnUpdBtTT = function (input) {
    var tr = input.closest('tr');
    var gn = parseFloat(tr.querySelector('.bt-gia-nhap').value) || 0;
    var sl = parseInt(tr.querySelector('.bt-so-luong').value)   || 0;
    var tt = tr.querySelector('.bt-tt');
    if (tt) tt.textContent = fmtP(gn * sl);
  };

  /* Nhan "Xong" — day cac dong co sl>0 sang phieu */
  window.pnBtBangXong = function () {
    var tbody = document.getElementById('pn_bt_bang_tbody');
    var trs   = tbody.querySelectorAll('tr[data-bt-id]');
    var added = 0;

    trs.forEach(function(tr) {
      var sl = parseInt(tr.querySelector('.bt-so-luong').value) || 0;
      if (sl <= 0) return;

      var btId = parseInt(tr.dataset.btId, 10);
      var sku  = tr.dataset.sku || '';
      var gn   = parseFloat(tr.querySelector('.bt-gia-nhap').value) || 0;

      var existing = rows.find(function(r) { return r.bien_the_id === btId && !r.is_new; });
      if (existing) {
        existing.so_luong += sl;
        existing.gia_nhap  = gn;
      } else {
        rows.push({
          bien_the_id: btId,
          san_pham:    selSpName,
          thuong_hieu: '',
          sku:         sku,
          gia_nhap:    gn,
          so_luong:    sl,
          is_new:      false,
        });
      }
      added++;
    });

    if (added === 0) {
      alert('Ch\u01b0a nh\u1eadp s\u1ed1 l\u01b0\u1ee3ng cho bi\u1ebfn th\u1ec3 n\u00e0o!');
      return;
    }

    renderTable();
    updateSummary();
    pnClearCombo();
    hide('pn_bt_bang_section');
  };

  /* Hien form them bien the moi cho SP hien co */
window.pnShowAddNewBT = function () {
  var form = document.getElementById('pn_add_bt_form');

  // Nếu chưa tồn tại thì tạo mới và gắn vào pn_bt_bang_section
  if (!form) {
    form = document.createElement('div');
    form.id = 'pn_add_bt_form';
    form.style.cssText =
      'margin-top:12px;background:#f5fced;border:1.5px solid #c8e6a0;' +
      'border-radius:10px;padding:14px;';
    form.innerHTML =
      '<div style="font-size:11px;font-weight:700;text-transform:uppercase;' +
      'letter-spacing:1px;color:#4B672D;margin-bottom:10px;">➕ Biến thể mới cho sản phẩm này</div>' +
      '<div class="pn-row" style="margin-bottom:8px;">' +
        '<div class="pn-f"><label>Thuộc tính</label>' +
          '<input type="text" id="addbt_attr_ten" placeholder="VD: Dung tích"></div>' +
        '<div class="pn-f"><label>Giá trị</label>' +
          '<input type="text" id="addbt_attr_val" placeholder="VD: 75ml"></div>' +
      '</div>' +
      '<div class="pn-row pn-row-3" style="margin-bottom:10px;">' +
        '<div class="pn-f"><label>SKU</label>' +
          '<input type="text" id="addbt_sku" placeholder="SKU-NEW"></div>' +
        '<div class="pn-f"><label>Giá nhập (₫)</label>' +
          '<input type="number" id="addbt_gia_nhap" min="0" value="0"></div>' +
        '<div class="pn-f"><label>Giá bán (₫)</label>' +
          '<input type="number" id="addbt_gia_ban" min="0" value="0"></div>' +
        '<div class="pn-f"><label>Số lượng nhập</label>' +
          '<input type="number" id="addbt_so_luong" min="1" value="1"></div>' +
      '</div>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end;">' +
        '<button class="pn-btn pn-btn-s pn-btn-sm" onclick="pnConfirmAddNewBT()">✓ Xác nhận</button>' +
        '<button class="pn-btn pn-btn-sm" style="background:#eee;color:#666;" ' +
          'onclick="document.getElementById(\'pn_add_bt_form\').style.display=\'none\'">Hủy</button>' +
      '</div>';

    var section = document.getElementById('pn_bt_bang_section');
    if (section) {
      section.appendChild(form);
    } else {
      document.body.appendChild(form);
    }
  }

  // Reset fields
  document.getElementById('addbt_attr_ten').value  = '';
  document.getElementById('addbt_attr_val').value  = '';
  document.getElementById('addbt_sku').value        = '';
  document.getElementById('addbt_gia_nhap').value   = '0';
  document.getElementById('addbt_gia_ban').value    = '0';
  document.getElementById('addbt_so_luong').value   = '1';

  form.style.display = '';
  document.getElementById('addbt_attr_ten').focus();
};

window.pnConfirmAddNewBT = function () {
  if (!selSpId || !selSpName) {
    alert('Chưa chọn sản phẩm!');
    return;
  }
  var atTen  = document.getElementById('addbt_attr_ten').value.trim();
  var atVal  = document.getElementById('addbt_attr_val').value.trim();
  var sku    = document.getElementById('addbt_sku').value.trim();
  var gn     = parseFloat(document.getElementById('addbt_gia_nhap').value) || 0;
  var gb     = parseFloat(document.getElementById('addbt_gia_ban').value)  || 0;
  var sl     = parseInt(document.getElementById('addbt_so_luong').value)   || 1;

  if (!atVal) { alert('Vui lòng nhập giá trị thuộc tính (VD: 75ml)!'); return; }
  if (sl <= 0) { alert('Số lượng phải lớn hơn 0!'); return; }

  // Thêm vào newProducts — gắn với SP đang chọn qua selSpId
  // Tìm xem SP này đã có trong newProducts chưa
  var npKey = '__existing__' + selSpId;
  var npIdx = newProducts.findIndex(function(p){ return p._spId === selSpId; });

  var btEntry = {
    sku:    sku || (selSpName + '-' + atVal),
    attrs:  atTen && atVal ? [{ ten_thuoc_tinh: atTen, gia_tri: atVal }] : [],
    gia_nhap: gn,
    gia_ban:  gb,
    so_luong: sl,
  };

  if (npIdx >= 0) {
    // Đã có entry cho SP này → append biến thể
    newProducts[npIdx].bien_the.push(btEntry);
  } else {
    // Tạo mới entry — dùng ten_san_pham + _spId để backend tìm đúng SP
    newProducts.push({
      ten_san_pham: selSpName,
      _spId:        selSpId,    // dùng nội bộ để track
      bien_the:     [btEntry],
    });
  }

  // Thêm vào rows để hiển thị trên phiếu
  rows.push({
    bien_the_id: null,
    san_pham:    selSpName,
    thuong_hieu: '',
    sku:         sku || atVal || 'NEW',
    gia_nhap:    gn,
    so_luong:    sl,
    is_new:      true,
  });

  renderTable();
  updateSummary();

  // Thêm row preview vào bảng biến thể (để thấy ngay)
  var tbody = document.getElementById('pn_bt_bang_tbody');
  if (tbody) {
    var tr = document.createElement('tr');
    tr.style.background = '#f0fce8';
    tr.innerHTML =
      '<td>' +
        '<code style="background:#d4f0b0;padding:2px 7px;border-radius:4px;font-size:11px;">'
        + (sku || atVal || 'NEW') + '</code>' +
        '<div style="font-size:10px;color:#4B672D;margin-top:2px;">✨ Biến thể mới · ' + (atTen ? atTen + ': ' : '') + atVal + '</div>' +
      '</td>' +
      '<td style="text-align:right;color:#4B672D;font-size:12px;">' + fmtP(gb) + '</td>' +
      '<td style="text-align:right;">—</td>' +
      '<td style="text-align:right;"><input type="number" class="bt-gia-nhap bt-input" value="' + gn + '" disabled></td>' +
      '<td style="text-align:right;"><input type="number" class="bt-so-luong bt-input" value="' + sl + '" disabled></td>' +
      '<td style="text-align:right;font-weight:600;color:#4B672D;">' + fmtP(gn * sl) + '</td>';
    tbody.appendChild(tr);
  }

  document.getElementById('pn_add_bt_form').style.display = 'none';
  alert('Đã thêm biến thể mới vào phiếu! Nhấn "Xong → Đưa vào phiếu" khi hoàn tất.');
};
  /* ══════════════════════════════════════
     SYNC PHIEU TRAI
  ══════════════════════════════════════ */
  window.pnSyncNcc = function () {
    var sel  = document.getElementById('pn_ncc');
    var opt  = sel && sel.selectedOptions[0];
    setText('ph_ncc_display', opt && opt.dataset.name  ? opt.dataset.name  : '\u2014');
    setText('ph_sdt_display', opt && opt.dataset.phone ? opt.dataset.phone : '\u2014');
  };

  window.pnSyncTT = function () {
    var val = document.getElementById('pn_tt').value;
    var map = {
      draft:     ['draft',     '\ud83d\udcdd Nh\u00e1p'],
      confirmed: ['confirmed', '\u2705 X\u00e1c nh\u1eadn'],
      done:      ['done',      '\u2714 Ho\u00e0n t\u1ea5t'],
      cancelled: ['cancelled', '\u2716 Hu\u1ef7'],
    };
    var pair  = map[val] || ['draft', '\ud83d\udcdd Nh\u00e1p'];
    var el    = document.getElementById('ph_tt_display');
    if (el) el.innerHTML = '<span class="pn-status ' + pair[0] + '">' + pair[1] + '</span>';
  };

  window.pnSyncGhiChu = function () {
    var v = (document.getElementById('pn_ghichu').value || '').trim();
    setText('ph_ghichu_display', v || '\u2014');
  };

  window.pnSearchNcc = function () {
    var input   = document.getElementById('pn_ncc_search');
    var sel     = document.getElementById('pn_ncc');
    var q       = (input.value || '').trim().toLowerCase();
    var matched = '';
    Array.from(sel.options).forEach(function(o) {
      if (!o.value) return;
      if (!matched && (o.dataset.name || '').toLowerCase().indexOf(q) >= 0) matched = o.value;
    });
    if (matched) { sel.value = matched; pnSyncNcc(); }
    else { setText('ph_ncc_display', input.value || '\u2014'); setText('ph_sdt_display', '\u2014'); }
  };

  /* ══════════════════════════════════════
     BANG PHIEU TRAI
  ══════════════════════════════════════ */
  function renderTable() {
    var tbody    = document.getElementById('ph_tbody');
    var emptyRow = document.getElementById('ph_empty_row');
    if (!rows.length) {
      tbody.innerHTML = '';
      if (emptyRow) { tbody.appendChild(emptyRow); emptyRow.style.display = ''; }
      return;
    }
    if (emptyRow) emptyRow.style.display = 'none';
    tbody.innerHTML = '';
    rows.forEach(function(r, i) {
      var tt = r.gia_nhap * r.so_luong;
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td style="color:#aaa;font-size:11px;">' + (i+1) + '</td>' +
        '<td><strong style="font-size:13px;">' + r.san_pham + '</strong>' +
          (r.is_new ? '<span class="pn-badge-new">M\u1edaI</span>' : '') +
          (r.thuong_hieu ? '<br><small style="color:#888;">' + r.thuong_hieu + '</small>' : '') +
        '</td>' +
        '<td><code style="background:#f0f4ea;padding:2px 7px;border-radius:4px;font-size:11px;">' + r.sku + '</code></td>' +
        '<td class="r"><input type="number" value="' + r.gia_nhap + '" min="0" style="width:100px;"' +
          ' onchange="pnUpdRow(' + i + ',\'gia_nhap\',this.value)"></td>' +
        '<td class="r"><input type="number" value="' + r.so_luong + '" min="1" style="width:64px;"' +
          ' onchange="pnUpdRow(' + i + ',\'so_luong\',this.value)"></td>' +
        '<td class="r num" id="row_tt_' + i + '">' + fmtP(tt) + '</td>' +
        '<td><button class="pn-btn pn-btn-d" onclick="pnDelRow(' + i + ')">\u2715</button></td>';
      tbody.appendChild(tr);
    });
  }

  window.pnUpdRow = function (i, field, val) {
    rows[i][field] = parseFloat(val) || 0;
    var el = document.getElementById('row_tt_' + i);
    if (el) el.textContent = fmtP(rows[i].gia_nhap * rows[i].so_luong);
    updateSummary();
  };
  window.pnDelRow = function (i) {
    rows.splice(i, 1); renderTable(); updateSummary();
  };

  function updateSummary() {
    var exist = rows.filter(function(r){ return !r.is_new; }).length;
    var news  = rows.filter(function(r){ return  r.is_new; }).length;
    var total = 0, qty = 0;
    rows.forEach(function(r){ total += r.gia_nhap * r.so_luong; qty += r.so_luong; });
    setText('ph_tong', fmtP(total));
    setText('ph_qty_summary', exist + ' s\u1ea3n ph\u1ea9m hi\u1ec7n c\u00f3 \u00b7 '
      + news + ' m\u1edbi \u00b7 ' + qty + ' \u0111\u01a1n v\u1ecb');
  }

  /* ══════════════════════════════════════
     SAN PHAM MOI
  ══════════════════════════════════════ */
  window.pnShowNewProduct = function () {
    var filterVal = (document.getElementById('pn_sp_filter') || {}).value || '';
    var name      = filterVal.trim();
    document.getElementById('pn_np_ten').value            = name;
    document.getElementById('pn_np_name_title').textContent = name;
    document.getElementById('pn_np_brand').value          = '';
    document.getElementById('pn_np_bt_list').innerHTML    = '';
    show('pn_new_sp_form');
    hide('pn_not_found');
    document.getElementById('pn_acc_body').classList.remove('hidden');
    document.getElementById('pn_acc_chevron').textContent = '\u25bc';
    pnAddNewBT();
  };

  window.pnToggleAcc = function () {
    var body    = document.getElementById('pn_acc_body');
    var chevron = document.getElementById('pn_acc_chevron');
    chevron.textContent = body.classList.toggle('hidden') ? '\u25b6' : '\u25bc';
  };

  window.pnCancelNew = function () {
    hide('pn_new_sp_form'); pnClearCombo();
  };

  window.pnAddNewBT = function () {
    var idx = btNewIdx++;
    var c   = document.getElementById('pn_np_bt_list');
    var d   = document.createElement('div');
    d.className = 'pn-bt-item'; d.id = 'np_bt_' + idx;
    d.innerHTML =
      '<button class="pn-bt-rm" onclick="document.getElementById(\'np_bt_' + idx + '\').remove()">\u2715</button>' +
      '<div class="pn-row" style="margin-bottom:8px;">' +
        '<div class="pn-f"><label>Thu\u1ed9c t\u00ednh</label>' +
          '<input type="text" class="np-attr-ten" placeholder="Dung t\u00edch"></div>' +
        '<div class="pn-f"><label>Gi\u00e1 tr\u1ecb</label>' +
          '<input type="text" class="np-attr-val" placeholder="50ml"></div>' +
      '</div>' +
      '<div class="pn-row pn-row-3">' +
        '<div class="pn-f"><label>SKU</label>' +
          '<input type="text" class="np-sku" placeholder="SKU-001"></div>' +
        '<div class="pn-f"><label>Gi\u00e1 nh\u1eadp (\u20ab)</label>' +
          '<input type="number" class="np-gnhap" min="0" value="0"></div>' +
        '<div class="pn-f"><label>Gi\u00e1 b\u00e1n (\u20ab)</label>' +
          '<input type="number" class="np-gban" min="0" value="0"></div>' +
        '<div class="pn-f"><label>S\u1ed1 l\u01b0\u1ee3ng nh\u1eadp</label>' +
          '<input type="number" class="np-sl" min="1" value="1"></div>' +
      '</div>';
    c.appendChild(d);
  };

  window.pnConfirmNew = function () {
    var ten   = document.getElementById('pn_np_ten').value.trim();
    var brand = document.getElementById('pn_np_brand').value.trim();
    if (!ten) { alert('T\u00ean s\u1ea3n ph\u1ea9m tr\u1ed1ng!'); return; }
    var items = document.querySelectorAll('#pn_np_bt_list .pn-bt-item');
    if (!items.length) { alert('Th\u00eam \u00edt nh\u1ea5t 1 bi\u1ebfn th\u1ec3!'); return; }

    var bien_the = [];
    items.forEach(function(item) {
      var atTen = item.querySelector('.np-attr-ten').value.trim();
      var atVal = item.querySelector('.np-attr-val').value.trim();
      var sku   = item.querySelector('.np-sku').value.trim();
      var gn    = parseFloat(item.querySelector('.np-gnhap').value) || 0;
      var gb    = parseFloat(item.querySelector('.np-gban').value)  || 0;
      var sl    = parseInt(item.querySelector('.np-sl').value)       || 1;
      bien_the.push({ sku: sku || (ten + '-' + (atVal||'VAR')),
        attrs: atTen && atVal ? [{ten_thuoc_tinh:atTen, gia_tri:atVal}] : [],
        gia_nhap:gn, gia_ban:gb, so_luong:sl });
      rows.push({ bien_the_id:null, san_pham:ten, thuong_hieu:brand,
        sku: sku||atVal||'NEW', gia_nhap:gn, so_luong:sl,
        is_new:true, _np_idx:newProducts.length });
    });
    newProducts.push({ ten_san_pham:ten, thuong_hieu:brand, bien_the:bien_the });
    renderTable(); updateSummary();

    document.getElementById('pn_acc_body').classList.add('hidden');
    document.getElementById('pn_acc_chevron').textContent = '\u25b6';
    document.getElementById('pn_np_name_title').textContent = ten + ' \u2714';
    pnClearCombo();

    var sel = document.getElementById('pn_sp_select');
    if (sel) {
      var o = document.createElement('option');
      o.value = '__pending_' + newProducts.length;
      o.dataset.name = ten; o.dataset.brand = brand;
      o.textContent  = ten + (brand ? ' \u00b7 ' + brand : '') + '  [m\u1edbi]';
      var addNew = sel.querySelector('option[value="__new__"]');
      if (addNew) sel.insertBefore(o, addNew); else sel.appendChild(o);
    }
    hide('pn_not_found');
  };

  /* ══════════════════════════════════════
     LUU PHIEU
  ══════════════════════════════════════ */
  window.pnSave = function (forceTT) {
    var tt    = forceTT || document.getElementById('pn_tt').value;
    var nccId = parseInt(document.getElementById('pn_ncc').value) || null;
    var msg   = document.getElementById('ph_save_msg');

    var rowPayload = rows.filter(function(r){ return !r.is_new && r.bien_the_id; })
      .map(function(r){ return { bien_the_id:r.bien_the_id, so_luong:r.so_luong, gia_nhap:r.gia_nhap }; });

    msg.innerHTML = '\u23f3 \u0110ang l\u01b0u...';

    fetch(PN_SAVE_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ phieu_id:PN_PHIEU_ID, ncc_id:nccId, trang_thai:tt,
        rows:rowPayload, new_products:newProducts }),
    })
    .then(function(res){ return res.json(); })
    .then(function(data) {
      if (data.ok) {
        msg.innerHTML = '<span style="color:#2e7d32;">\u2714 \u0110\u00e3 l\u01b0u phi\u1ebfu <strong>' + data.ma_phieu + '</strong></span>';
        setText('ph_ma_display', 'M\u00e3 phi\u1ebfu: ' + data.ma_phieu);
        setTimeout(function(){ window.location.href = '../'; }, 1400);
      } else {
        msg.innerHTML = '<span style="color:#c62828;">\u2716 ' + data.error + '</span>';
      }
    })
    .catch(function(e) {
      msg.innerHTML = '<span style="color:#c62828;">\u2716 L\u1ed7i k\u1ebft n\u1ed1i: ' + e.message + '</span>';
    });
  };

  /* ── Helpers ── */
  function fmtP(n) { return Math.round(parseFloat(n)||0).toLocaleString('vi-VN') + '\u20ab'; }
  function setText(id,v) { var e=document.getElementById(id); if(e) e.textContent=v; }
  function show(id) { var e=document.getElementById(id); if(e) e.style.display=''; }
  function hide(id) { var e=document.getElementById(id); if(e) e.style.display='none'; }
  function getCsrf() {
    var c=document.cookie.split(';').find(function(x){ return x.trim().startsWith('csrftoken='); });
    return c ? decodeURIComponent(c.trim().slice('csrftoken='.length)) : '';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();