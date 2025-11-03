# ocr_app/decorators.py
from django.shortcuts import render
from functools import wraps
from django.contrib.auth.decorators import login_required


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

            # اگر دسترسی ندارد
            return render(request, 'ocr_app/access_denied.html', status=403)

        return _wrapped_view

    return decorator