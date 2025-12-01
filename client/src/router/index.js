import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

const LoginPage      = () => import("@/components/auth/LoginPage.vue");
const MenuPage       = () => import("@/components/menu/MenuPage.vue");
const MyOrdersPage   = () => import("@/components/orders/MyOrdersPage.vue");
const CategoriesPage = () => import("@/components/categories/CategoriesPage.vue");
const CustomersPage  = () => import("@/components/customers/CustomersPage.vue");
const OrdersPage     = () => import("@/components/orders/OrdersPage.vue");
const OrderItemsPage = () => import("@/components/order-items/OrderItemsPage.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/menu" },
    { path: "/login", name: "login", component: LoginPage, meta: { guestOnly: true } },
    { path: "/menu", name: "menu", component: MenuPage, meta: { requiresAuth: true } },
    { path: "/my-orders", name: "my-orders", component: MyOrdersPage, meta: { requiresAuth: true } },

    { path: "/categories", name: "categories", component: CategoriesPage, meta: { requiresAuth: true, adminOnly: true } },
    { path: "/customers",  name: "customers",  component: CustomersPage,  meta: { requiresAuth: true, adminOnly: true } },
    { path: "/orders",     name: "orders",     component: OrdersPage,     meta: { requiresAuth: true, adminOnly: true } },
    { path: "/order-items",name: "order-items",component: OrderItemsPage, meta: { requiresAuth: true, adminOnly: true } },
  ],
});

router.beforeEach(async (to, from, next) => {
  const store = useUserStore();
  if (!store.initialized) {
    try { await store.restore(); } catch {}
  }
  if (to.meta.requiresAuth && !store.isAuth) return next({ name: "login", query: { redirect: to.fullPath } });
  if (to.meta.guestOnly && store.isAuth)     return next({ name: "menu" });
  if (to.meta.adminOnly && !store.isAdmin)   return next({ name: "menu" });
  next();
});

export default router;
