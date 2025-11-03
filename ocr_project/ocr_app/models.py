import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    MUST_CHANGE_PASSWORD = models.BooleanField(default=True, verbose_name="نیاز به تغییر رمز")
    department = models.CharField(max_length=100, blank=True, verbose_name="دپارتمان")
    phone = models.CharField(max_length=15, blank=True, verbose_name="تلفن")

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"


class UserPermission(models.Model):
    PERMISSION_CHOICES = [
        ('person_management', 'مدیریت افراد'),
        ('document_upload', 'آپلود اسناد'),
        ('document_view', 'مشاهده اسناد'),
        ('search', 'جستجو'),
        ('ocr_processing', 'پردازش OCR'),
        ('user_management', 'مدیریت کاربران'),
        ('system_admin', 'مدیریت سیستم'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    granted = models.BooleanField(default=True)

    class Meta:
        verbose_name = "دسترسی کاربر"
        verbose_name_plural = "دسترسی‌های کاربران"
        unique_together = ['user', 'permission']

    def __str__(self):
        return f"{self.user.username} - {self.get_permission_display()}"


class Person(models.Model):
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="شماره پرسنلی", null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    case_description = models.TextField(verbose_name="شرح پرونده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "شخص"
        verbose_name_plural = "اشخاص"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_documents_count(self):
        return Document.objects.filter(folder__person=self).count()


class Folder(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='folders')
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='subfolders')
    name = models.CharField(max_length=255, verbose_name="نام پوشه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پوشه"
        verbose_name_plural = "پوشه‌ها"

    def __str__(self):
        return self.name


def document_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    if instance.folder:
        return f"documents/{instance.folder.person.id}/{instance.folder.id}/{filename}"
    return f"documents/{instance.person.id}/{filename}"


class Document(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    original_file = models.FileField(upload_to=document_upload_path, verbose_name="فایل اصلی")
    file_name = models.CharField(max_length=255, verbose_name="نام فایل")
    file_type = models.CharField(max_length=50, verbose_name="نوع فایل")
    description = models.TextField(blank=True, verbose_name="شرح سند")
    extracted_text = models.TextField(blank=True, verbose_name="متن استخراج شده")
    extraction_confidence = models.FloatField(default=0, verbose_name="دقت استخراج")
    ocr_processed = models.BooleanField(default=False, verbose_name="پردازش شده")
    scan_queue_position = models.IntegerField(default=0, verbose_name="موقعیت در صف")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "سند"
        verbose_name_plural = "اسناد"
        ordering = ['scan_queue_position', 'created_at']

    def __str__(self):
        return self.file_name

    # افزودن property جدید برای دسترسی آسان‌تر
    @property
    def processed(self):
        return self.ocr_processed

    @property
    def file_extension(self):
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    def get_absolute_url(self):
        if self.original_file:
            return self.original_file.url
        return ''


class ScanQueue(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق')
    ], default='pending', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "صف اسکن"
        verbose_name_plural = "صف اسکن"
