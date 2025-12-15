from rest_framework import serializers
from .models import Category, Menu, Customer, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["id", "title", "group", "price", "description", "picture"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "email", "picture"]


class OrderItemSerializer(serializers.ModelSerializer):
    line_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "order", "menu", "qty", "line_price"]

    def get_line_price(self, obj):
        return float(obj.menu.price * obj.qty)


class OrderSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "user", "customer", "status", "created_at", "total_price"]
        read_only_fields = ["created_at", "user", "total_price"]

    def get_total_price(self, obj):
        total = 0
        for it in obj.items.select_related("menu").all():
            total += it.menu.price * it.qty
        return float(total)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserInfoSerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()
    username = serializers.CharField(allow_blank=True, required=False)
    is_staff = serializers.BooleanField()