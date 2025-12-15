<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { orders, customers } = storeToRefs(dataStore);

const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const createForm = ref({
  customer: null,
  status: "NEW",
});

const editForm = ref({
  id: null,
  customer: null,
  status: "NEW",
});

onBeforeMount(async () => {
  await userStore.checkLogin();
  if (isAdmin.value) {
    await dataStore.fetchCustomers();
    await dataStore.fetchOrders();
  }
});

function openEdit(o) {
  editForm.value = {
    id: o.id,
    customer: o.customer ?? null,
    status: o.status || "NEW",
  };
}

async function createOrder() {
  await axios.post("/api/orders/", createForm.value);
  createForm.value = { customer: null, status: "NEW" };
  await dataStore.fetchOrders();
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;
  await axios.patch(`/api/orders/${id}/`, {
    customer: editForm.value.customer,
    status: editForm.value.status,
  });
  await dataStore.fetchOrders();
}

async function deleteOrder(id) {
  await axios.delete(`/api/orders/${id}/`);
  await dataStore.fetchOrders();
}

function customerName(id) {
  return (customers.value || []).find((c) => c.id === id)?.name || "—";
}
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Заказы (админ)</h2>

    <div v-if="!isAdmin" class="alert alert-danger">
      Доступно только администратору.
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">Создать заказ</div>
        <div class="card-body">
          <form class="row g-2" @submit.prevent="createOrder">
            <div class="col-md-6">
              <label class="form-label">Клиент</label>
              <select v-model="createForm.customer" class="form-select">
                <option :value="null">—</option>
                <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>

            <div class="col-md-6">
              <label class="form-label">Статус</label>
              <select v-model="createForm.status" class="form-select">
                <option value="NEW">NEW</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="DONE">DONE</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
            </div>

            <div class="col-12 text-end">
              <button class="btn btn-primary" type="submit">Создать</button>
            </div>
          </form>
        </div>
      </div>

      <div class="card">
        <div class="card-header bg-body-tertiary d-flex justify-content-between">
          <span>Список заказов</span>
          <span class="text-muted">Всего: {{ orders.length }}</span>
        </div>

        <div class="card-body table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th style="width: 90px;">ID</th>
                <th style="width: 220px;">Клиент</th>
                <th style="width: 160px;">Статус</th>
                <th style="width: 220px;">Дата</th>
                <th style="width: 140px;">Сумма</th>
                <th style="width: 240px;">Действия</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="o in orders" :key="o.id">
                <td>#{{ o.id }}</td>
                <td>{{ customerName(o.customer) }}</td>
                <td>{{ o.status }}</td>
                <td class="text-muted small">{{ o.created_at }}</td>
                <td>{{ o.total_price }}</td>
                <td class="d-flex gap-2">
                  <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editOrderModal" @click="openEdit(o)">
                    Редактировать
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteOrder(o.id)">
                    Удалить
                  </button>
                </td>
              </tr>

              <tr v-if="orders.length === 0">
                <td colspan="6" class="text-center text-muted">Пока заказов нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- modal -->
      <div class="modal fade" id="editOrderModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">

            <div class="modal-header">
              <h5 class="modal-title">Редактировать заказ</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>

            <div class="modal-body">
              <form class="row g-2" @submit.prevent.stop="saveEdit">
                <div class="col-12">
                  <label class="form-label">Клиент</label>
                  <select v-model="editForm.customer" class="form-select">
                    <option :value="null">—</option>
                    <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>

                <div class="col-12">
                  <label class="form-label">Статус</label>
                  <select v-model="editForm.status" class="form-select">
                    <option value="NEW">NEW</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="DONE">DONE</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </select>
                </div>

                <div class="col-12 text-end">
                  <button class="btn btn-primary" type="submit" data-bs-dismiss="modal">
                    Сохранить
                  </button>
                </div>
              </form>
            </div>

          </div>
        </div>
      </div>

    </div>
  </div>
</template>
