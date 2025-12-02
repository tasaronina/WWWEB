from django.contrib import admin
from .models import Category, Menu, Customer, Order, OrderItem, Profile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "group", "price")
    list_filter = ("group",)
    search_fields = ("name", "group__name")
    autocomplete_fields = ("group",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "user")
    list_filter = ("user",)
    search_fields = ("name", "phone", "user__username")
    autocomplete_fields = ("user",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("menu",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "customer", "status", "created_at")
    list_filter = ("status",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("user", "customer")
    # НУЖНО для автокомплита из OrderItemAdmin по полю order:
    search_fields = ("id", "customer__name", "user__username")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "menu", "qty")
    list_filter = ("order", "menu")
    # Чтобы работал автокомплит, у связанных админов должны быть search_fields
    autocomplete_fields = ("order", "menu")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "has_otp")
    list_filter = ("role",)
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)

    def has_otp(self, obj):
        """Есть ли привязанный секрет для 2FA."""
        return bool(obj.opt_key)
    has_otp.boolean = True
    has_otp.short_description = "2FA привязана"
