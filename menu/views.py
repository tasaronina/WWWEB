from django.views.generic import TemplateView
from .models import Category, Menu, Customer, Order, OrderItem


class ShowCafeView(TemplateView):
    template_name = "menu/show_cafe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["menu_items"] = Menu.objects.all().select_related("group")
        context["customers"] = Customer.objects.all()
        context["orders"] = Order.objects.all().select_related("user", "customer")
        context["orderitems"] = OrderItem.objects.all().select_related("order", "menu")
        return context
