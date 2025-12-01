from django.views.generic import TemplateView
from django.db.models import Avg, Count, Max, Min
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Category, Customer, Menu, Order, OrderItem
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    MenuSerializer,
    OrderSerializer,
    OrderItemSerializer,
)
from .permissions import IsAdminOrReadOnly


class ShowMenuView(TemplateView):
    template_name = "menu/show_menu.html"


# ---- служебные вьюхи для фронта ----

@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """
    GET /api/csrf/ — устанавливает CSRF cookie (csrftoken)
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "CSRF cookie set"})


class LoginView(APIView):
    """
    POST /api/auth/login/ {username, password}
    Если пользователь уже аутентифицирован — возвращаем OK.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        if request.user.is_authenticated:
            return Response({"detail": "already authenticated",
                             "username": request.user.username})

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Неверные логин или пароль"}, status=400)
        login(request, user)
        return Response({"detail": "ok", "username": user.username})


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({"detail": "ok"})


class MeView(APIView):
    """
    GET /api/me/ (и алиасы) — информация о текущем пользователе
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_authenticated": True,
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
            "is_admin": bool(u.is_staff or u.is_superuser),
        })


# ---- твои CRUD вьюсеты ----

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

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
        return Response(self.StatsSerializer(instance=stats).data)


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

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
        return Response(self.StatsSerializer(instance=stats).data)


class MenuViewSet(ModelViewSet):
    queryset = Menu.objects.select_related("group").order_by("id")
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly]

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
        return Response(self.StatsSerializer(instance=stats).data)


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.select_related("customer").prefetch_related("items__menu").order_by("-id")
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

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
        return Response(self.StatsSerializer(instance=stats).data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        with transaction.atomic():
            OrderItem.objects.filter(order=obj).delete()
            return super().destroy(request, *args, **kwargs)


class OrderItemViewSet(ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAdminOrReadOnly]

    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        avg = serializers.FloatField()
        max = serializers.IntegerField()
        min = serializers.IntegerField()

    def get_queryset(self):
        qs = OrderItem.objects.select_related("order", "menu", "menu__group").order_by("id")
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
        return Response(self.StatsSerializer(instance=stats).data)
