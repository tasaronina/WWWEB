from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    GET/HEAD/OPTIONS — всем
    POST/PUT/PATCH/DELETE — только staff/superuser
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user:
            return False

        if not request.user.is_authenticated:
            return False

        return bool(request.user.is_staff)


class OTPRequiredForDelete(permissions.BasePermission):
    """
    2FA требуется ТОЛЬКО на DELETE.
    Причём только для staff.
    """
    message = "Для удаления требуется двухфакторная аутентификация (2FA)."

    def has_permission(self, request, view):
        if request.method != "DELETE":
            return True

        if not request.user:
            return False

        if not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            second = request.session.get("second")
            return bool(second)

        return True
