# decorators.py
from django.http import JsonResponse
from django.shortcuts import render
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def has_permission(permission_required):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # اگر کاربر سوپر یوزر است، همه دسترسی‌ها را دارد
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # بررسی دسترسی‌های سفارشی کاربر
            if hasattr(request.user, 'permissions'):
                has_perm = request.user.permissions.filter(
                    permission=permission_required,
                    granted=True
                ).exists()
                if has_perm:
                    return view_func(request, *args, **kwargs)

            # برای درخواست‌های AJAX/JSON
            if request.headers.get(
                    'x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

            messages.error(request, 'شما دسترسی لازم برای این بخش را ندارید')
            return render(request, 'ocr_app/access_denied.html', status=403)

        return _wrapped_view

    return decorator

# دکوراتورهای اختصاصی برای هر بخش
def require_person_management(view_func):
    return has_permission('person_management')(view_func)

def require_person_detail(view_func):
    return has_permission('person_detail')(view_func)

def require_person_create(view_func):
    return has_permission('person_create')(view_func)

def require_folder_management(view_func):
    return has_permission('folder_management')(view_func)

def require_document_upload(view_func):
    return has_permission('document_upload')(view_func)

def require_document_view(view_func):
    return has_permission('document_view')(view_func)

def require_search_persons(view_func):
    return has_permission('search_persons')(view_func)

def require_search_documents(view_func):
    return has_permission('search_documents')(view_func)

def require_simple_ocr(view_func):
    return has_permission('simple_ocr')(view_func)