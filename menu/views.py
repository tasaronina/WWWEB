from django.views.generic import TemplateView
from django.db.models import Avg, Count, Max, Min
from django.db import transaction  # ← добавлено

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
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

    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        avg = serializers.FloatField()
        max = serializers.IntegerField()
        min = serializers.IntegerField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = Category.objects.aggregate(
            count=Count("*"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer

    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        avg = serializers.FloatField()
        max = serializers.IntegerField()
        min = serializers.IntegerField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = Customer.objects.aggregate(
            count=Count("*"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)


class MenuViewSet(ModelViewSet):
    queryset = Menu.objects.select_related("group").order_by("id")
    serializer_class = MenuSerializer

    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        avg = serializers.FloatField()
        max = serializers.FloatField()
        min = serializers.FloatField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = Menu.objects.aggregate(
            count=Count("*"),
            avg=Avg("price"),
            max=Max("price"),
            min=Min("price"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    queryset = (
        Order.objects.select_related("customer")
        .prefetch_related("items__menu")
        .order_by("-id")
    )
    serializer_class = OrderSerializer

    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        avg = serializers.FloatField()
        max = serializers.IntegerField()
        min = serializers.IntegerField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = Order.objects.aggregate(
            count=Count("*"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)

    # === ВАЖНО: корректное удаление заказа с его позициями ===
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        with transaction.atomic():
            OrderItem.objects.filter(order=obj).delete()
            return super().destroy(request, *args, **kwargs)


class OrderItemViewSet(ModelViewSet):
    serializer_class = OrderItemSerializer

    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        avg = serializers.FloatField()
        max = serializers.IntegerField()
        min = serializers.IntegerField()

    def get_queryset(self):
        qs = (
            OrderItem.objects.select_related("order", "menu", "menu__group")
            .order_by("id")
        )
        order_id = self.request.query_params.get("order_id")
        if order_id:
            try:
                qs = qs.filter(order_id=int(order_id))
            except (TypeError, ValueError):
                pass
        return qs

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = OrderItem.objects.aggregate(
            count=Count("*"),
            avg=Avg("qty"),
            max=Max("qty"),
            min=Min("qty"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)
