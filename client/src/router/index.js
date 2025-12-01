import { createRouter, createWebHistory } from "vue-router";

const CategoriesPage = () => import("@/components/categories/CategoriesPage.vue");
const MenuPage       = () => import("@/components/menu/MenuPage.vue");
const CustomersPage  = () => import("@/components/customers/CustomersPage.vue");
const OrdersPage     = () => import("@/components/orders/OrdersPage.vue");
const OrderItemsPage = () => import("@/components/order-items/OrderItemsPage.vue");
const LoginPage      = () => import("@/components/auth/LoginPage.vue");

export default createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", redirect: "/categories" },
    { path: "/categories",  name: "categories",  component: CategoriesPage },
    { path: "/menu",        name: "menu",        component: MenuPage },
    { path: "/customers",   name: "customers",   component: CustomersPage },
    { path: "/orders",      name: "orders",      component: OrdersPage },
    { path: "/order-items", name: "order-items", component: OrderItemsPage },
    { path: "/login",       name: "login",       component: LoginPage },
  ],
});
