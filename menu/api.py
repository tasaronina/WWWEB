
from io import StringIO
import csv
import time

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token
from django.utils import timezone
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.conf import settings
from django.db.models import Avg, Max, Min, Count, Q

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

import pyotp

from .models import Category, Menu, Customer, Order, OrderItem, Profile
from .serializers import (
    CategorySerializer,
    MenuSerializer,
    CustomerSerializer,
    OrderSerializer,
    OrderItemSerializer,
)
from .permissions import (
    IsAdminOrReadOnly,
    WriteRequiresOTP,
    AllowUserWriteOrAdminWithOTP,
    IsOwnerOrAdmin,
)


def csrf_view(request):
    return JsonResponse({"csrfToken": get_token(request)})

@api_view(["POST"])
def auth_login(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"ok": False})
    dj_login(request, user)
    return Response({"ok": True})

@api_view(["POST"])
def auth_logout(request):
    dj_logout(request)
    return Response({"ok": True})

@api_view(["GET"])
def auth_me(request):
    u = request.user
    if not u.is_authenticated:
        return Response({"is_authenticated": False})
    return Response({
        "is_authenticated": True,
        "id": u.id,
        "username": u.get_username(),
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    })



OTP_TRUST_SECONDS = getattr(settings, "OTP_TRUST_SECONDS",
                            getattr(settings, "OTP_TRUST_TTL_SECONDS", 300))
OTP_SESSION_KEY = "otp_ok_until"

def _ensure_profile(user):
    prof, _ = Profile.objects.get_or_create(user=user)
    return prof

@api_view(["GET"])
def otp_status(request):
    ok_until = int(request.session.get(OTP_SESSION_KEY, 0))
    ttl = max(0, ok_until - int(time.time()))
    confirmed = False
    if request.user.is_authenticated:
        prof = _ensure_profile(request.user)
        confirmed = bool(getattr(prof, "opt_key", None))
    return Response({"otp_good": ttl > 0, "ttl_seconds": ttl, "confirmed": confirmed})

@api_view(["GET"])
def otp_secret(request):
    if not request.user.is_authenticated:
        return Response({"detail": "auth required"}, status=403)
    prof = _ensure_profile(request.user)
    secret = pyotp.random_base32()
   
    prof.opt_key = secret
    prof.save(update_fields=["opt_key"])
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=f"CafeApp:{request.user.username}", issuer_name="CafeApp"
    )
    return Response({"secret": secret, "otpauth_url": uri})

@api_view(["POST"])
def otp_login(request):
    if not request.user.is_authenticated:
        return Response({"success": False})
    code = (request.data.get("key") or "").strip()
    prof = _ensure_profile(request.user)
    secret = getattr(prof, "opt_key", None)
    if not secret:
        return Response({"success": False})
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        return Response({"success": False})
    now = int(time.time())
    request.session[OTP_SESSION_KEY] = now + int(OTP_TRUST_SECONDS)
    request.session.save()
    return Response({"success": True, "ttl_seconds": OTP_TRUST_SECONDS})

@api_view(["POST"])
def otp_reset(request):
    if not request.user.is_authenticated:
        return Response({"detail": "auth required"}, status=403)
    prof = _ensure_profile(request.user)
    secret = pyotp.random_base32()
    # фикс: opt_key вместо несуществующих полей
    prof.opt_key = secret
    prof.save(update_fields=["opt_key"])
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=f"CafeApp:{request.user.username}", issuer_name="CafeApp"
    )
    if OTP_SESSION_KEY in request.session:
        del request.session[OTP_SESSION_KEY]
        request.session.save()
    return Response({"secret": secret, "otpauth_url": uri})

# --- CRUD ViewSets ---

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class MenuViewSet(ModelViewSet):
    queryset = Menu.objects.select_related("group").all().order_by("id")
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly]

class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [AllowUserWriteOrAdminWithOTP]

