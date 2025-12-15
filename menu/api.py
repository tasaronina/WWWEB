import pyotp

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from django.contrib.auth import authenticate, login, logout
from rest_framework import permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from .models import Category, Menu, Customer, Order, OrderItem, Profile
from .serializers import (
    CategorySerializer,
    MenuSerializer,
    CustomerSerializer,
    OrderSerializer,
    OrderItemSerializer,
)



class IsStaffOrReadOnly(permissions.BasePermission):
 
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class OTPRequiredForDelete(permissions.BasePermission):

    message = "Требуется OTP-подтверждение (second-factor) для удаления."

    def has_permission(self, request, view):
        
        if request.method != "DELETE":
            return True

        
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return False

        return bool(request.session.get("second", False))




class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly, OTPRequiredForDelete]


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffOrReadOnly, OTPRequiredForDelete]


class MenuViewSet(ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsStaffOrReadOnly, OTPRequiredForDelete]


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]  

    def get_queryset(self):
        qs = super().get_queryset()

       
        if self.request.user.is_staff or self.request.user.is_superuser:
            return qs

        # обычный пользователь — только свои заказы
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
      
        serializer.save(user=self.request.user)


class OrderItemViewSet(ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    
    permission_classes = [IsStaffOrReadOnly, OTPRequiredForDelete]




class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SecondLoginSerializer(serializers.Serializer):
    key = serializers.CharField()


class UserViewSet(GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer 

    @method_decorator(ensure_csrf_cookie)
    @action(detail=False, url_path="csrf", methods=["GET"])
    def csrf(self, request, *args, **kwargs):
       
        return Response({"ok": True})

    def get_serializer_class(self):
        if self.action == "second_login":
            return SecondLoginSerializer
        return LoginSerializer

    @action(detail=False, url_path="info", methods=["GET"])
    def get_info(self, request, *args, **kwargs):
        data = {
            "username": request.user.username if request.user.is_authenticated else "",
            "is_authenticated": request.user.is_authenticated,
            "is_staff": request.user.is_staff if request.user.is_authenticated else False,
        }

        if request.user.is_authenticated:
            data["second"] = request.session.get("second") or False

        return Response(data)

    @action(detail=False, url_path="login", methods=["POST"])
    def login_user(self, request, *args, **kwargs):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        user = authenticate(
            username=ser.validated_data["username"],
            password=ser.validated_data["password"],
        )
        if user is not None:
            login(request, user)
            request.session["second"] = False  
            return Response({"success": True})

        
        return Response({"success": False})

    @action(detail=False, url_path="logout", methods=["POST"], permission_classes=[permissions.IsAuthenticated])
    def logout_user(self, request, *args, **kwargs):
        
        logout(request)
        return Response({"status": "success"})

    @action(detail=False, url_path="get-totp", methods=["GET"], permission_classes=[permissions.IsAuthenticated])
    def get_totp(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.opt_key = pyotp.random_base32()
        profile.save()

        url = pyotp.totp.TOTP(profile.opt_key).provisioning_uri(
            name=request.user.username,
            issuer_name="CafeApp",
        )
        return Response({"url": url})

    @action(detail=False, url_path="second-login", methods=["POST"], permission_classes=[permissions.IsAuthenticated])
    def second_login(self, request, *args, **kwargs):
        ser = SecondLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.opt_key:
            return Response({"success": False})

        t = pyotp.totp.TOTP(profile.opt_key)
        code = ser.validated_data["key"].strip()

        if code == t.now():
            request.session["second"] = True
            return Response({"success": True})

        return Response({"success": False})
