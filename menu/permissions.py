from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class OTPRequiredForDelete(permissions.BasePermission):

    message = "Требуется OTP-подтверждение (second-factor) для удаления."

    def has_permission(self, request, view):
        if request.method != "DELETE":
            return True
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return False
        return bool(request.session.get("second", False))
