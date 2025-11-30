from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets, permissions
from rest_framework.request import Request

from .models import Category, Customer, Menu, Order, OrderItem
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    MenuSerializer,
    OrderSerializer,
    OrderItemSerializer,
)


class ShowMenuView(TemplateView):
    """Простая заглушка для корневой страницы."""
    template_name = "menu/show_menu.html"


@ensure_csrf_cookie
def csrf_ok(request):
    """GET-запрос сюда выставляет csrf-cookie (`csrftoken`)."""
    return JsonResponse({"detail": "ok"})


class BaseOwnedViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet.

    - Модели БЕЗ поля user → без ограничений, доступны всем (учебный CRUD).
    - Модели С полем user:
        * анонимный пользователь → видит все (тоже для простоты в учебном проекте);
        * обычный пользователь → видит только свои записи;
        * superuser → видит всё, может фильтровать ?user=<id> или ?user=me.
    """

    permission_classes = [permissions.AllowAny]

    def _has_user_field(self) -> bool:
        qs = getattr(self, "queryset", None)
        if qs is None:
            return False
        model = qs.model
        return any(f.name == "user" for f in model._meta.get_fields())

    def get_queryset(self):
        qs = super().get_queryset()
        request: Request = self.request

        if not self._has_user_field():
            # Модель без user → не трогаем queryset
            return qs

        # Для анонима тоже показываем всё, чтобы не ломать тесты/фронт без логина
        if not request.user or not request.user.is_authenticated:
            return qs

        # superuser видит всё и может фильтровать по ?user=
        if request.user.is_superuser:
            user_param = request.query_params.get("user")
            if user_param:
                if user_param == "me":
                    return qs.filter(user=request.user)
                try:
                    return qs.filter(user_id=int(user_param))
                except ValueError:
                    return qs
            return qs

        # Обычный пользователь — только свои записи
        return qs.filter(user=request.user)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class CategoryViewSet(BaseOwnedViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer


class CustomerViewSet(BaseOwnedViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer


class MenuViewSet(BaseOwnedViewSet):
    queryset = Menu.objects.select_related("group").order_by("id")
    serializer_class = MenuSerializer


class OrderViewSet(BaseOwnedViewSet):
    queryset = (
        Order.objects.select_related("customer")
        .prefetch_related("items")
        .order_by("-id")
    )
    serializer_class = OrderSerializer


class OrderItemViewSet(BaseOwnedViewSet):
    queryset = OrderItem.objects.select_related("order", "menu").order_by("id")
    serializer_class = OrderItemSerializer
