from django.core.cache import cache
from rest_framework.permissions import BasePermission, SAFE_METHODS



def _otp_key(user_id: int) -> str:
    return f"otp_good:{user_id}"

def _is_admin(user) -> bool:
    return bool(user and (user.is_staff or user.is_superuser))

def _is_owner(obj, user) -> bool:
    
    if not (user and user.is_authenticated):
        return False

    
    for attr in ("user", "owner", "created_by"):
        if hasattr(obj, attr):
            try:
                return getattr(obj, attr) == user
            except Exception:
                pass

    
    for parent in ("customer", "profile"):
        if hasattr(obj, parent):
            parent_obj = getattr(obj, parent)
            if hasattr(parent_obj, "user"):
                try:
                    return parent_obj.user == user
                except Exception:
                    pass

    return False



class IsAdminOrReadOnly(BasePermission):
   
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _is_admin(getattr(request, "user", None))


class WriteRequiresOTP(BasePermission):
   
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = getattr(request, "user", None)
        if not (u and u.is_authenticated):
            return False
        return bool(cache.get(_otp_key(u.id), False))


class AllowUserWriteOrAdminWithOTP(BasePermission):
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = getattr(request, "user", None)
        if not (u and u.is_authenticated):
            return False
        if _is_admin(u):
            return bool(cache.get(_otp_key(u.id), False))
        return True


class IsOwnerOrAdmin(BasePermission):
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(getattr(request, "user", None) and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        u = getattr(request, "user", None)
        return _is_admin(u) or _is_owner(obj, u)



DoubleAuthRequired = WriteRequiresOTP
OTPRequired = WriteRequiresOTP
AdminWriteNeedsOTP = WriteRequiresOTP
OwnerOrAdmin = IsOwnerOrAdmin
