from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Экспорт и CRUD для заказов берём из menu.api
from .api import OrdersViewSet, OrderItemsViewSet


from .views import (
    CategoryViewSet,
    CustomerViewSet,
    MenuViewSet,
    CsrfView,      
    MeView,
    LoginView,
    LogoutView,
)

router = DefaultRouter()
router.register(r"orders", OrdersViewSet, basename="orders")
router.register(r"order-items", OrderItemsViewSet, basename="order-items")

router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"menu", MenuViewSet, basename="menu")

urlpatterns = [
    path("", include(router.urls)),

    # служебные эндпоинты для фронта
    path("csrf/", CsrfView.as_view(), name="csrf"),
    path("me/", MeView.as_view(), name="me"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("users/me/", MeView.as_view(), name="users-me"),
    path("user/", MeView.as_view(), name="user-whoami"),
    path("whoami/", MeView.as_view(), name="whoami"),

    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
]
