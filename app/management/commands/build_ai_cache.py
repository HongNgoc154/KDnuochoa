from django.core.management.base import BaseCommand
from app.ai.recommender import build_and_cache

class Command(BaseCommand):
    help = "Build và lưu cache ma trận gợi ý sản phẩm AI"

    def handle(self, *args, **options):
        self.stdout.write("Đang build AI cache...")
        ids, _ = build_and_cache()
        self.stdout.write(
            self.style.SUCCESS(f"Hoàn thành! Đã xử lý {len(ids)} sản phẩm.")
        )