class OrderViewSet(ModelViewSet):
    queryset = (
        Order.objects.select_related("customer", "user")
        .prefetch_related("items", "items__menu")
        .all()
        .order_by("-id")
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not u.is_authenticated:
            return qs.none()
        if u.is_staff or u.is_superuser:
            return qs
        return qs.filter(Q(user=u) | Q(customer__user=u))

    @action(detail=False, methods=["post"], url_path="add-to-cart",
            permission_classes=[IsAuthenticated | WriteRequiresOTP])
    def add_to_cart(self, request, *args, **kwargs):
        menu_id = int(request.data.get("menu_id") or 0)
        qty = max(1, int(request.data.get("qty") or 1))
        order_id = request.data.get("order_id")
        new_order = bool(request.data.get("new_order"))
        item_menu = get_object_or_404(Menu, id=menu_id)
        if order_id and not new_order:
            order = get_object_or_404(Order, id=order_id)
        else:
            customer = Customer.objects.filter(user=request.user).first() if request.user.is_authenticated else None
            order = Order.objects.create(customer=customer, user=request.user, created_at=timezone.now())
        item = OrderItem.objects.create(order=order, menu=item_menu, qty=qty, price=getattr(item_menu, "price", 0))
        return Response({
            "order_id": order.id,
            "item": OrderItemSerializer(item, context={"request": request}).data,
        })

class OrderItemViewSet(ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "menu").all().order_by("id")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not u.is_authenticated:
            return qs.none()
        if u.is_staff or u.is_superuser:
            return qs
        return qs.filter(Q(order__user=u) | Q(order__customer__user=u))

    @action(detail=False, methods=["get"], url_path="stats", url_name="stats")
    def stats(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        aggr = qs.aggregate(count=Count("id"), avg=Avg("id"), max=Max("id"), min=Min("id"))
        return Response({
            "count": aggr.get("count") or 0,
            "avg": aggr.get("avg") or 0,
            "max": aggr.get("max") or 0,
            "min": aggr.get("min") or 0,
        })

    @action(detail=False, methods=["get"], url_path="export", url_name="export")
    def export(self, request, *args, **kwargs):
        export_type = (request.query_params.get("type") or "excel").lower()
        qs = self.filter_queryset(self.get_queryset())
        rows = [("ID", "Заказ", "Позиция меню", "Кол-во")]
        for it in qs:
            rows.append((
                it.id,
                f"#{getattr(it.order, 'id', it.order_id)}",
                getattr(it.menu, "name", None)
                or getattr(it.menu, "title", None)
                or f"#{getattr(it.menu, 'id', it.menu_id)}",
                it.qty,
            ))
        if export_type == "excel":
            s = StringIO()
            s.write("sep=;\r\n")
            writer = csv.writer(s, delimiter=";", lineterminator="\r\n")
            for r in rows:
                writer.writerow(["" if v is None else str(v) for v in r])
            data = s.getvalue().encode("utf-8-sig")
            resp = HttpResponse(data, content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = "attachment; filename=order_items.csv; filename*=UTF-8''order_items.csv"
            return resp
        if export_type == "word":
            html = [
                "<html><head><meta charset='utf-8'></head><body>",
                "<h2>Позиции заказов</h2>",
                "<table border='1' cellspacing='0' cellpadding='4'>",
                "<tr>", "".join(f"<th>{c}</th>" for c in rows[0]), "</tr>",
            ]
            for r in rows[1:]:
                html.extend(["<tr>", "".join(f"<td>{c}</td>" for c in r), "</tr>"])
            html.append("</table></body></html>")
            resp = HttpResponse("".join(html), content_type="application/msword; charset=utf-8")
            resp["Content-Disposition"] = "attachment; filename=order_items.doc; filename*=UTF-8''order_items.doc"
            return resp
        return Response({"detail": "Unknown export type"}, status=400)


router = DefaultRouter()
router.register(r"categories",   CategoryViewSet,  basename="categories")
router.register(r"menu",         MenuViewSet,      basename="menu")
router.register(r"customers",    CustomerViewSet,  basename="customers")
router.register(r"orders",       OrderViewSet,     basename="orders")
router.register(r"order-items",  OrderItemViewSet, basename="order-items")
