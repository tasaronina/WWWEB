<!-- client/src/components/orders/MyOrdersPage.vue -->
<script setup>
import { ref, onBeforeMount } from "vue";
import axios from "axios";

axios.defaults.withCredentials = true;

const orders = ref([]);
const items  = ref({}); // {orderId: [...items]}
const loading = ref(false);

function price(v){ return Number(v||0).toFixed(2) }

async function fetchOrders(){
  loading.value = true;
  try{
    const { data } = await axios.get("/api/orders/");
    orders.value = data || [];
  }finally{ loading.value = false }
}

async function fetchItems(orderId){
  const { data } = await axios.get("/api/order-items/", { params: { order_id: orderId }});
  items.value = { ...items.value, [orderId]: data || [] };
}

function total(orderId){
  const arr = items.value[orderId] || [];
  return arr.reduce((s, it) => s + Number(it.menu?.price||0) * Number(it.qty||0), 0);
}

async function loadDetails(){
  await fetchOrders();
  for(const o of orders.value){
    await fetchItems(o.id);
  }
}

onBeforeMount(loadDetails);
</script>

<template>
  <div class="container">
    <h1 class="mb-3">Мои заказы</h1>

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle">
          <thead>
            <tr>
              <th style="width:100px">ID</th>
              <th>Клиент</th>
              <th>Состав</th>
              <th style="width:140px">Сумма</th>
              <th style="width:160px">Статус</th>
              <th style="width:190px">Создан</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="6">Загрузка...</td></tr>
            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ o.customer?.name || o.user || "я" }}</td>
              <td>
                <ul class="small mb-0">
                  <li v-for="it in items[o.id] || []" :key="it.id">
                    {{ it.menu?.name || it.menu?.title || ("Позиция #" + (it.menu_id || "")) }} × {{ it.qty }}
                  </li>
                </ul>
              </td>
              <td><strong>{{ price(total(o.id)) }}</strong></td>
              <td>{{ o.status }}</td>
              <td>{{ o.created_at ? new Date(o.created_at).toLocaleString() : "—" }}</td>
            </tr>
            <tr v-if="!loading && !orders.length">
              <td colspan="6" class="text-muted text-center">Заказов пока нет</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
