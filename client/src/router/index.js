import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/components/auth/LoginPage.vue"),
    meta: { public: true },
  },

  // пользовательские страницы
  {
    path: "/menu",
    name: "menu",
    component: () => import("@/components/menu/MenuPage.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/my-orders",
    name: "my-orders",
    component: () => import("@/components/orders/MyOrdersPage.vue"),
    meta: { requiresAuth: true },
  },

  // админские страницы
  {
    path: "/orders",
    name: "orders",
    component: () => import("@/components/orders/OrdersPage.vue"),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: "/categories",
    name: "categories",
    component: () => import("@/components/categories/CategoriesPage.vue"),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: "/customers",
    name: "customers",
    component: () => import("@/components/customers/CustomersPage.vue"),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: "/order-items",
    name: "order-items",
    component: () => import("@/components/order-items/OrderItemsPage.vue"),
    meta: { requiresAuth: true, adminOnly: true },
  },

  { path: "/", redirect: { name: "menu" } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const store = useUserStore();

  if (!store.ready) {
    try { await store.restore(); } catch {}
  }

  if (to.meta?.public) {
    if (store.isAuthed) {
      const next = (to.query?.next && String(to.query.next)) || "/menu";
      return next;
    }
    return true;
  }

  if (to.meta?.requiresAuth && !store.isAuthed) {
    return { name: "login", query: { next: to.fullPath || "/menu" } };
  }

  if (to.meta?.adminOnly && !store.isAdmin) {
    return { name: "menu" };
  }

  return true;
});

export default router;
