import { createRouter, createWebHistory } from "vue-router";

import CafeHomeView from "@/views/CafeHomeView.vue";
import CategoriesView from "@/views/CategoriesView.vue";
import MenuView from "@/views/MenuView.vue";
import CustomersView from "@/views/CustomersView.vue";
import OrdersView from "@/views/OrdersView.vue";
import OrderItemsView from "@/views/OrderItemsView.vue";
import StatisticView from "@/views/StatisticView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", component: CafeHomeView },

    { path: "/categories", component: CategoriesView },
    { path: "/menu", component: MenuView },
    { path: "/customers", component: CustomersView },
    { path: "/orders", component: OrdersView },
    { path: "/order-items", component: OrderItemsView },
    { path: "/statistic", component: StatisticView },
  ],
});

export default router;
