from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth.models import User
from menu.models import Category, Menu, Customer, Order, OrderItem
import random

class Command(BaseCommand):
    def handle(self, *args, **options):
        fake = Faker(['ru_RU'])
        users = list(User.objects.all())
        if not users:
            users = [User.objects.create_user(username='testuser', password='password')]

        categories = ['Чай', 'Кофе', 'Напитки', 'Десерты']
        for cat_name in categories:
            Category.objects.get_or_create(name=cat_name)

        for _ in range(1000):
            category = Category.objects.order_by('?').first()
            menu_name = fake.word().capitalize()
            if not Menu.objects.filter(name=menu_name, group=category).exists():
                Menu.objects.create(
                    name=menu_name,
                    group=category,
                    picture=None 
                )

        for _ in range(1000):
            customer_name = fake.name()
            phone = fake.phone_number()
            user = random.choice(users)
            if not Customer.objects.filter(name=customer_name, phone=phone, user=user).exists():
                Customer.objects.create(
                    name=customer_name,
                    phone=phone,
                    picture=None,
                    user=user
                )

        for _ in range(1000):
            customer = Customer.objects.order_by('?').first()
            Order.objects.create(
                customer=customer,
                status='NEW',
                user=customer.user
            )

        for _ in range(1000):
            order = Order.objects.order_by('?').first()
            menu = Menu.objects.order_by('?').first()
            qty = fake.random_int(min=1, max=5)
            if not OrderItem.objects.filter(order=order, menu=menu).exists():
                OrderItem.objects.create(
                    order=order,
                    menu=menu,
                    qty=qty
                )
