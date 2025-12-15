from django.contrib import admin
from .models import Category, Menu, Customer, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "group", "price"]
    list_filter = ["group"]
    search_fields = ["title", "group__name"]
    autocomplete_fields = ["group"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "phone", "email"]
    search_fields = ["name", "phone", "email"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["menu"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "customer", "status", "created_at"]
    list_filter = ["status"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["user", "customer"]
    inlines = [OrderItemInline]

  
    search_fields = ["id", "user__username", "customer__name"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "menu", "qty"]
    list_filter = ["order"]
    autocomplete_fields = ["order", "menu"]

   
    search_fields = ["order__id", "menu__title"]
