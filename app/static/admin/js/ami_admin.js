/* =============================================================
   Ami Perfumery — ami_admin.js
   File đặt tại: app/static/admin/js/ami_admin.js
   ============================================================= */

(function () {
  "use strict";

  /* ── Nhóm hương: đảm bảo checkbox hidden hoạt động đúng với label pill ── */
  function initNhomHuongPills() {
    const container = document.querySelector(".ami-field--scents ul, .nhom-huong-checks");
    if (!container) return;

    const items = container.querySelectorAll("li");
    items.forEach(function (li) {
      const checkbox = li.querySelector('input[type="checkbox"]');
      const label    = li.querySelector("label");
      if (!checkbox || !label) return;

      // Đặt label for/id khớp nhau nếu chưa có
      if (checkbox.id && !label.htmlFor) {
        label.htmlFor = checkbox.id;
      }

      // Cập nhật style ngay khi load (trường hợp edit)
      updatePillStyle(checkbox, label);

      // Lắng nghe thay đổi
      checkbox.addEventListener("change", function () {
        updatePillStyle(checkbox, label);
      });
    });
  }

  function updatePillStyle(checkbox, label) {
    if (checkbox.checked) {
      label.style.background    = "var(--ami-olive, #576238)";
      label.style.borderColor   = "var(--ami-olive, #576238)";
      label.style.color         = "#fff";
    } else {
      label.style.background    = "";
      label.style.borderColor   = "";
      label.style.color         = "";
    }
  }

  /* ── Biến thể: highlight dòng có tồn kho thấp ── */
  function highlightLowStock() {
    const soLuongCells = document.querySelectorAll(
      '.ami-form-wrap .tabular td input[name$="-SoLuong"]'
    );
    soLuongCells.forEach(function (input) {
      function check() {
        const val = parseInt(input.value, 10);
        const row = input.closest("tr");
        if (!row) return;
        row.style.background = isNaN(val)
          ? ""
          : val <= 0
            ? "#fce4ec"
            : val < 10
              ? "#fff8e1"
              : "";
      }
      check();
      input.addEventListener("input", check);
    });
  }

  /* ── Ảnh: xem trước khi chọn file ── */
  function initImagePreview() {
    const imageInputs = document.querySelectorAll(
      '.ami-form-wrap input[type="file"][name$="-url"]'
    );
    imageInputs.forEach(function (input) {
      input.addEventListener("change", function () {
        const file = input.files[0];
        if (!file) return;
        const td = input.closest("td");
        if (!td) return;
        let preview = td.querySelector(".ami-preview-img");
        if (!preview) {
          preview = document.createElement("img");
          preview.className = "ami-preview-img";
          preview.style.cssText =
            "display:block;margin-top:8px;width:72px;height:72px;" +
            "object-fit:cover;border-radius:8px;border:1px solid #e0d9cc;";
          td.appendChild(preview);
        }
        const reader = new FileReader();
        reader.onload = function (e) {
          preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      });
    });
  }

  /* ── Xác nhận xóa inline ── */
  function initDeleteConfirm() {
    document.addEventListener("click", function (e) {
      const deleteLink = e.target.closest(".inline-deletelink");
      if (!deleteLink) return;
      const checkbox = document.getElementById(deleteLink.htmlFor || deleteLink.getAttribute("for"));
      if (checkbox && !checkbox.checked) {
        if (!confirm("Bạn có chắc muốn xóa dòng này không?")) {
          e.preventDefault();
        }
      }
    });
  }

  /* ── Init khi DOM sẵn sàng ── */
  document.addEventListener("DOMContentLoaded", function () {
    initNhomHuongPills();
    highlightLowStock();
    initImagePreview();
    initDeleteConfirm();
  });
})();