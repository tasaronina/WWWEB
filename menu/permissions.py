from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Чтение — всем, запись — только staff/superuser.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return bool(u and (u.is_staff or u.is_superuser))


class IsAdmin(BasePermission):
    """
    Доступ только для staff/superuser.
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(u and (u.is_staff or u.is_superuser))
