import pyotp

from django.contrib.auth import authenticate, login, logout
from rest_framework import mixins, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Category, Menu, Customer, Order, OrderItem, Profile
from .serializers import (
    CategorySerializer,
    MenuSerializer,
    CustomerSerializer,
    OrderSerializer,
    OrderItemSerializer,
)




class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
     
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class CustomerViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class MenuViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
       
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff or self.request.user.is_superuser:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]




class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SecondLoginSerializer(serializers.Serializer):
    key = serializers.CharField()


class UserViewSet(GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer  

    def get_serializer_class(self):
        if self.action == "second_login":
            return SecondLoginSerializer
        if self.action == "get_info":
            # пустой сериализатор не нужен, но пусть будет тот же
            return LoginSerializer
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

        username = ser.validated_data["username"]
        password = ser.validated_data["password"]

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            request.session["second"] = False  
            return Response({"success": True})

        return Response({"success": False}, status=400)

    @action(detail=False, url_path="logout", methods=["POST"], permission_classes=[permissions.IsAuthenticated])
    def logout_user(self, request, *args, **kwargs):
        logout(request)
        request.session["second"] = False
        return Response({"status": "success"})

    @action(detail=False, url_path="get-totp", methods=["GET"], permission_classes=[permissions.IsAuthenticated])
    def get_totp(self, request, *args, **kwargs):
        # но хранение секрета в Profile
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

        code = ser.validated_data["key"].strip()
        profile, _ = Profile.objects.get_or_create(user=request.user)

        if not profile.opt_key:
            return Response({"success": False}, status=400)

        t = pyotp.totp.TOTP(profile.opt_key)
        if code == t.now():
            request.session["second"] = True
            return Response({"success": True})

        return Response({"success": False}, status=400)
