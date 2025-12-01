// client/src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

import MenuPage from "@/components/menu/MenuPage.vue";
import CategoriesPage from "@/components/categories/CategoriesPage.vue";
import CustomersPage from "@/components/customers/CustomersPage.vue";
import OrdersPage from "@/components/orders/OrdersPage.vue";
import OrderItemsPage from "@/components/order-items/OrderItemsPage.vue";
import MyOrdersPage from "@/components/orders/MyOrdersPage.vue";
import LoginPage from "@/components/auth/LoginPage.vue";

const routes = [
  { path: "/", redirect: "/menu" },

  // публичный
  { path: "/login", component: LoginPage, meta: { public: true } },

  // защищённые
  { path: "/menu", component: MenuPage, meta: { requiresAuth: true } },
  { path: "/categories", component: CategoriesPage, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/customers", component: CustomersPage, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/orders", component: OrdersPage, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/order-items", component: OrderItemsPage, meta: { requiresAuth: true, adminOnly: true } },

  // только для обычных пользователей (у админа ссылки не будет, но доступ всё равно прикроем)
  { path: "/my-orders", component: MyOrdersPage, meta: { requiresAuth: true, userOnly: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() { return { top: 0 }; },
});

// Глобальный гард
router.beforeEach(async (to) => {
  const store = useUserStore();
  if (!store.ready) {
    await store.restore();
  }

  if (to.meta.public) {
    // Если уже залогинен — не даём на /login
    if (store.isAuth) return { path: "/menu" };
    return true;
  }

  if (to.meta.requiresAuth && !store.isAuth) {
    return { path: "/login" };
  }

  // Админ-ограничения
  if (to.meta.adminOnly && !store.isAdmin) return { path: "/menu" };
  if (to.meta.userOnly && store.isAdmin) return { path: "/menu" };

  return true;
});

export default router;
