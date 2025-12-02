# menu/urls.py
from django.urls import path, include
from .api import (
    router,

    csrf_view,
    auth_login, auth_logout, auth_me,

    otp_status, otp_secret, otp_login, otp_reset,
)

urlpatterns = [
    # системные
    path("csrf/", csrf_view, name="csrf"),
    path("auth/login/", auth_login, name="auth_login"),
    path("auth/logout/", auth_logout, name="auth_logout"),
    path("auth/me/", auth_me, name="auth_me"),

    # 2FA
    path("2fa/otp-status/", otp_status, name="otp_status"),
    path("2fa/otp-secret/", otp_secret, name="otp_secret"),
    path("2fa/otp-login/", otp_login, name="otp_login"),
    path("2fa/otp-reset/", otp_reset, name="otp_reset"),

    # CRUD
    path("", include(router.urls)),
]
