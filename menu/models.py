from django.db import models


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
    picture = models.ImageField("Изображение", null=True, upload_to="menus")

    class Meta:
        verbose_name = "Меню"
        verbose_name_plural = "Меню"

    def __str__(self) -> str:
        return self.name


class Customer(models.Model):
    name = models.TextField("Имя")
    phone = models.TextField("Телефон", null=True)
    picture = models.ImageField("Аватар", null=True, upload_to="customers")
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, verbose_name="Пользователь"
    )

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

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, verbose_name="Клиент", related_name="orders"
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    status = models.TextField("Статус", choices=STATUS_CHOICES, default="NEW")
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, verbose_name="Пользователь"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self) -> str:
        return f"Заказ #{self.pk}"


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
    )
    qty = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self) -> str:
        return f"{self.menu} x {self.qty}"



class Profile(models.Model):
    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь"
    )
    ROLE_CHOICES = [
        ("USER", "Пользователь"),
        ("ADMIN", "Администратор"),
    ]
    role = models.CharField("Роль", max_length=16, choices=ROLE_CHOICES, default="USER")

    
    twofa_passed = models.BooleanField("2FA пройдена", default=False)
    twofa_expires_at = models.DateTimeField("2FA истекает", null=True, blank=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"
