# menu/otp.py
import pyotp
from django.core.cache import cache
from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

OTP_TTL_SECONDS = 300  # 5 минут

def _otp_good_key(user_id: int) -> str:
    return f"otp_good:{user_id}"

def _otp_secret_key(user_id: int) -> str:
    return f"otp_secret:{user_id}"

class OTPSerializer(serializers.Serializer):
    key = serializers.CharField(min_length=6, max_length=6)

class TwoFactorViewSet(GenericViewSet):
    """
    /api/2fa/otp-secret/  -> выдать/создать секрет и otpauth://
    /api/2fa/otp-login/   -> проверить код, выставить флаг в кэше
    /api/2fa/otp-status/  -> проверить флаг
    /api/2fa/otp-logout/  -> сбросить флаг
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"], url_path="otp-secret")
    def otp_secret(self, request):
        user = request.user
        secret_key = cache.get(_otp_secret_key(user.id))
        if not secret_key:
            secret_key = pyotp.random_base32()
            # храним секрет в кэше (для учебного проекта этого достаточно)
            cache.set(_otp_secret_key(user.id), secret_key, None)

        issuer = getattr(settings, "OTP_ISSUER", "CoffeeApp")
        label = f"{issuer}:{user.username}"
        otpauth_url = pyotp.totp.TOTP(secret_key).provisioning_uri(name=label, issuer_name=issuer)

        return Response({"secret": secret_key, "otpauth_url": otpauth_url})

    @action(detail=False, methods=["POST"], url_path="otp-login", serializer_class=OTPSerializer)
    def otp_login(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        secret_key = cache.get(_otp_secret_key(user.id))
        if not secret_key:
            return Response({"success": False, "ttl_seconds": 0})

        totp = pyotp.TOTP(secret_key)
        ok = bool(totp.verify(serializer.validated_data["key"], valid_window=1))
        if ok:
            cache.set(_otp_good_key(user.id), True, OTP_TTL_SECONDS)
        return Response({"success": ok, "ttl_seconds": OTP_TTL_SECONDS if ok else 0})

    @action(detail=False, methods=["GET"], url_path="otp-status")
    def otp_status(self, request):
        ok = bool(cache.get(_otp_good_key(request.user.id), False))
        return Response({"otp_good": ok})

    @action(detail=False, methods=["POST"], url_path="otp-logout")
    def otp_logout(self, request):
        cache.delete(_otp_good_key(request.user.id))
        return Response({"success": True})
