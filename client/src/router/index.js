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
      meta: { requiresAdmin: true },
    },
    {
      path: "/customers",
      name: "Customers",
      component: CustomersView,
      meta: { requiresAdmin: true },
    },
    {
      path: "/orders",
      name: "Orders",
      component: OrdersView,
      meta: { requiresAdmin: true },
    },
    {
      path: "/order-items",
      name: "OrderItems",
      component: OrderItemsView,
      meta: { requiresAdmin: true },
    },
  ],
});

router.beforeEach(async (to, from) => {
  const userStore = useUserStore();

  if (userStore.is_authenticated === null) {
    await userStore.fetchUserInfo();
  }

  if (userStore.is_authenticated == false && to.name != "Login") {
    return { name: "Login" };
  }

  if (to.meta && to.meta.requiresAdmin) {
    if (userStore.is_staff == false) {
      return { name: "Menu" };
    }
  }
});

export default router;
