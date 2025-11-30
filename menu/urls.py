from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    csrf_ok,
    CategoryViewSet,
    CustomerViewSet,
    MenuViewSet,
    OrderViewSet,
    OrderItemViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"menu", MenuViewSet, basename="menu")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="orderitem")

urlpatterns = [
    path("csrf/", csrf_ok, name="csrf"),
    path("", include(router.urls)),
]
