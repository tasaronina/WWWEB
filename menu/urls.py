from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import (
    # служебные эндпоинты
    csrf_view,
    login_view,
    logout_view,
    me_view,
    # ViewSet'ы
    CategoryViewSet,
    MenuViewSet,
    CustomerViewSet,
    OrderViewSet,
    OrderItemViewSet,
)

router = DefaultRouter()
router.register(r"categories",   CategoryViewSet,   basename="category")
router.register(r"menu",         MenuViewSet,       basename="menu")
router.register(r"customers",    CustomerViewSet,   basename="customer")
router.register(r"orders",       OrderViewSet,      basename="order")
router.register(r"order-items",  OrderItemViewSet,  basename="orderitem")

urlpatterns = [
    # REST роуты
    path("", include(router.urls)),

    # служебные эндпоинты
    path("csrf/",        csrf_view,   name="csrf"),
    path("auth/login/",  login_view,  name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/me/",     me_view,     name="me"),
]
