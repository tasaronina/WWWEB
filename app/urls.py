from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from menu.views import ShowCafeView 

from menu.api import (
    CategoryViewSet,
    MenuViewSet,
    CustomerViewSet,
    OrderViewSet,
    OrderItemViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("menu", MenuViewSet, basename="menu")
router.register("customers", CustomerViewSet, basename="customers")
router.register("orders", OrderViewSet, basename="orders")
router.register("order-items", OrderItemViewSet, basename="order-items")
router.register("user", UserViewSet, basename="user")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path("", ShowCafeView.as_view(), name="show_cafe"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
