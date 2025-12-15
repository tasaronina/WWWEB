import { createRouter, createWebHistory } from "vue-router";

import MenuView from "@/views/MenuView.vue";
import LoginView from "@/views/LoginView.vue";

import CategoriesView from "@/views/CategoriesView.vue";
import CustomersView from "@/views/CustomersView.vue";
import OrdersView from "@/views/OrdersView.vue";
import OrderItemsView from "@/views/OrderItemsView.vue";

import { useUserStore } from "@/stores/user_store";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "Login",
      component: LoginView,
    },

    // главную страницу убрали — стартуем с меню
    {
      path: "/",
      redirect: "/menu",
    },

    {
      path: "/menu",
      name: "Menu",
      component: MenuView,
    },
    {
      path: "/categories",
      name: "Categories",
      component: CategoriesView,
    },
    {
      path: "/customers",
      name: "Customers",
      component: CustomersView,
    },
    {
      path: "/orders",
      name: "Orders",
      component: OrdersView,
    },
    {
      path: "/order-items",
      name: "OrderItems",
      component: OrderItemsView,
    },
  ],
});

router.beforeEach((to, from) => {
  const userStore = useUserStore();
  if (userStore.is_authenticated == false && to.name != "Login") {
    return { name: "Login" };
  }
});

export default router;
