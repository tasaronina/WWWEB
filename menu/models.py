from django.db import models
from django.conf import settings  


class Category(models.Model):
    name = models.TextField("Название")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name


class Menu(models.Model):
    name = models.TextField("Название")
    group = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Категория",
        related_name="menus",
    )
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, default=0)
    picture = models.ImageField("Изображение", upload_to="menus", null=True, blank=True)

    class Meta:
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"

    def __str__(self) -> str:
        return self.name


class Customer(models.Model):
    name = models.TextField("Имя")
    phone = models.TextField("Телефон", null=True, blank=True)
    picture = models.ImageField("Аватар", upload_to="customers", null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Черновик"),    
        ("NEW", "Новый"),
        ("IN_PROGRESS", "В работе"),
        ("DONE", "Готов"),
        ("CANCELLED", "Отменён"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name="Клиент",
        related_name="orders",
        null=True,
        blank=True,               
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    status = models.CharField("Статус", choices=STATUS_CHOICES, default="DRAFT", max_length=20)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Пользователь",
        related_name="orders",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"Заказ #{self.pk or ''}".strip()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, verbose_name="Заказ", related_name="items"
    )
    menu = models.ForeignKey(
        Menu,
        on_delete=models.PROTECT,
        verbose_name="Позиция меню",
        related_name="order_items",
        null=True,                 
        blank=True,
    )
    qty = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self) -> str:
        return f"{self.menu} × {self.qty}"


class Profile(models.Model):
    ROLE_USER = "USER"
    ROLE_ADMIN = "ADMIN"
    ROLE_CHOICES = (
        (ROLE_USER, "Пользователь"),
        (ROLE_ADMIN, "Админ"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)

 
    opt_key = models.CharField("OTP-секрет", max_length=64, blank=True, null=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Profile<{self.user.username}>"
