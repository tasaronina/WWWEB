<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { orderItems, orders, menu } = storeToRefs(dataStore);

const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const createForm = ref({
  order: null,
  menu: null,
  qty: 1,
});

const editForm = ref({
  id: null,
  order: null,
  menu: null,
  qty: 1,
});

onBeforeMount(async () => {
  await userStore.checkLogin();
  if (isAdmin.value) {
    await dataStore.fetchOrders();
    await dataStore.fetchMenu();
    await dataStore.fetchOrderItems();
  }
});

function openEdit(it) {
  editForm.value = {
    id: it.id,
    order: it.order,
    menu: it.menu,
    qty: it.qty,
  };
}

function orderLabel(id) {
  return id ? `#${id}` : "—";
}

function menuLabel(id) {
  return (menu.value || []).find((m) => m.id === id)?.title || `menu #${id}`;
}

async function createItem() {
  createForm.value.qty = Math.max(1, Number(createForm.value.qty || 1));
  await axios.post("/api/order-items/", createForm.value);
  createForm.value = { order: null, menu: null, qty: 1 };
  await dataStore.fetchOrderItems();
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  const payload = {
    order: editForm.value.order,
    menu: editForm.value.menu,
    qty: Math.max(1, Number(editForm.value.qty || 1)),
  };

  await axios.put(`/api/order-items/${id}/`, payload);
  await dataStore.fetchOrderItems();
}

async function deleteItem(id) {
  await axios.delete(`/api/order-items/${id}/`);
  await dataStore.fetchOrderItems();
}
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Позиции заказов (админ)</h2>

    <div v-if="!isAdmin" class="alert alert-danger">
      Доступно только администратору.
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">Добавить позицию в заказ</div>
        <div class="card-body">
          <form class="row g-2" @submit.prevent="createItem">
            <div class="col-md-4">
              <label class="form-label">Заказ</label>
              <select v-model="createForm.order" class="form-select" required>
                <option :value="null">—</option>
                <option v-for="o in orders" :key="o.id" :value="o.id">#{{ o.id }}</option>
              </select>
            </div>

            <div class="col-md-5">
              <label class="form-label">Позиция меню</label>
              <select v-model="createForm.menu" class="form-select" required>
                <option :value="null">—</option>
                <option v-for="m in menu" :key="m.id" :value="m.id">{{ m.title }}</option>
              </select>
            </div>

            <div class="col-md-3">
              <label class="form-label">Количество</label>
              <input v-model.number="createForm.qty" type="number" min="1" class="form-control" />
            </div>

            <div class="col-12 text-end">
              <button class="btn btn-primary" type="submit">Добавить</button>
            </div>
          </form>
        </div>
      </div>

      <div class="card">
        <div class="card-header bg-body-tertiary d-flex justify-content-between">
          <span>Список позиций</span>
          <span class="text-muted">Всего: {{ orderItems.length }}</span>
        </div>

        <div class="card-body table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th style="width: 90px;">ID</th>
                <th style="width: 160px;">Заказ</th>
                <th>Позиция меню</th>
                <th style="width: 120px;">Кол-во</th>
                <th style="width: 140px;">Сумма</th>
                <th style="width: 220px;">Действия</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="it in orderItems" :key="it.id">
                <td>{{ it.id }}</td>
                <td>{{ orderLabel(it.order) }}</td>
                <td class="fw-semibold">{{ menuLabel(it.menu) }}</td>
                <td>{{ it.qty }}</td>
                <td>{{ it.line_price }}</td>
                <td class="d-flex gap-2">
                  <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editOrderItemModal" @click="openEdit(it)">
                    Редактировать
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteItem(it.id)">
                    Удалить
                  </button>
                </td>
              </tr>

              <tr v-if="orderItems.length === 0">
                <td colspan="6" class="text-center text-muted">Пока позиций нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- modal -->
      <div class="modal fade" id="editOrderItemModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">

            <div class="modal-header">
              <h5 class="modal-title">Редактировать позицию заказа</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>

            <div class="modal-body">
              <form class="row g-2" @submit.prevent.stop="saveEdit">
                <div class="col-12">
                  <label class="form-label">Заказ</label>
                  <select v-model="editForm.order" class="form-select" required>
                    <option v-for="o in orders" :key="o.id" :value="o.id">#{{ o.id }}</option>
                  </select>
                </div>

                <div class="col-12">
                  <label class="form-label">Позиция меню</label>
                  <select v-model="editForm.menu" class="form-select" required>
                    <option v-for="m in menu" :key="m.id" :value="m.id">{{ m.title }}</option>
                  </select>
                </div>

                <div class="col-12">
                  <label class="form-label">Количество</label>
                  <input v-model.number="editForm.qty" type="number" min="1" class="form-control" />
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
