from django.db import models


class Category(models.Model):
    name = models.TextField("Название")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name


class Menu(models.Model):
    # Делаем поле с дефолтом, чтобы Django не спрашивал,
    # чем заполнить уже существующие записи в БД
    name = models.TextField("Название", default="")
    group = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Категория",
        related_name="menus",
    )
    picture = models.ImageField("Изображение", null=True, upload_to="menus")

    class Meta:
        verbose_name = "Меню"
        verbose_name_plural = "Меню"

    def __str__(self) -> str:
        return self.name or f"Меню #{self.pk}"


class Customer(models.Model):
    name = models.TextField("Имя")
    phone = models.TextField("Телефон")
    picture = models.ImageField("Изображение", null=True, upload_to="customers")
    # user — чтобы можно было фильтровать по владельцу, но он НЕ обязателен
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class Order(models.Model):
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        verbose_name="Клиент",
        related_name="orders",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    status = models.TextField("Статус", default="NEW")  # NEW / PAID / CANCELED
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self) -> str:
        return f"Заказ #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        verbose_name="Заказ",
        related_name="items",
    )
    menu = models.ForeignKey(
        "Menu",
        on_delete=models.PROTECT,
        verbose_name="Позиция меню",
        related_name="order_items",
    )
    qty = models.IntegerField("Кол-во", default=1)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self) -> str:
        return f"{self.menu} x {self.qty} (заказ #{self.order_id})"
