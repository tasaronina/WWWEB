# menu/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from model_bakery import baker

from menu.models import Category, Menu, Customer, Order, OrderItem


class CategoryCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    # CREATE
    def test_category_create(self):
        r = self.client.post("/api/categories/", {"name": "Десерты"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.first().name, "Десерты")

    # READ (list + retrieve)
    def test_category_list_and_retrieve(self):
        cats = baker.make(Category, _quantity=3)
        r = self.client.get("/api/categories/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 3)

        r = self.client.get(f"/api/categories/{cats[1].id}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], cats[1].id)

    # UPDATE (PUT целиком)
    def test_category_update(self):
        cat = baker.make(Category, name="Старое")
        r = self.client.put(
            f"/api/categories/{cat.id}/", {"name": "Новое"}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "Новое")

    # DELETE
    def test_category_delete(self):
        cat = baker.make(Category)
        r = self.client.delete(f"/api/categories/{cat.id}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Category.objects.count(), 0)


class MenuCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat = baker.make(Category, name="Горячие напитки")

    # CREATE (обрати внимание: пишем group_id, т.к. group read_only)
    def test_menu_create(self):
        r = self.client.post(
            "/api/menu/", {"name": "Эспрессо", "group_id": self.cat.id}, format="json"
        )
        self.assertEqual(r.status_code, 201)
        obj_id = r.json()["id"]
        obj = Menu.objects.get(id=obj_id)
        self.assertEqual(obj.name, "Эспрессо")
        self.assertEqual(obj.group, self.cat)

    # READ
    def test_menu_list_and_retrieve(self):
        items = baker.make(Menu, group=self.cat, _quantity=4)
        r = self.client.get("/api/menu/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 4)

        r = self.client.get(f"/api/menu/{items[0].id}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], items[0].id)

    # UPDATE (PUT требует полный набор полей → name + group_id)
    def test_menu_update(self):
        item = baker.make(Menu, group=self.cat, name="Старое имя")
        r = self.client.put(
            f"/api/menu/{item.id}/",
            {"name": "Новое имя", "group_id": self.cat.id},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.name, "Новое имя")
        self.assertEqual(item.group, self.cat)

    # DELETE
    def test_menu_delete(self):
        # создадим 1 «Латте» и удалим именно его
        latte = baker.make(Menu, name="Латте", group=self.cat)
        _other = baker.make(Menu, group=self.cat, _quantity=2)

        r = self.client.delete(f"/api/menu/{latte.id}/")
        self.assertEqual(r.status_code, 204)
        ids = list(Menu.objects.values_list("id", flat=True))
        self.assertNotIn(latte.id, ids)


class CustomerCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_customer_crud(self):
        # CREATE
        r = self.client.post(
            "/api/customers/",
            {"name": "Алия", "phone": "+7-900-000-00-00"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        cid = r.json()["id"]

        # READ (retrieve)
        r = self.client.get(f"/api/customers/{cid}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["name"], "Алия")

        # UPDATE
        r = self.client.put(
            f"/api/customers/{cid}/",
            {"name": "Алия И.", "phone": "+7-900-000-00-00"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)

        # DELETE
        r = self.client.delete(f"/api/customers/{cid}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Customer.objects.count(), 0)


class OrderCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = baker.make(Customer)

    # CREATE
    def test_order_create(self):
        r = self.client.post(
            "/api/orders/", {"customer_id": self.customer.id, "status": "NEW"}, format="json"
        )
        self.assertEqual(r.status_code, 201)
        oid = r.json()["id"]
        obj = Order.objects.get(id=oid)
        self.assertEqual(obj.customer, self.customer)
        self.assertEqual(obj.status, "NEW")

    # READ
    def test_order_list_and_retrieve(self):
        orders = baker.make(Order, customer=self.customer, _quantity=2)
        r = self.client.get("/api/orders/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)

        r = self.client.get(f"/api/orders/{orders[0].id}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], orders[0].id)

    # UPDATE
    def test_order_update(self):
        order = baker.make(Order, customer=self.customer, status="NEW")
        r = self.client.put(
            f"/api/orders/{order.id}/",
            {"customer_id": self.customer.id, "status": "PAID"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "PAID")

    # DELETE
    def test_order_delete(self):
        order = baker.make(Order, customer=self.customer)
        r = self.client.delete(f"/api/orders/{order.id}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Order.objects.count(), 0)


class OrderItemCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat = baker.make(Category)
        self.menu = baker.make(Menu, group=self.cat)
        self.customer = baker.make(Customer)
        self.order = baker.make(Order, customer=self.customer)

    # CREATE (order_id + menu_id + qty)
    def test_orderitem_create(self):
        r = self.client.post(
            "/api/order-items/",
            {"order_id": self.order.id, "menu_id": self.menu.id, "qty": 2},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        iid = r.json()["id"]
        oi = OrderItem.objects.get(id=iid)
        self.assertEqual(oi.order, self.order)
        self.assertEqual(oi.menu, self.menu)
        self.assertEqual(oi.qty, 2)

    # READ
    def test_orderitem_list_and_retrieve(self):
        items = baker.make(OrderItem, order=self.order, menu=self.menu, _quantity=3)
        r = self.client.get("/api/order-items/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 3)

        r = self.client.get(f"/api/order-items/{items[1].id}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], items[1].id)

    # UPDATE (меняем qty)
    def test_orderitem_update(self):
        oi = baker.make(OrderItem, order=self.order, menu=self.menu, qty=1)
        r = self.client.put(
            f"/api/order-items/{oi.id}/",
            {"order_id": self.order.id, "menu_id": self.menu.id, "qty": 5},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        oi.refresh_from_db()
        self.assertEqual(oi.qty, 5)

    # DELETE
    def test_orderitem_delete(self):
        oi = baker.make(OrderItem, order=self.order, menu=self.menu)
        r = self.client.delete(f"/api/order-items/{oi.id}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(OrderItem.objects.count(), 0)
