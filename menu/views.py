from django.views.generic import TemplateView
from rest_framework.viewsets import ModelViewSet

from .models import Category, Customer, Menu, Order, OrderItem
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    MenuSerializer,
    OrderSerializer,
    OrderItemSerializer,
)


class ShowMenuView(TemplateView):
    template_name = "menu/show_menu.html"


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer


class MenuViewSet(ModelViewSet):
    queryset = Menu.objects.select_related("group").order_by("id")
    serializer_class = MenuSerializer


class OrderViewSet(ModelViewSet):
    queryset = (
        Order.objects.select_related("customer")
        .prefetch_related("items__menu")
        .order_by("-id")
    )
    serializer_class = OrderSerializer


class OrderItemViewSet(ModelViewSet):
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        qs = (
            OrderItem.objects.select_related("order", "menu", "menu__group")
            .order_by("id")
        )
        # фильтр по заказу для модалки (order_id из query-параметра)
        order_id = self.request.query_params.get("order_id")
        if order_id:
            try:
                qs = qs.filter(order_id=int(order_id))
            except (TypeError, ValueError):
                pass
        return qs
