from django.contrib.auth import authenticate, login, logout
from django.db.models import (
    F, Sum, Avg, Max, Min, Count, ExpressionWrapper, DecimalField
)
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Category, Menu, Customer, Order, OrderItem
from .serializers import (
    CategorySerializer, MenuSerializer, CustomerSerializer,
    OrderSerializer, OrderItemSerializer
)

# ---------------- CSRF & AUTH ----------------

@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    """Выдаёт/обновляет csrftoken cookie (для фронта, если нужно)."""
    return Response({"csrfToken": get_token(request)})

@csrf_exempt  # не требуем CSRF именно на логине, чтобы не падать 403
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])  # не тащим SessionAuthentication для логина
def login_view(request):
    username = request.data.get("username") or request.data.get("login") or ""
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"detail": "Неверные логин/пароль"}, status=400)
    login(request, user)
    return Response({"ok": True})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"ok": True})

@api_view(["GET"])
@permission_classes([AllowAny])
def me_view(request):
    if not request.user.is_authenticated:
        return Response({"is_authenticated": False}, status=200)
    u = request.user
    return Response({
        "is_authenticated": True,
        "id": u.id,
        "username": u.username,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    })


# ---------------- Permissions ----------------

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


# ---------------- Catalog ----------------

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("group").all().order_by("id")
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(count=Count("id"), avg=Avg("price"), max=Max("price"), min=Min("price"))
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": float(data["max"] or 0),
            "min": float(data["min"] or 0),
        })


# ---------------- Customers ----------------

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(count=Count("id"), avg=Avg("id"), max=Max("id"), min=Min("id"))
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": data["max"] or 0,
            "min": data["min"] or 0,
        })


# ---------------- Orders & Items ----------------

def _with_total_queryset(base_qs):
    money = ExpressionWrapper(
        F("items__qty") * F("items__menu__price"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    return base_qs.annotate(total=Sum(money))


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Order.objects
            .select_related("customer", "user")
            .prefetch_related("items", "items__menu")
            .order_by("-id")
        )
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            qs = qs.filter(user=self.request.user)
        return _with_total_queryset(qs)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(count=Count("id"), avg=Avg("id"), max=Max("id"), min=Min("id"))
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": data["max"] or 0,
            "min": data["min"] or 0,
        })

    @action(detail=False, methods=["post"], url_path="add-to-cart")
    def add_to_cart(self, request):
        """
        USER добавляет позицию в корзину.
        Если нет открытого заказа NEW — создаём его.
        """
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Auth required"}, status=403)

        menu_id = request.data.get("menu_id")
        qty = int(request.data.get("qty", 1) or 1)
        if qty < 1:
            qty = 1

        menu_obj = get_object_or_404(Menu, id=menu_id)

        # Находим/создаем клиента по имени пользователя
        display_name = (user.get_full_name() or user.username or "Покупатель").strip()
        customer, _ = Customer.objects.get_or_create(name=display_name)

        # Берём незакрытый заказ NEW или создаём
        order, created = Order.objects.get_or_create(
            user=user,
            status="NEW",
            defaults={"customer": customer},
        )
        if not order.customer_id:
            order.customer = customer
            order.save(update_fields=["customer"])

        # Добавляем/увеличиваем позицию
        item, created_item = OrderItem.objects.get_or_create(
            order=order, menu=menu_obj, defaults={"qty": qty}
        )
        if not created_item:
            item.qty = item.qty + qty
            item.save(update_fields=["qty"])

        ser_item = OrderItemSerializer(item)
        return Response({"ok": True, "item": ser_item.data})


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "menu").all().order_by("id")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(order__user=user)
        order_id = self.request.query_params.get("order_id")
        if order_id:
            qs = qs.filter(order_id=order_id)
        return qs.order_by("-id")
