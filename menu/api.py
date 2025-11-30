from rest_framework.viewsets import ModelViewSet
from menu.models import Category, Menu, Customer, Order, OrderItem
from menu.serializers import (
    CategorySerializer, MenuSerializer, CustomerSerializer, OrderSerializer, OrderItemSerializer
)

class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        qs = Customer.objects.all()
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(user=user)
        else:
           
            user_id = self.request.query_params.get("user_id")
            if user_id:
                qs = qs.filter(user__id=user_id)
        return qs

class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = Order.objects.all().select_related("customer")
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(user=user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                qs = qs.filter(user__id=user_id)
        return qs

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
class MenuViewSet(ModelViewSet):
    queryset = Menu.objects.all().select_related("group")
    serializer_class = MenuSerializer

class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer



class OrderItemViewSet(ModelViewSet):
    queryset = OrderItem.objects.all().select_related("order", "menu", "menu__group")
    serializer_class = OrderItemSerializer
