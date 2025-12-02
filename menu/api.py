# menu/api.py
from datetime import datetime, timedelta, timezone as dt_tz
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

import pyotp

from .models import Category, Menu, Customer, Order, OrderItem, Profile
from .serializers import (
    CategorySerializer, MenuSerializer, CustomerSerializer,
    OrderSerializer, OrderItemSerializer
)
from .permissions import (
    IsAdminOrReadOnly,
    AllowUserWriteOrAdminWithOTP,
    IsOwnerOrAdmin,
    # если у тебя есть WriteRequiresOTP — можно добавить в нужные вьюсеты
)

# ===================== служебки =====================

OTP_ISSUER = getattr(settings, "OTP_ISSUER", "CafeApp")
OTP_TTL_SECONDS = int(getattr(settings, "OTP_TTL_SECONDS", 300))  # 5 минут

def _now_ts() -> int:
    return int(datetime.now(dt_tz.utc).timestamp())

def _otp_cache_key(user_id: int) -> str:
    # будем хранить ВРЕМЯ_ИСТЕЧЕНИЯ, чтобы легко считать ttl_left
    return f"otp_trusted_until:{user_id}"

def _get_profile(user) -> Profile:
    prof, _ = Profile.objects.get_or_create(user=user)
    return prof

def _ensure_secret(prof: Profile) -> Profile:
    if not getattr(prof, "opt_key", None):
        prof.opt_key = pyotp.random_base32()
        prof.save(update_fields=["opt_key"])
    return prof

def _set_trusted(user_id: int):
    until = _now_ts() + OTP_TTL_SECONDS
    cache.set(_otp_cache_key(user_id), until, timeout=OTP_TTL_SECONDS)

def _get_trusted_ttl(user_id: int) -> int:
    until = cache.get(_otp_cache_key(user_id))
    if not until:
        return 0
    ttl = int(until) - _now_ts()
    return max(0, ttl)

# ===================== CSRF & AUTH =====================

@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    return Response({"csrfToken": get_token(request)})

@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    username = (request.data.get("username") or request.data.get("login") or "").strip()
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"detail": "Неверные логин/пароль"}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    return Response({"success": True})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    logout(request)
    return Response({"success": True})

@api_view(["GET"])
@permission_classes([AllowAny])
def auth_me(request):
    if not request.user.is_authenticated:
        return Response({"authenticated": False}, status=200)

    u = request.user
    user_payload = {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    }
    return Response({
        "authenticated": True,
        "user": user_payload,
        "otp_ttl": _get_trusted_ttl(u.id),
    })

# ===================== 2FA (TOTP на Profile.opt_key) =====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def otp_status(request):
    """
    Совместимо с фронтом:
      confirmed   — есть ли секрет (создан/привязан)
      otp_good    — действует ли «доверенное» окно сейчас
      ttl_seconds — остаток секунд доверенного окна
    """
    prof = _get_profile(request.user)
    confirmed = bool(getattr(prof, "opt_key", None))
    ttl = _get_trusted_ttl(request.user.id)
    return Response({
        "confirmed": confirmed,
        "otp_good": ttl > 0,
        "ttl_seconds": ttl,
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def otp_secret(request):
    """
    Отдаёт секрет и otpauth_url.
    Не перегенерирует, если уже есть.
    """
    prof = _ensure_secret(_get_profile(request.user))
    totp = pyotp.TOTP(prof.opt_key)
    otpauth_url = totp.provisioning_uri(name=(request.user.username or str(request.user.id)), issuer_name=OTP_ISSUER)
    return Response({"secret": prof.opt_key, "otpauth_url": otpauth_url})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def otp_login(request):
    """
    Принимает { key: "123456" }.
    Проверяем код по opt_key; допускаем окно дрейфа ±1.
    При успехе — ставим «доверенное» окно (TTL) в кэше.
    """
    raw = str(request.data.get("key") or "")
    code = "".join(ch for ch in raw if ch.isdigit())[:6]
    if len(code) != 6:
        return Response({"success": False, "ttl_seconds": 0}, status=400)

    prof = _ensure_secret(_get_profile(request.user))
    ok = pyotp.TOTP(prof.opt_key).verify(code, valid_window=1)
    if not ok:
        return Response({"success": False, "ttl_seconds": 0}, status=400)

    _set_trusted(request.user.id)
    return Response({"success": True, "ttl_seconds": OTP_TTL_SECONDS})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def otp_reset(request):
    """
    Перепривязка: генерируем новый opt_key и сбрасываем доверие.
    """
    prof = _get_profile(request.user)
    prof.opt_key = pyotp.random_base32()
    prof.save(update_fields=["opt_key"])
    cache.delete(_otp_cache_key(request.user.id))
    totp = pyotp.TOTP(prof.opt_key)
    otpauth_url = totp.provisioning_uri(name=(request.user.username or str(request.user.id)), issuer_name=OTP_ISSUER)
    return Response({"secret": prof.opt_key, "otpauth_url": otpauth_url})

# ===================== CRUD ViewSets =====================

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("group").all().order_by("id")
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly]

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-id")
    serializer_class = CustomerSerializer
    permission_classes = [AllowUserWriteOrAdminWithOTP]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("customer", "user").prefetch_related("items").all().order_by("-id")
    serializer_class = OrderSerializer
    permission_classes = [AllowUserWriteOrAdminWithOTP]

    @action(detail=False, methods=["post"], url_path="add-to-cart", permission_classes=[IsAuthenticated])
    def add_to_cart(self, request):
        menu_id = request.data.get("menu_id")
        qty = int(request.data.get("qty") or 1)
        if not menu_id:
            return Response({"detail": "menu_id is required"}, status=400)
        menu_obj = get_object_or_404(Menu, pk=menu_id)

        # берём черновик текущего пользователя или создаём новый
        order = Order.objects.filter(user=request.user, status="DRAFT").order_by("-id").first()
        if order is None:
            order = Order.objects.create(user=request.user, status="DRAFT")

        item, created = OrderItem.objects.get_or_create(order=order, menu=menu_obj, defaults={"qty": max(1, qty)})
        if not created:
            item.qty += max(1, qty)
            item.save(update_fields=["qty"])

        return Response({"order_id": order.id, "item": OrderItemSerializer(item).data})

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "menu").all().order_by("-id")
    serializer_class = OrderItemSerializer
    permission_classes = [AllowUserWriteOrAdminWithOTP]

# ===================== Router =====================

router = DefaultRouter()
router.register(r"categories",  CategoryViewSet,  basename="category")
router.register(r"menu",        MenuViewSet,      basename="menu")
router.register(r"customers",   CustomerViewSet,  basename="customer")
router.register(r"orders",      OrderViewSet,     basename="order")
router.register(r"order-items", OrderItemViewSet, basename="orderitem")
