from rest_framework import serializers

from .models import Category, Customer, Menu, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class MenuSerializer(serializers.ModelSerializer):
    group = CategorySerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        source="group",
        queryset=Category.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Menu
        fields = ["id", "name", "group", "group_id", "price", "picture"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "picture", "user"]
        read_only_fields = ["user"]


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        source="customer",
        queryset=Customer.objects.all(),
        write_only=True,
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_id",
            "status",
            "created_at",
            "user",
            "total_price",
        ]
        read_only_fields = ["created_at", "user", "total_price"]

    def get_total_price(self, obj):
        total = 0
        for item in obj.items.all():
            if item.menu and item.menu.price is not None:
                total += item.menu.price * item.qty
        return float(total)


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(
        source="order",
        queryset=Order.objects.all(),
        write_only=True,
    )
    menu = MenuSerializer(read_only=True)
    menu_id = serializers.PrimaryKeyRelatedField(
        source="menu",
        queryset=Menu.objects.all(),
        write_only=True,
    )
    line_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "order_id",
            "menu",
            "menu_id",
            "qty",
            "line_price",
        ]

    def get_line_price(self, obj):
        if obj.menu and obj.menu.price is not None:
            return float(obj.menu.price * obj.qty)
        return 0.0
