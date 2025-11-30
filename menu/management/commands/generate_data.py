from random import randint, choice

from django.core.management.base import BaseCommand
from faker import Faker

from menu.models import Category, Menu, Customer, Order, OrderItem


class Command(BaseCommand):
    help = "Генерирует тестовые данные для категорий, меню, клиентов и заказов"

    def handle(self, *args, **options):
        fake = Faker(["ru_RU"])

        # --- Категории ---
        categories = list(Category.objects.all())
        for _ in range(5):
            category = Category.objects.create(
                name=fake.word()
            )
            categories.append(category)

        # --- Пункты меню ---
        menus = list(Menu.objects.all())
        for _ in range(50):
            menu_item = Menu.objects.create(
                name=fake.word().title(),
                group=choice(categories) if categories else None,
            )
            menus.append(menu_item)

        # --- Клиенты ---
        customers = list(Customer.objects.all())
        for _ in range(200):
            customer = Customer.objects.create(
                name=fake.name(),
                phone=fake.phone_number(),
            )
            customers.append(customer)

        # --- Заказы (основная таблица) ---
        orders_created = 0
        for _ in range(1000):
            if not customers:
                # На всякий случай, чтобы не упасть
                customer = Customer.objects.create(
                    name=fake.name(),
                    phone=fake.phone_number(),
                )
                customers.append(customer)
            else:
                customer = choice(customers)

            order = Order.objects.create(
                customer=customer,
                status="NEW",
            )
            orders_created += 1

            # Для каждого заказа создаём от 1 до 5 позиций
            items_count = randint(1, 5)
            for _ in range(items_count):
                if not menus:
                    break
                menu_item = choice(menus)
                qty = randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    menu=menu_item,
                    qty=qty,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Сгенерировано 5 категорий, 50 пунктов меню, "
                f"200 клиентов и {orders_created} заказов."
            )
        )
