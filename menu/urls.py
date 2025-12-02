# menu/urls.py
from django.urls import path, include
from .api import (
    router,

    # системные
    csrf_view,
    auth_login, auth_logout, auth_me,

    # 2FA
    otp_status, otp_secret, otp_login, otp_reset,

    # для явных путей кастомных экшенов
    OrderItemViewSet,
)

urlpatterns = [
    # системные
    path("csrf/", csrf_view, name="csrf"),
    path("auth/login/",  auth_login,  name="auth_login"),
    path("auth/logout/", auth_logout, name="auth_logout"),
    path("auth/me/",     auth_me,     name="auth_me"),

    # 2FA
    path("2fa/otp-status/", otp_status, name="otp_status"),
    path("2fa/otp-secret/", otp_secret, name="otp_secret"),
    path("2fa/otp-login/",  otp_login,  name="otp_login"),
    path("2fa/otp-reset/",  otp_reset,  name="otp_reset"),

    # ЯВНЫЕ пути на кастомные экшены (чтобы не ловить 404 ни при каких условиях)
    path("order-items/stats/",  OrderItemViewSet.as_view({"get": "stats"}),  name="order-items-stats"),
    path("order-items/export/", OrderItemViewSet.as_view({"get": "export"}), name="order-items-export"),

    # CRUD DRF
    path("", include(router.urls)),
]
