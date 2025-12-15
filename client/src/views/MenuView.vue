<script setup>
import { onBeforeMount, ref } from "vue";
import axios from "axios";

const items = ref([]);
const stats = ref(null);
const categories = ref([]);

const filters = ref({
  title: "",
  group: "",
  price_min: "",
  price_max: "",
});

const createForm = ref({
  title: "",
  group: null,
  price: "",
  description: "",
});

const editForm = ref({
  id: null,
  title: "",
  group: null,
  price: "",
  description: "",
});

function buildQuery() {
  const q = [];
  if (filters.value.title) q.push("title=" + encodeURIComponent(filters.value.title));
  if (filters.value.group) q.push("group=" + encodeURIComponent(filters.value.group));
  if (filters.value.price_min) q.push("price_min=" + encodeURIComponent(filters.value.price_min));
  if (filters.value.price_max) q.push("price_max=" + encodeURIComponent(filters.value.price_max));
  return q.join("&");
}

async function fetchCategories() {
  const r = await axios.get("/api/categories/");
  categories.value = r.data || [];
}

async function fetchItems() {
  const r = await axios.get("/api/menu/", { params: filters.value });
  items.value = r.data || [];
}

async function fetchStats() {
  const r = await axios.get("/api/menu/stats/", { params: filters.value });
  stats.value = r.data;
}

async function applyFilters() {
  await fetchItems();
  await fetchStats();
}

async function createItem() {
  if (!createForm.value.title) return;
  if (!createForm.value.group) return;

  await axios.post("/api/menu/", {
    title: createForm.value.title,
    group: createForm.value.group,
    price: createForm.value.price || "0",
    description: createForm.value.description || "",
  });

  createForm.value = { title: "", group: null, price: "", description: "" };
  await applyFilters();
}

function openEdit(m) {
  editForm.value = {
    id: m.id,
    title: m.title,
    group: m.group,
    price: m.price,
    description: m.description || "",
  };
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/menu/${id}/`, {
    title: editForm.value.title,
    group: editForm.value.group,
    price: editForm.value.price || "0",
    description: editForm.value.description || "",
  });

  await applyFilters();
}

async function deleteItem(id) {
  await axios.delete(`/api/menu/${id}/`);
  await applyFilters();
}

function exportExcel() {
  const qs = buildQuery();
  window.location = "/api/menu/export-excel/" + (qs ? "?" + qs : "");
}

function exportWord() {
  const qs = buildQuery();
  window.location = "/api/menu/export-word/" + (qs ? "?" + qs : "");
}

function categoryTitle(id) {
  return categories.value.find((c) => c.id === id)?.name || `#${id}`;
}

onBeforeMount(async () => {
  await fetchCategories();
  await applyFilters();
});
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Меню</h2>

    <div class="d-flex justify-content-between align-items-center mb-2">
      <div class="text-muted" v-if="stats">
        Кол-во: <b>{{ stats.count }}</b>,
        Средняя цена: <b>{{ stats.avg }}</b>,
        Мин: <b>{{ stats.min }}</b>,
        Макс: <b>{{ stats.max }}</b>
      </div>

      <!-- ✅ экспорт только тут -->
      <div class="d-flex gap-2">
        <button class="btn btn-outline-success btn-sm" @click="exportExcel">Excel</button>
        <button class="btn btn-outline-primary btn-sm" @click="exportWord">Word</button>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Добавить позицию меню</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="createItem">
          <div class="col-md-4">
            <label class="form-label">Название</label>
            <input class="form-control" v-model="createForm.title" />
          </div>

          <div class="col-md-3">
            <label class="form-label">Категория</label>
            <select class="form-select" v-model="createForm.group">
              <option :value="null">—</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label">Цена</label>
            <input class="form-control" v-model="createForm.price" />
          </div>

          <div class="col-md-3">
            <label class="form-label">Описание</label>
            <input class="form-control" v-model="createForm.description" />
          </div>

          <div class="col-12 d-flex justify-content-end">
            <button class="btn btn-primary">Добавить</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Фильтры</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="applyFilters">
          <div class="col-md-4">
            <label class="form-label">Название</label>
            <input class="form-control" v-model="filters.title" />
          </div>

          <div class="col-md-2">
            <label class="form-label">Категория (id)</label>
            <input class="form-control" v-model="filters.group" />
          </div>

          <div class="col-md-2">
            <label class="form-label">Цена от</label>
            <input class="form-control" v-model="filters.price_min" />
          </div>

          <div class="col-md-2">
            <label class="form-label">Цена до</label>
            <input class="form-control" v-model="filters.price_max" />
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
              <th>Название</th>
              <th style="width: 220px;">Категория</th>
              <th style="width: 130px;">Цена</th>
              <th style="width: 220px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="m in items" :key="m.id">
              <td>#{{ m.id }}</td>
              <td>{{ m.title }}</td>
              <td>{{ categoryTitle(m.group) }}</td>
              <td>{{ m.price }}</td>
              <td class="d-flex gap-2">
                <button
                  class="btn btn-sm btn-outline-secondary"
                  data-bs-toggle="modal"
                  data-bs-target="#editMenuModal"
                  @click="openEdit(m)"
                >
                  Редактировать
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteItem(m.id)">
                  Удалить
                </button>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td colspan="6" class="text-muted text-center">Нет данных</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>


    <div class="modal fade" id="editMenuModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">Редактировать позицию меню</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">
            <form class="row g-2" @submit.prevent.stop="saveEdit">
              <div class="col-md-5">
                <label class="form-label">Название</label>
                <input class="form-control" v-model="editForm.title" />
              </div>

              <div class="col-md-3">
                <label class="form-label">Категория</label>
                <select class="form-select" v-model="editForm.group">
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>

              <div class="col-md-2">
                <label class="form-label">Цена</label>
                <input class="form-control" v-model="editForm.price" />
              </div>

              <div class="col-md-2">
                <label class="form-label">Описание</label>
                <input class="form-control" v-model="editForm.description" />
              </div>

              <div class="col-12 text-end">
                <button class="btn btn-primary" type="submit" data-bs-dismiss="modal">Сохранить</button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>
