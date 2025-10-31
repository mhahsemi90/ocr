# ocr_app/management/commands/ocr_worker.py
import time
import os
import django
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocr_project.settings')
django.setup()

# Import models after Django setup
from ocr_app.models import ScanQueue

try:
    from ocr_app.universal_ocr import UniversalOCR

    ocr_engine = UniversalOCR()
    OCR_AVAILABLE = True
    print("✅ UniversalOCR با موفقیت لود شد")
except ImportError as e:
    print(f"❌ خطا در لود OCR: {e}")
    OCR_AVAILABLE = False


class Command(BaseCommand):
    help = 'Process OCR queue'

    def handle(self, *args, **options):
        if not OCR_AVAILABLE:
            self.stdout.write(
                self.style.ERROR('❌ موتور OCR در دسترس نیست. لطفا از صحت نصب کتابخانه‌ها اطمینان حاصل کنید.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('🚀 شروع پردازش صف OCR...')
        )

        while True:
            try:
                # پیدا کردن آیتم‌های در انتظار
                pending_items = ScanQueue.objects.filter(status='pending').order_by('created_at')

                if pending_items.exists():
                    self.stdout.write(f'📋 تعداد آیتم‌های در انتظار: {pending_items.count()}')

                for item in pending_items:
                    self.process_queue_item(item)

                if not pending_items.exists():
                    self.stdout.write('⏳ هیچ آیتمی در صف وجود ندارد...')

                time.sleep(10)  # بررسی هر 10 ثانیه

            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING('⏹️ توقف worker توسط کاربر...')
                )
                break
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ خطا در پردازش صف: {str(e)}')
                )
                time.sleep(30)  # در صورت خطا 30 ثانیه صبر کن

    def process_queue_item(self, item):
        """پردازش یک آیتم از صف"""
        try:
            self.stdout.write(f'🔄 در حال پردازش: {item.document.file_name}')

            # تغییر وضعیت به در حال پردازش
            item.status = 'processing'
            item.save()

            # بررسی وجود فایل
            if not item.document.original_file:
                raise FileNotFoundError('فایل اصلی وجود ندارد')

            file_path = item.document.original_file.path

            if not os.path.exists(file_path):
                raise FileNotFoundError(f'فایل در مسیر {file_path} یافت نشد')

            # پردازش OCR
            self.stdout.write(f'🔍 استخراج متن از: {item.document.file_name}')
            result = ocr_engine.extract_text(file_path)

            # بروزرسانی سند
            with transaction.atomic():
                item.document.extracted_text = result['text']
                item.document.extraction_confidence = result.get('confidence', 0)
                item.document.ocr_processed = True
                item.document.save()

                item.status = 'completed'
                item.processed_at = timezone.now()
                item.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ پردازش کامل شد: {item.document.file_name} (دقت: {result.get("confidence", 0):.2f})')
            )

        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ فایل یافت نشد: {str(e)}')
            )
            item.status = 'failed'
            item.save()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطا در پردازش {item.document.file_name}: {str(e)}')
            )
            item.status = 'failed'
            item.save()