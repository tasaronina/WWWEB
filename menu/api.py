from django.contrib.auth import authenticate, login, logout
from django.db.models import (
    F, Sum, Avg, Max, Min, Count, ExpressionWrapper, DecimalField
)
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Category, Menu, Customer, Order, OrderItem
from .serializers import (
    CategorySerializer, MenuSerializer, CustomerSerializer,
    OrderSerializer, OrderItemSerializer
)

# =========================
# CSRF & AUTH
# =========================

@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    """Отдаёт и устанавливает csrftoken-cookie."""
    return Response({"csrfToken": get_token(request)})

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Логин по SessionAuth (username/password)."""
    username = request.data.get("username") or request.data.get("login") or ""
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"detail": "Неверные логин/пароль"}, status=400)
    login(request, user)
    return Response({
        "id": user.id,
        "username": user.get_username(),
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    })

@api_view(["POST"])
def logout_view(request):
    """Выход (сброс сессии)."""
    logout(request)
    return Response({"ok": True})

@api_view(["GET"])
@permission_classes([AllowAny])
def me_view(request):
    """Информация о текущем пользователе (или пусто, если гость)."""
    if not request.user.is_authenticated:
        return Response({}, status=200)
    u = request.user
    return Response({
        "id": u.id,
        "username": u.get_username(),
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
    })

# =========================
# Permissions
# =========================

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_staff or request.user.is_superuser))

# =========================
# Helpers
# =========================

def annotate_total(qs):
    """total = SUM(items.qty * items.menu.price) как Decimal."""
    money = ExpressionWrapper(
        F("items__qty") * F("items__menu__price"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    return qs.annotate(total=Sum(money))

# =========================
# ViewSets
# =========================

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        data = self.get_queryset().aggregate(
            count=Count("id"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": data["max"] or 0,
            "min": data["min"] or 0,
        })


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("group").all().order_by("id")
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser)  # для фото

    @action(detail=False, methods=["get"])
    def stats(self, request):
        data = self.get_queryset().aggregate(
            count=Count("id"),
            avg=Avg("price"),
            max=Max("price"),
            min=Min("price"),
        )
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": float(data["max"] or 0),
            "min": float(data["min"] or 0),
        })


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser)  # для фото

    @action(detail=False, methods=["get"])
    def stats(self, request):
        data = self.get_queryset().aggregate(
            count=Count("id"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": data["max"] or 0,
            "min": data["min"] or 0,
        })


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.select_related("customer", "user") \
                          .prefetch_related("items", "items__menu")
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(user=user)
        return annotate_total(qs).order_by("-id")

    @action(detail=False, methods=["get"])
    def stats(self, request):
        data = self.get_queryset().aggregate(
            count=Count("id"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": data["max"] or 0,
            "min": data["min"] or 0,
        })

    @action(detail=False, methods=["post"], url_path="add-to-cart")
    def add_to_cart(self, request):
        """Добавление позиции в корзину текущего пользователя (status=NEW)."""
        if not request.user.is_authenticated:
            return Response({"detail": "Auth required"}, status=403)

        menu_id = request.data.get("menu_id")
        qty = int(request.data.get("qty", 1) or 1)
        if qty < 1:
            qty = 1

        menu_obj = get_object_or_404(Menu, id=menu_id)

        # Подвязываем клиента (если нет — создаём базового по имени пользователя)
        name = (request.user.get_full_name() or request.user.get_username() or "Покупатель").strip()
        customer, _ = Customer.objects.get_or_create(name=name)

        # Берём/создаём незакрытый заказ пользователя
        order, created = Order.objects.get_or_create(
            user=request.user, status="NEW", defaults={"customer": customer}
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

        return Response({"ok": True, "item": OrderItemSerializer(item).data}, status=200)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "menu").all().order_by("id")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(order__user=user)
        return qs.order_by("-id")

    @action(detail=False, methods=["get"])
    def stats(self, request):
        data = self.get_queryset().aggregate(
            count=Count("id"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        return Response({
            "count": data["count"] or 0,
            "avg": float(data["avg"] or 0),
            "max": data["max"] or 0,
            "min": data["min"] or 0,
        })
