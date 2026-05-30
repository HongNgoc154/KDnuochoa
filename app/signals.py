# app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def _rebuild_kb():
    """Rebuild FAISS index trong background thread."""
    import threading

    def _run():
        try:
            from app.ai.knowledge_base import rebuild_index
            count = rebuild_index()
            print(f"[KB] Auto-rebuild xong: {count} chunks")
        except Exception as e:
            print(f"[KB] Auto-rebuild lỗi: {e}")

    threading.Thread(target=_run, daemon=True).start()


@receiver(post_save, sender='app.SanPham')
def on_sanpham_save(sender, instance, created, **kwargs):
    action = "Thêm mới" if created else "Cập nhật"
    print(f"[KB] {action} sản phẩm: {instance.TenSanPham} → rebuild...")
    _rebuild_kb()


@receiver(post_delete, sender='app.SanPham')
def on_sanpham_delete(sender, instance, **kwargs):
    print(f"[KB] Xóa sản phẩm: {instance.TenSanPham} → rebuild...")
    _rebuild_kb()


@receiver(post_save, sender='app.BaiViet')
def on_baiviet_save(sender, instance, created, **kwargs):
    print(f"[KB] Cập nhật bài viết → rebuild...")
    _rebuild_kb()


@receiver(post_delete, sender='app.BaiViet')
def on_baiviet_delete(sender, instance, **kwargs):
    _rebuild_kb()