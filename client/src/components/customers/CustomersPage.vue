<script setup>
import axios from "axios";
import { ref, computed, onBeforeMount } from "vue";
import "@/styles/admin.css";

const items = ref([]);
const stats = ref(null);
const newItem = ref({ name: "", pictureFile: null, picturePreview: null });
const itemToEdit = ref({ id: null, name: "", pictureUrl: null });
const editPictureFile = ref(null);
const error = ref("");
const loading = ref(false);

const filters = ref({ id: "", name: "" });

function formatNumber(value) {
  if (value === null || value === undefined) return "-";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toFixed(2);
}

const filteredItems = computed(() =>
  items.value.filter((it) => {
    const f = filters.value;
    if (f.id && String(it.id) !== f.id.trim()) return false;
    if (f.name && !it.name.toLowerCase().includes(f.name.toLowerCase().trim())) return false;
    return true;
  })
);

async function fetchItems() {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await axios.get("/api/customers/");
    items.value = data.map((it) => ({
      ...it,
      pictureUrl:
        it.picture && !String(it.picture).startsWith("http")
          ? `${window.location.origin}${it.picture}`
          : it.picture,
    }));
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
}

async function fetchStats() {
  const { data } = await axios.get("/api/customers/stats/");
  stats.value = data;
}

function customerAddPictureChange(e) {
  if (!e.target.files.length) return;
  if (newItem.value.picturePreview) {
    URL.revokeObjectURL(newItem.value.picturePreview);
  }
  newItem.value.pictureFile = e.target.files[0];
  newItem.value.picturePreview = URL.createObjectURL(newItem.value.pictureFile);
}

function onEditPictureChange(e) {
  if (!e.target.files.length) return;
  editPictureFile.value = e.target.files[0];
  itemToEdit.value.pictureUrl = URL.createObjectURL(editPictureFile.value);
}

async function onItemAdd() {
  if (!newItem.value.name.trim()) return;
  const fd = new FormData();
  fd.append("name", newItem.value.name.trim());
  if (newItem.value.pictureFile) {
    fd.append("picture", newItem.value.pictureFile);
  }
  await axios.post("/api/customers/", fd, { headers: { "Content-Type": "multipart/form-data" } });
  if (newItem.value.picturePreview) {
    URL.revokeObjectURL(newItem.value.picturePreview);
  }
  newItem.value = { name: "", pictureFile: null, picturePreview: null };
  await Promise.all([fetchItems(), fetchStats()]);
}

function onItemEditClick(it) {
  itemToEdit.value = { id: it.id, name: it.name, pictureUrl: it.pictureUrl || null };
  editPictureFile.value = null;
  new bootstrap.Modal(document.getElementById("editCustomerModal")).show();
}

async function onItemUpdate() {
  if (!itemToEdit.value.name.trim()) return;
  const fd = new FormData();
  fd.append("name", itemToEdit.value.name.trim());
  if (editPictureFile.value) {
    fd.append("picture", editPictureFile.value);
  }
  await axios.put(`/api/customers/${itemToEdit.value.id}/`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  editPictureFile.value = null;
  await Promise.all([fetchItems(), fetchStats()]);
}

async function onItemDelete(it) {
  if (!confirm(`Удалить клиента "${it.name}"?`)) return;
  await axios.delete(`/api/customers/${it.id}/`);
  await Promise.all([fetchItems(), fetchStats()]);
}

function resetFilters() {
  filters.value = { id: "", name: "" };
}

onBeforeMount(async () => {
  await Promise.all([fetchItems(), fetchStats()]);
});
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Клиенты</h1>

    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить клиента</h5>
        <form class="row g-3 align-items-end" @submit.prevent="onItemAdd">
          <div class="col-md-4">
            <label class="form-label">Имя клиента</label>
            <input v-model="newItem.name" type="text" class="form-control" placeholder="Имя" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Фото</label>
            <input type="file" class="form-control" accept="image/*" @change="customerAddPictureChange" />
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" type="submit">Добавить</button>
          </div>
        </form>

        <div v-if="newItem.picturePreview" class="mt-3">
          <img :src="newItem.picturePreview" class="img-thumbnail round" style="width: 72px; height: 72px; object-fit: cover" />
        </div>
      </div>
    </div>

    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего клиентов: <strong>{{ stats.count }}</strong></span>
        <span>Средний ID: <strong>{{ formatNumber(stats.avg) }}</strong></span>
        <span>Максимальный ID: <strong>{{ stats.max }}</strong></span>
        <span>Минимальный ID: <strong>{{ stats.min }}</strong></span>
      </div>
    </div>

    <!-- Фильтры как на “Добавить заказ” -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-2">
            <input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" />
          </div>
          <div class="col-md-4">
            <input v-model="filters.name" type="text" class="form-control" placeholder="Фильтр по имени" />
          </div>
          <div class="col-md-2">
            <button class="btn btn-outline-secondary w-100" type="button" @click="resetFilters">Сброс</button>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="list-group">
        <div v-for="it in filteredItems" :key="it.id" class="list-group-item">
          <div class="d-flex justify-content-between align-items-center gap-3">
            <div class="d-flex align-items-center gap-3">
              <img v-if="it.pictureUrl" :src="it.pictureUrl" class="rounded-circle" style="width: 60px; height: 60px; object-fit: cover" />
              <div v-else class="rounded-circle bg-secondary" style="width: 60px; height: 60px"></div>
              <div>
                <div class="fw-semibold">{{ it.name }}</div>
                <div class="text-muted small">ID: {{ it.id }}</div>
              </div>
            </div>
            <div class="btn-group">
              <button class="btn btn-sm btn-outline-primary" type="button" @click="onItemEditClick(it)">Редактировать</button>
              <button class="btn btn-sm btn-outline-danger" type="button" @click="onItemDelete(it)">Удалить</button>
            </div>
          </div>
        </div>
        <div v-if="!filteredItems.length && !loading" class="list-group-item text-center text-muted">Ничего не найдено</div>
      </div>
    </div>

    <div id="editCustomerModal" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Редактировать клиента</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <label class="form-label">Имя клиента</label>
            <input v-model="itemToEdit.name" type="text" class="form-control mb-3" />
            <label class="form-label">Фото</label>
            <input type="file" class="form-control" accept="image/*" @change="onEditPictureChange" />
            <div v-if="itemToEdit.pictureUrl" class="mt-3">
              <img :src="itemToEdit.pictureUrl" class="img-thumbnail round" style="width: 72px; height: 72px; object-fit: cover" />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onItemUpdate">Сохранить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
