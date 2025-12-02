# menu/views.py
from django.contrib.auth import authenticate, login, logout
from django.db.models import F, Sum, Avg, Max, Min, Count, ExpressionWrapper, DecimalField
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token

from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Category, Menu, Customer, Order, OrderItem
from .serializers import (
    CategorySerializer, MenuSerializer, CustomerSerializer,
    OrderSerializer, OrderItemSerializer
)
from .permissions import (
    IsAdminOrReadOnly,
    DoubleAuthRequired,
    AllowUserWriteOrAdminWithOTP,
    IsOwnerOrAdmin,
)

from django.views.generic import TemplateView

class ShowMenuView(TemplateView):
    template_name = "menu/show_menu.html"
# ---------------- CSRF & AUTH ----------------

@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_view(request):
    return Response({"csrfToken": get_token(request)})

@api_view(["POST"])
@permission_classes([AllowAny])
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
# (IsAdminOrReadOnly и DoubleAuthRequired берутся из permissions.py)

# ---------------- Catalog ----------------

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly, DoubleAuthRequired]

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.select_related("group").all().order_by("id")
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly, DoubleAuthRequired]

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

# ---------------- Orders & Items ----------------

def _with_total_queryset(base_qs):
    money = ExpressionWrapper(
        F("items__qty") * F("items__menu__price"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    return base_qs.annotate(total=Sum(money))

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, AllowUserWriteOrAdminWithOTP, IsOwnerOrAdmin]

    def get_queryset(self):
        qs = (
            Order.objects
            .select_related("customer", "user")
            .prefetch_related("items", "items__menu")
            .order_by("-id")
        )
        u = self.request.user
        if not (u.is_staff or u.is_superuser):
            qs = qs.filter(user=u)
        return _with_total_queryset(qs)

    def get_permissions(self):
        """
        list/retrieve — только IsAuthenticated (на уровне класса уже есть остальное);
        add_to_cart — разрешаем без 2FA (для пользователя);
        остальное — как задано в permission_classes.
        """
        if getattr(self, "action", None) in ("list", "retrieve"):
            return [IsAuthenticated()]
        if getattr(self, "action", None) == "add_to_cart":
            return [IsAuthenticated()]  # корзина без 2FA
        return [p() if isinstance(p, type) else p for p in self.permission_classes]

    def perform_create(self, serializer):
        u = self.request.user
        if not (u.is_staff or u.is_superuser):
            serializer.save(user=u)
        else:
            serializer.save()

    def perform_update(self, serializer):
        u = self.request.user
        instance = self.get_object()
        if not (u.is_staff or u.is_superuser) and instance.user_id != u.id:
            raise PermissionDenied("Можно редактировать только свой заказ")
        serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if not (u.is_staff or u.is_superuser) and instance.user_id != u.id:
            raise PermissionDenied("Можно удалять только свой заказ")
        instance.delete()

    @action(detail=False, methods=["post"], url_path="add-to-cart")
    def add_to_cart(self, request):
        """
        Ожидает: {menu_id, qty, order_id? , new_order?}
        Создаёт заказ (если нужно) и OrderItem.
        """
        menu_id = int(request.data.get("menu_id") or 0)
        qty = max(1, int(request.data.get("qty") or 1))
        order_id = request.data.get("order_id")
        new_order = bool(request.data.get("new_order"))

        menu_obj = get_object_or_404(Menu, pk=menu_id)

        order = None
        if order_id and not new_order:
            order = get_object_or_404(Order, pk=order_id)
            # пользователь не может добавлять в чужой заказ
            u = request.user
            if not (u.is_staff or u.is_superuser) and order.user_id != u.id:
                raise PermissionDenied("Нельзя добавлять позиции в чужой заказ")
        else:
            order = Order.objects.create(user=request.user)

        item = OrderItem.objects.create(order=order, menu=menu_obj, qty=qty)

        return Response({
            "ok": True,
            "order_id": order.id,
            "item": {
                "id": item.id,
                "order": order.id,
                "menu": menu_obj.id,
                "qty": item.qty,
            }
        })


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "menu").all().order_by("id")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated, AllowUserWriteOrAdminWithOTP, IsOwnerOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if not (u.is_staff or u.is_superuser):
            qs = qs.filter(order__user=u)
        order_id = self.request.query_params.get("order_id")
        if order_id:
            qs = qs.filter(order_id=order_id)
        return qs.order_by("-id")

    def perform_create(self, serializer):
        u = self.request.user
        order = serializer.validated_data.get("order")
        if order and not (u.is_staff or u.is_superuser) and order.user_id != u.id:
            raise PermissionDenied("Нельзя добавлять позиции в чужой заказ")
        serializer.save()

    def perform_update(self, serializer):
        u = self.request.user
        instance = self.get_object()
        if not (u.is_staff or u.is_superuser) and instance.order.user_id != u.id:
            raise PermissionDenied("Можно менять только свои позиции заказа")
        serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if not (u.is_staff or u.is_superuser) and instance.order.user_id != u.id:
            raise PermissionDenied("Можно удалять только свои позиции заказа")
        instance.delete()
