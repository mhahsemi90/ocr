# views.py
import json
import os

from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Person, Folder, Document, ScanQueue

try:
    from .universal_ocr import UniversalOCR
    ocr_engine = UniversalOCR()
    OCR_AVAILABLE = True
    print("✅ UniversalOCR با موفقیت لود شد")
except ImportError as e:
    print(f"❌ خطا در لود OCR: {e}")
    OCR_AVAILABLE = False


def home(request):
    """صفحه اصلی - مدیریت افراد"""
    return person_management(request)


def simple_ocr(request):
    """صفحه OCR ساده"""
    return render(request, 'ocr_app/home.html')


@csrf_exempt
def extract_text(request):
    global filename
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()

        try:
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(filename)

            if not os.path.exists(file_path):
                return JsonResponse({'error': 'فایل ذخیره نشد', 'status': 'error'})

            if OCR_AVAILABLE:
                result = ocr_engine.extract_text(file_path)
                response_data = {
                    'text': result['text'],
                    'type': result.get('type', 'unknown'),
                    'file_type': result.get('file_type', 'unknown'),
                    'confidence': round(result.get('confidence', 0), 2),
                    'status': 'success'
                }
            else:
                response_data = {
                    'text': "موتور OCR در دسترس نیست",
                    'type': 'error',
                    'file_type': 'error',
                    'confidence': 0,
                    'status': 'error'
                }

            fs.delete(filename)
            return JsonResponse(response_data)

        except Exception as e:
            if 'filename' in locals():
                fs.delete(filename)
            return JsonResponse({'error': str(e), 'status': 'error'})

    return JsonResponse({'error': 'فایلی ارسال نشده', 'status': 'error'})


@csrf_exempt
def get_root_contents(request, person_id):
    """دریافت محتوای ریشه (فایل‌های بدون پوشه و پوشه‌های اصلی)"""
    person = get_object_or_404(Person, id=person_id)

    # پوشه‌های اصلی (بدون والد)
    subfolders = person.folders.filter(parent_folder__isnull=True)

    # فایل‌های بدون پوشه
    documents = person.documents.filter(folder__isnull=True)

    return JsonResponse({
        'subfolders': [{'id': f.id, 'name': f.name} for f in subfolders],
        'documents': [{
            'id': d.id,
            'name': d.file_name,
            'processed': d.ocr_processed
        } for d in documents]
    })


@csrf_exempt
def get_person_folders(request, person_id):
    """دریافت تمام پوشه‌های یک فرد به صورت درختی"""
    person = get_object_or_404(Person, id=person_id)

    def get_folder_tree(folder=None, level=0):
        folders = []
        if folder is None:
            # پوشه‌های ریشه
            root_folders = person.folders.filter(parent_folder__isnull=True)
            for f in root_folders:
                folders.append({
                    'id': f.id,
                    'name': f.name,
                    'level': level,
                    'subfolders': get_folder_tree(f, level + 1)
                })
        else:
            # زیرپوشه‌ها
            subfolders = folder.subfolders.all()
            for f in subfolders:
                folders.append({
                    'id': f.id,
                    'name': f.name,
                    'level': level,
                    'subfolders': get_folder_tree(f, level + 1)
                })
        return folders

    folder_tree = get_folder_tree()
    return JsonResponse({'folders': folder_tree})


def document_content(request, document_id):
    """دریافت محتوای سند - نسخه اصلاح شده"""
    document = get_object_or_404(Document, id=document_id)

    # ساخت URL فایل اصلی - روش مطمئن‌تر
    original_file_url = None
    if document.original_file and hasattr(document.original_file, 'url'):
        original_file_url = request.build_absolute_uri(document.original_file.url)
        print(f"File URL: {original_file_url}")
        print(f"File path: {document.original_file.path}")
        print(f"File exists: {os.path.exists(document.original_file.path)}")

    # استفاده از propertyهای جدید
    return JsonResponse({
        'file_name': document.file_name,
        'description': document.description,
        'extracted_text': document.extracted_text,
        'confidence': document.extraction_confidence,
        'processed': document.ocr_processed,  # استفاده از فیلد واقعی
        'ocr_processed': document.ocr_processed,  # برای سازگاری
        'person_name': f"{document.person.first_name} {document.person.last_name}",
        'original_file_url': original_file_url,
        'file_extension': document.file_extension,  # استفاده از property جدید
        'file_type': document.file_type  # اضافه کردن فیلد file_type
    })


def person_management(request):
    """مدیریت افراد - صفحه اصلی"""
    persons = Person.objects.all().order_by('-created_at')
    return render(request, 'ocr_app/person_management.html', {'persons': persons})


