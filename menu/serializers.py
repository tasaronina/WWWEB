from rest_framework import serializers
from .models import Category, Customer, Menu, Order, OrderItem


class OwnedModelSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор:
    - если у модели есть поле user, на create проставляем текущего пользователя;
    - запрещаем менять user на update;
    - есть вспомогательный метод _limit_fk_queryset для FK-полей.
    """

    def _model_has_user(self) -> bool:
        meta = getattr(self, "Meta", None)
        model = getattr(meta, "model", None)
        if model is None:
            return False
        return any(f.name == "user" for f in model._meta.get_fields())

    def create(self, validated_data):
        request = self.context.get("request")
        if (
            self._model_has_user()
            and request
            and getattr(request, "user", None)
            and request.user.is_authenticated
        ):
            validated_data["user"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # user менять нельзя даже если он есть в модели
        if self._model_has_user():
            validated_data.pop("user", None)
        return super().update(instance, validated_data)

    def _limit_fk_queryset(self, field_name, model_cls):
        """
        Если у связанной модели есть поле user, ограничиваем выборку
        объектами текущего пользователя (для обычного пользователя).
        Для моделей без user фильтрации нет.
        """
        field = self.fields.get(field_name)
        if not field:
            return

        request = self.context.get("request")
        qs = model_cls.objects.all()

        has_user = any(f.name == "user" for f in model_cls._meta.get_fields())

        if (
            has_user
            and request
            and getattr(request, "user", None)
            and request.user.is_authenticated
            and not request.user.is_superuser
        ):
            qs = qs.filter(user=request.user)

        field.queryset = qs


class CategorySerializer(OwnedModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class CustomerSerializer(OwnedModelSerializer):
    # На фронте телефона нет, поэтому делаем поле необязательным
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "picture", "user"]


class MenuSerializer(OwnedModelSerializer):
    # Читаем человеко-понятную категорию, пишем через group_id
    from .models import Category  # для подсветки типов в IDE; можно удалить, если мешает

    group = CategorySerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="group",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Menu
        fields = ["id", "name", "group", "group_id", "picture"]


class OrderSerializer(OwnedModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer",
        write_only=True,
    )

    class Meta:
        model = Order
        fields = ["id", "customer", "customer_id", "status", "created_at", "user"]
        read_only_fields = ["created_at", "user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор клиентов по user, если поле в модели есть
        self._limit_fk_queryset("customer_id", Customer)


class OrderItemSerializer(OwnedModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source="order",
        write_only=True,
    )

    menu = MenuSerializer(read_only=True)
    menu_id = serializers.PrimaryKeyRelatedField(
        queryset=Menu.objects.all(),
        source="menu",
        write_only=True,
    )

    class Meta:
        model = OrderItem
        fields = ["id", "order", "order_id", "menu", "menu_id", "qty"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._limit_fk_queryset("order_id", Order)
        self._limit_fk_queryset("menu_id", Menu)
