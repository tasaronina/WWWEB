from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CustomerViewSet,
    MenuViewSet,
    OrderViewSet,
    OrderItemViewSet,
    CSRFView,
    LoginView,
    LogoutView,
    MeView,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"menu", MenuViewSet, basename="menu")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="orderitem")

urlpatterns = [
    # авторизация сессии
    path("csrf/", CSRFView.as_view(), name="csrf"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),

    # остальной API
    path("", include(router.urls)),
]
