<script setup>
import { onBeforeMount, ref } from "vue";
import axios from "axios";

const items = ref([]);
const stats = ref(null);

const orders = ref([]);
const menu = ref([]);

const filters = ref({
  order: "",
  menu: "",
  qty_min: "",
  qty_max: "",
});

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

async function fetchOrders() {
  const r = await axios.get("/api/orders/");
  orders.value = r.data || [];
}

async function fetchMenu() {
  const r = await axios.get("/api/menu/");
  menu.value = r.data || [];
}

async function fetchItems() {
  const r = await axios.get("/api/order-items/", { params: filters.value });
  items.value = r.data || [];
}

async function fetchStats() {
  const r = await axios.get("/api/order-items/stats/", { params: filters.value });
  stats.value = r.data;
}

async function applyFilters() {
  await fetchItems();
  await fetchStats();
}

async function createItem() {
  if (!createForm.value.order) return;
  if (!createForm.value.menu) return;

  await axios.post("/api/order-items/", {
    order: createForm.value.order,
    menu: createForm.value.menu,
    qty: Math.max(1, Number(createForm.value.qty || 1)),
  });

  createForm.value = { order: null, menu: null, qty: 1 };
  await applyFilters();
}

function openEdit(it) {
  editForm.value = {
    id: it.id,
    order: it.order,
    menu: it.menu,
    qty: it.qty,
  };
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/order-items/${id}/`, {
    order: editForm.value.order,
    menu: editForm.value.menu,
    qty: Math.max(1, Number(editForm.value.qty || 1)),
  });

  await applyFilters();
}

async function deleteItem(id) {
  await axios.delete(`/api/order-items/${id}/`);
  await applyFilters();
}

function menuTitle(id) {
  return menu.value.find((m) => m.id === id)?.title || `#${id}`;
}

onBeforeMount(async () => {
  await fetchOrders();
  await fetchMenu();
  await applyFilters();
});
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Позиции заказов</h2>

    <div class="d-flex justify-content-between align-items-center mb-2">
      <div class="text-muted" v-if="stats">
        Всего позиций: <b>{{ stats.total }}</b>,
        Мин: <b>{{ stats.min_qty }}</b>,
        Макс: <b>{{ stats.max_qty }}</b>,
        Среднее: <b>{{ stats.avg_qty }}</b>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Добавить позицию</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="createItem">
          <div class="col-md-4">
            <label class="form-label">Заказ</label>
            <select class="form-select" v-model="createForm.order">
              <option :value="null">—</option>
              <option v-for="o in orders" :key="o.id" :value="o.id">#{{ o.id }}</option>
            </select>
          </div>

          <div class="col-md-4">
            <label class="form-label">Меню</label>
            <select class="form-select" v-model="createForm.menu">
              <option :value="null">—</option>
              <option v-for="m in menu" :key="m.id" :value="m.id">
                {{ m.title }} (#{{ m.id }})
              </option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label">Кол-во</label>
            <input class="form-control" type="number" min="1" v-model.number="createForm.qty" />
          </div>

          <div class="col-md-2 d-flex align-items-end justify-content-end">
            <button class="btn btn-primary">Добавить</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Фильтры</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="applyFilters">
          <div class="col-md-3">
            <label class="form-label">Заказ (id)</label>
            <input class="form-control" v-model="filters.order" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Меню (id)</label>
            <input class="form-control" v-model="filters.menu" />
          </div>
          <div class="col-md-2">
            <label class="form-label">Кол-во от</label>
            <input class="form-control" v-model="filters.qty_min" />
          </div>
          <div class="col-md-2">
            <label class="form-label">Кол-во до</label>
            <input class="form-control" v-model="filters.qty_max" />
          </div>
          <div class="col-md-2 d-flex align-items-end justify-content-end">
            <button class="btn btn-primary">Применить</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card">
      <div class="card-header">Таблица</div>
      <div class="card-body table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th style="width: 90px;">ID</th>
              <th style="width: 140px;">Заказ</th>
              <th>Меню</th>
              <th style="width: 140px;">Кол-во</th>
              <th style="width: 220px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td>#{{ it.id }}</td>
              <td>#{{ it.order }}</td>
              <td>{{ menuTitle(it.menu) }}</td>
              <td>{{ it.qty }}</td>
              <td class="d-flex gap-2">
                <button
                  class="btn btn-sm btn-outline-secondary"
                  data-bs-toggle="modal"
                  data-bs-target="#editOrderItemModal"
                  @click="openEdit(it)"
                >
                  Редактировать
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteItem(it.id)">
                  Удалить
                </button>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td colspan="5" class="text-muted text-center">Нет данных</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>


    <div class="modal fade" id="editOrderItemModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">Редактировать позицию</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">
            <form class="row g-2" @submit.prevent.stop="saveEdit">
              <div class="col-12">
                <label class="form-label">Заказ</label>
                <select class="form-select" v-model="editForm.order">
                  <option v-for="o in orders" :key="o.id" :value="o.id">#{{ o.id }}</option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label">Меню</label>
                <select class="form-select" v-model="editForm.menu">
                  <option v-for="m in menu" :key="m.id" :value="m.id">
                    {{ m.title }} (#{{ m.id }})
                  </option>
                </select>
              </div>

              <div class="col-12">
                <label class="form-label">Кол-во</label>
                <input class="form-control" type="number" min="1" v-model.number="editForm.qty" />
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
</template>
