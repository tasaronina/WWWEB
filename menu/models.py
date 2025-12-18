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
    title = models.TextField("Название")
    group = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        related_name="items",
        null=True,
        blank=True,
    )
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, default=0)
    description = models.TextField("Описание", blank=True, default="")
    picture = models.ImageField("Изображение", null=True, blank=True, upload_to="menus")

    class Meta:
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"

    def __str__(self) -> str:
        return self.title


class Customer(models.Model):
    name = models.TextField("ФИО")
    phone = models.TextField("Телефон", blank=True, null=True)
    email = models.EmailField("Email", blank=True, null=True)
    picture = models.ImageField("Аватар", null=True, blank=True, upload_to="customers")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("NEW", "Новый"),
        ("IN_PROGRESS", "В работе"),
        ("DONE", "Готов"),
        ("CANCELLED", "Отменён"),
    ]

    created_at = models.DateTimeField("Создан", auto_now_add=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="NEW")

  
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь",
        null=True,
        blank=True,
    )

  
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name="Клиент",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"Заказ #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )

    menu = models.ForeignKey(
        Menu,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Позиция меню",
        null=True,
        blank=True,
    )

    qty = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self) -> str:
        return f"{self.menu.title if self.menu else '—'} × {self.qty}"

class Profile(models.Model):
    ROLE_CHOICES = [
        ("USER", "Пользователь"),
        ("ADMIN", "Администратор"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    role = models.CharField("Роль", max_length=10, choices=ROLE_CHOICES, default="USER")


    opt_key = models.CharField("OTP ключ", max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self) -> str:
        return f"Профиль {self.user.username}"