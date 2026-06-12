from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'Quản lý sản phẩm'
    def _rebuild_kb():
        """Rebuild FAISS index trong background thread."""
        import threading

        def _run():
            try:
                from app.ai.knowledge_base import rebuild_index
                from app.ai.personalize import invalidate_faiss_cache

                count = rebuild_index()
                invalidate_faiss_cache()   # ← reset cache để load index mới
                print(f"[KB] Auto-rebuild xong: {count} chunks")
            except Exception as e:
                print(f"[KB] Auto-rebuild lỗi: {e}")

        threading.Thread(target=_run, daemon=True).start()
