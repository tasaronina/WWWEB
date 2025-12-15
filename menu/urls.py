from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import (
    csrf_view,
    CategoryViewSet,
    CustomerViewSet,
    MenuViewSet,
    OrderViewSet,
    OrderItemViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("customers", CustomerViewSet, basename="customers")
router.register("menu", MenuViewSet, basename="menu")
router.register("orders", OrderViewSet, basename="orders")
router.register("order-items", OrderItemViewSet, basename="order-items")
router.register("auth", UserViewSet, basename="auth")

urlpatterns = [
    path("csrf/", csrf_view, name="csrf"),
    path("", include(router.urls)),
]
