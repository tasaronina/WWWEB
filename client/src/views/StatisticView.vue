<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { menuStats } = storeToRefs(dataStore);

const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const ordersStats = ref(null);

onBeforeMount(async () => {
  await userStore.checkLogin();
  if (isAdmin.value) {
    await dataStore.fetchMenuStats();
    const r = await axios.get("/api/orders/stats/");
    ordersStats.value = r.data;
  }
});
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Статистика (админ)</h2>

    <div v-if="!isAdmin" class="alert alert-danger">
      Доступно только администратору.
    </div>

    <div v-else class="row g-3">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-primary text-white">Меню</div>
          <div class="card-body" v-if="menuStats">
            <div>Кол-во позиций: <strong>{{ menuStats.count }}</strong></div>
            <div>Средняя цена: <strong>{{ menuStats.avg }}</strong></div>
            <div>Максимальная цена: <strong>{{ menuStats.max }}</strong></div>
            <div>Минимальная цена: <strong>{{ menuStats.min }}</strong></div>
          </div>
          <div class="card-body text-muted" v-else>Нет данных</div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card">
          <div class="card-header bg-success text-white">Заказы</div>
          <div class="card-body" v-if="ordersStats">
            <div>Всего заказов: <strong>{{ ordersStats.total_orders }}</strong></div>
            <div>Выручка: <strong>{{ ordersStats.revenue }}</strong></div>
          </div>
          <div class="card-body text-muted" v-else>Нет данных</div>
        </div>
      </div>
    </div>
  </div>
</template>