def person_detail(request, person_id):
    """جزئیات فرد و نمایش پوشه‌ها و فایل‌ها"""
    person = get_object_or_404(Person, id=person_id)
    folders = person.folders.filter(parent_folder__isnull=True)
    documents_without_folder = person.documents.filter(folder__isnull=True)

    return render(request, 'ocr_app/person_detail.html', {
        'person': person,
        'folders': folders,
        'documents_without_folder': documents_without_folder
    })


@csrf_exempt
def create_person(request):
    """ایجاد فرد جدید"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            person, created = Person.objects.get_or_create(
                national_id=data['national_id'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'case_description': data.get('case_description', '')
                }
            )

            return JsonResponse({
                'success': True,
                'person': {
                    'id': person.id,
                    'name': f"{person.first_name} {person.last_name}",
                    'created': created
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def create_folder(request, person_id):
    """ایجاد پوشه جدید"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            person = get_object_or_404(Person, id=person_id)

            folder = Folder.objects.create(
                person=person,
                name=data['name'],
                description=data.get('description', ''),
                parent_folder_id=data.get('parent_folder_id')
            )

            return JsonResponse({'success': True, 'folder_id': folder.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def upload_documents(request, person_id):
    """آپلود اسناد جدید"""
    if request.method == 'POST':
        person = get_object_or_404(Person, id=person_id)
        uploaded_files = request.FILES.getlist('files')
        folder_id = request.POST.get('folder_id')
        description = request.POST.get('description', '')

        folder = None
        if folder_id:
            folder = get_object_or_404(Folder, id=folder_id, person=person)

        results = []
        for uploaded_file in uploaded_files:
            document = Document.objects.create(
                person=person,
                folder=folder,
                original_file=uploaded_file,
                file_name=uploaded_file.name,
                file_type=uploaded_file.name.split('.')[-1].lower(),
                description=description
            )

            # اضافه کردن به صف اسکن
            scan_queue = ScanQueue.objects.create(document=document)
            document.scan_queue_position = ScanQueue.objects.filter(status='pending').count()
            document.save()

            results.append({
                'document_id': document.id,
                'file_name': document.file_name,
                'queue_position': document.scan_queue_position
            })

        return JsonResponse({'success': True, 'documents': results})


def get_folder_contents(request, folder_id):
    """دریافت محتوای پوشه (زیرپوشه‌ها و فایل‌ها)"""
    folder = get_object_or_404(Folder, id=folder_id)
    subfolders = folder.subfolders.all()
    documents = folder.documents.all()

    return JsonResponse({
        'subfolders': [{'id': f.id, 'name': f.name} for f in subfolders],
        'documents': [{
            'id': d.id,
            'name': d.file_name,
            'processed': d.ocr_processed
        } for d in documents]
    })


def search_documents(request):
    """جستجوی پیشرفته"""
    if not any(param in request.GET for param in
               ['first_name', 'last_name', 'national_id', 'document_text', 'q', 'processing_status']):
        return render(request, 'ocr_app/search.html')

    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    national_id = request.GET.get('national_id', '')
    document_text = request.GET.get('document_text', '')
    processing_status = request.GET.get('processing_status', '')
    simple_query = request.GET.get('q', '')

    if simple_query and not any([first_name, last_name, national_id, document_text, processing_status]):
        persons = Person.objects.filter(
            Q(first_name__icontains=simple_query) |
            Q(last_name__icontains=simple_query) |
            Q(national_id__icontains=simple_query) |
            Q(case_description__icontains=simple_query)
        ).distinct()

        documents = Document.objects.filter(
            Q(file_name__icontains=simple_query) |
            Q(description__icontains=simple_query) |
            Q(extracted_text__icontains=simple_query) |
            Q(person__first_name__icontains=simple_query) |
            Q(person__last_name__icontains=simple_query)
        ).select_related('person', 'folder')
    else:
        persons_query = Person.objects.all()

        if first_name:
            persons_query = persons_query.filter(first_name__icontains=first_name)
        if last_name:
            persons_query = persons_query.filter(last_name__icontains=last_name)
        if national_id:
            persons_query = persons_query.filter(national_id__icontains=national_id)

        persons = persons_query.distinct()

        documents_query = Document.objects.all()

        if document_text:
            documents_query = documents_query.filter(
                Q(extracted_text__icontains=document_text) |
                Q(file_name__icontains=document_text) |
                Q(description__icontains=document_text)
            )

        if processing_status == 'processed':
            documents_query = documents_query.filter(ocr_processed=True)
        elif processing_status == 'pending':
            documents_query = documents_query.filter(ocr_processed=False)

        documents = documents_query.select_related('person', 'folder')

    return render(request, 'ocr_app/search_results.html', {
        'persons': persons,
        'documents': documents,
        'search_params': request.GET,
        'query': simple_query or document_text or f"{first_name} {last_name}".strip() or national_id
    })