import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: { name: "menu" } },

   
    { path: "/login", name: "login", component: () => import("@/components/auth/LoginPage.vue") },

    
    { path: "/menu", name: "menu", component: () => import("@/components/menu/MenuPage.vue") },
    { path: "/my-orders", name: "my-orders", component: () => import("@/components/orders/MyOrdersPage.vue"), meta: { requiresAuth: true } },

    
    { path: "/orders", name: "orders", component: () => import("@/components/orders/OrdersPage.vue"), meta: { requiresAdmin: true } },
    { path: "/categories", name: "categories", component: () => import("@/components/categories/CategoriesPage.vue"), meta: { requiresAdmin: true } },
    { path: "/customers", name: "customers", component: () => import("@/components/customers/CustomersPage.vue"), meta: { requiresAdmin: true } },
    { path: "/order-items", name: "order-items", component: () => import("@/components/order-items/OrderItemsPage.vue"), meta: { requiresAdmin: true } },

   
    { path: "/:pathMatch(.*)*", redirect: { name: "menu" } },
  ],
});


router.beforeEach(async (to, from, next) => {
  const store = useUserStore();
  if (!store.ready) { await store.restore(); }

  if (to.meta?.requiresAuth && !store.isAuthed) {
    return next({ name: "login", query: { next: to.fullPath } });
  }
  if (to.meta?.requiresAdmin && !store.isAdmin) {
    return next({ name: "menu" });
  }
  return next();
});

export default router;
