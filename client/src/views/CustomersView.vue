<script setup>
import { onBeforeMount, ref } from "vue";
import axios from "axios";

const items = ref([]);
const stats = ref(null);

const filters = ref({
  name: "",
  phone: "",
});

const createForm = ref({
  name: "",
  phone: "",
});

const editForm = ref({
  id: null,
  name: "",
  phone: "",
});

async function fetchItems() {
  const r = await axios.get("/api/customers/", { params: filters.value });
  items.value = r.data || [];
}

async function fetchStats() {
  const r = await axios.get("/api/customers/stats/", { params: filters.value });
  stats.value = r.data;
}

async function applyFilters() {
  await fetchItems();
  await fetchStats();
}

async function createItem() {
  if (!createForm.value.name) return;

  await axios.post("/api/customers/", {
    name: createForm.value.name,
    phone: createForm.value.phone || "",
  });

  createForm.value = { name: "", phone: "" };
  await applyFilters();
}

function openEdit(c) {
  editForm.value = {
    id: c.id,
    name: c.name,
    phone: c.phone || "",
  };
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/customers/${id}/`, {
    name: editForm.value.name,
    phone: editForm.value.phone || "",
  });

  await applyFilters();
}

async function deleteItem(id) {
  await axios.delete(`/api/customers/${id}/`);
  await applyFilters();
}

onBeforeMount(applyFilters);
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Клиенты</h2>

    <div class="d-flex justify-content-between align-items-center mb-2">
      <div class="text-muted" v-if="stats">
        Всего клиентов: <b>{{ stats.total }}</b>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Добавить клиента</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="createItem">
          <div class="col-md-6">
            <label class="form-label">ФИО</label>
            <input class="form-control" v-model="createForm.name" />
          </div>

          <div class="col-md-4">
            <label class="form-label">Телефон</label>
            <input class="form-control" v-model="createForm.phone" />
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
          <div class="col-md-5">
            <label class="form-label">ФИО</label>
            <input class="form-control" v-model="filters.name" />
          </div>
          <div class="col-md-5">
            <label class="form-label">Телефон</label>
            <input class="form-control" v-model="filters.phone" />
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
              <th>ФИО</th>
              <th style="width: 240px;">Телефон</th>
              <th style="width: 220px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="c in items" :key="c.id">
              <td>#{{ c.id }}</td>
              <td>{{ c.name }}</td>
              <td>{{ c.phone }}</td>
              <td class="d-flex gap-2">
                <button
                  class="btn btn-sm btn-outline-secondary"
                  data-bs-toggle="modal"
                  data-bs-target="#editCustomerModal"
                  @click="openEdit(c)"
                >
                  Редактировать
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteItem(c.id)">
                  Удалить
                </button>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td colspan="4" class="text-muted text-center">Нет данных</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- modal -->
    <div class="modal fade" id="editCustomerModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">Редактировать клиента</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">
            <form class="d-flex flex-column" style="gap: 10px;" @submit.prevent.stop="saveEdit">
              <div>
                <label class="form-label">ФИО</label>
                <input class="form-control" v-model="editForm.name" />
              </div>

              <div>
                <label class="form-label">Телефон</label>
                <input class="form-control" v-model="editForm.phone" />
              </div>

              <div class="text-end">
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
