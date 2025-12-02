import { createRouter, createWebHistory } from "vue-router"

const LoginPage = () => import("@/components/auth/LoginPage.vue")
const MenuPage = () => import("@/components/menu/MenuPage.vue")
const CategoriesPage = () => import("@/components/categories/CategoriesPage.vue")
const CustomersPage = () => import("@/components/customers/CustomersPage.vue")
const OrdersPage = () => import("@/components/orders/OrdersPage.vue")
const OrderItemsPage = () => import("@/components/order-items/OrderItemsPage.vue")
const MyOrdersPage = () => import("@/components/orders/MyOrdersPage.vue")

const routes = [
  { path: "/login", name: "login", component: LoginPage },
  { path: "/", redirect: "/menu" },
  { path: "/menu", name: "menu", component: MenuPage },
  { path: "/categories", name: "categories", component: CategoriesPage },
  { path: "/customers", name: "customers", component: CustomersPage },
  { path: "/orders", name: "orders", component: OrdersPage },
  { path: "/order-items", name: "order-items", component: OrderItemsPage },
  { path: "/my-orders", name: "my-orders", component: MyOrdersPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
