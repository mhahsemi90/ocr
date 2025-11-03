# ocr_app/templatetags/permission_tags.py
from django import template

register = template.Library()


@register.filter
def has_perm(user, permission_codename):
    """بررسی دسترسی کاربر به یک permission خاص"""
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # بررسی دسترسی‌های سفارشی
    if hasattr(user, 'permissions'):
        return user.permissions.filter(
            permission=permission_codename,
            granted=True
        ).exists()

    return False