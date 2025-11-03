from django import template

register = template.Library()


@register.filter
def has_perm(user, permission_name):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # بررسی دسترسی در UserPermission
    return user.permissions.filter(permission=permission_name, granted=True).exists()