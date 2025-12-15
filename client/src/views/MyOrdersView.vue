<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { myOrders, menu } = storeToRefs(dataStore);

const selectedOrder = ref(null);
const selectedItems = ref([]);
const loadingItems = ref(false);

const isLoggedIn = computed(() => !!userInfo.value?.is_authenticated);

onBeforeMount(async () => {
  await userStore.checkLogin();


  await dataStore.fetchMenu();

  if (isLoggedIn.value) {
    await dataStore.fetchMyOrders();
  }
});

function menuTitle(menuId) {
  return (menu.value || []).find((m) => m.id === menuId)?.title || `#${menuId}`;
}

async function openOrder(order) {
  selectedOrder.value = order;
  selectedItems.value = [];
  loadingItems.value = true;

  try {
    const r = await axios.get("/api/order-items/");
    selectedItems.value = (r.data || []).filter((it) => it.order === order.id);
  } finally {
    loadingItems.value = false;
  }
}

async function cancelOrder(order) {

  await axios.patch(`/api/orders/${order.id}/`, { status: "CANCELLED" });
  await dataStore.fetchMyOrders();
}
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Мои заказы</h2>

    <div v-if="!isLoggedIn" class="alert alert-warning">
      Нужно войти, чтобы видеть свои заказы.
    </div>

    <div v-else class="card">
      <div class="card-header bg-success text-white d-flex justify-content-between">
        <span>Список заказов</span>
        <span>Всего: {{ myOrders.length }}</span>
      </div>

      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th style="width: 80px;">ID</th>
                <th style="width: 180px;">Статус</th>
                <th style="width: 200px;">Дата</th>
                <th style="width: 160px;">Сумма</th>
                <th style="width: 220px;">Действия</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="o in myOrders" :key="o.id">
                <td>#{{ o.id }}</td>
                <td>{{ o.status }}</td>
                <td class="text-muted small">{{ o.created_at }}</td>
                <td>{{ o.total_price }}</td>
                <td class="d-flex gap-2">
                  <button
                    class="btn btn-sm btn-outline-success"
                    data-bs-toggle="modal"
                    data-bs-target="#orderItemsModal"
                    @click="openOrder(o)"
                  >
                    Состав
                  </button>

                  <button
                    class="btn btn-sm btn-outline-secondary"
                    @click="cancelOrder(o)"
                    :disabled="o.status === 'CANCELLED' || o.status === 'DONE'"
                    title="Отменить можно только пока не готов"
                  >
                    Отменить
                  </button>
                </td>
              </tr>

              <tr v-if="myOrders.length === 0">
                <td colspan="5" class="text-center text-muted">Пока заказов нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

 
    <div class="modal fade" id="orderItemsModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">
              Состав заказа {{ selectedOrder ? "#" + selectedOrder.id : "" }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"></button>
          </div>

          <div class="modal-body">
            <div v-if="loadingItems" class="text-muted">Загрузка...</div>

            <div v-else>
              <ul class="list-group" v-if="selectedItems.length > 0">
                <li
                  class="list-group-item d-flex justify-content-between align-items-center"
                  v-for="it in selectedItems"
                  :key="it.id"
                >
                  <span>
                    <span class="fw-semibold">{{ menuTitle(it.menu) }}</span>
                    <span class="text-muted small ms-2">× {{ it.qty }}</span>
                  </span>
                  <span class="fw-semibold">{{ it.line_price }}</span>
                </li>
              </ul>

              <div v-else class="text-muted">Позиции не найдены.</div>
            </div>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>
