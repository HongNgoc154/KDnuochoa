from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Build FAISS knowledge base index cho chatbot AI"

    def handle(self, *args, **options):
        self.stdout.write("Đang build knowledge base từ DB...")
        from app.ai.knowledge_base import rebuild_index
        count = rebuild_index()
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Hoàn thành! Đã index {count} chunks "
                    f"(sản phẩm + bài viết)."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("Không có dữ liệu để index.")
            )