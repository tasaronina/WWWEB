import { defineStore } from "pinia";
import { ref } from "vue";
import axios from "axios";

export const useDataStore = defineStore("dataStore", () => {
  const categories = ref([]);
  const menu = ref([]);
  const customers = ref([]);
  const orders = ref([]);
  const orderItems = ref([]);

  async function fetchCategories() {
    const r = await axios.get("/api/categories");
    categories.value = r.data;
    return r.data;
  }

  async function fetchMenu() {
    const r = await axios.get("/api/menu");
    menu.value = r.data;
    return r.data;
  }

  async function fetchCustomers() {
    const r = await axios.get("/api/customers");
    customers.value = r.data;
    return r.data;
  }

  async function fetchOrders() {
    const r = await axios.get("/api/orders");
    orders.value = r.data;
    return r.data;
  }

  async function fetchOrderItems() {
    const r = await axios.get("/api/order-items");
    orderItems.value = r.data;
    return r.data;
  }

  return {
    categories,
    menu,
    customers,
    orders,
    orderItems,

    fetchCategories,
    fetchMenu,
    fetchCustomers,
    fetchOrders,
    fetchOrderItems,
  };
});
