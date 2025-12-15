import { defineStore } from "pinia";
import { ref } from "vue";
import axios from "axios";

export const useDataStore = defineStore("dataStore", () => {
  const categories = ref([]);
  const menu = ref([]);
  const customers = ref([]);
  const orders = ref([]);
  const myOrders = ref([]);

  const menuStats = ref(null);

  async function fetchCategories(params = {}) {
    const r = await axios.get("/api/categories/", { params });
    categories.value = r.data || [];
  }

  async function fetchMenu(params = {}) {
    const r = await axios.get("/api/menu/", { params });
    menu.value = r.data || [];
  }

  async function fetchCustomers(params = {}) {
    const r = await axios.get("/api/customers/", { params });
    customers.value = r.data || [];
  }

  async function fetchOrders(params = {}) {
    const r = await axios.get("/api/orders/", { params });
    orders.value = r.data || [];
  }

  async function fetchMyOrders(params = {}) {
    const r = await axios.get("/api/orders/", { params });
    myOrders.value = r.data || [];
  }

  async function fetchMenuStats() {
    const r = await axios.get("/api/menu/stats/");
    menuStats.value = r.data;
  }

  return {
    categories,
    menu,
    customers,
    orders,
    myOrders,
    menuStats,

    fetchCategories,
    fetchMenu,
    fetchCustomers,
    fetchOrders,
    fetchMyOrders,
    fetchMenuStats,
  };
});
