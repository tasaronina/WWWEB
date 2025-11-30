<template>
  <div class="container-fluid py-4">
    <h1 class="mb-4">Позиции меню</h1>

    <!-- Добавление позиции -->
    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить позицию</h5>

        <form @submit.prevent="onAddMenu">
          <div class="row g-3 align-items-end">
            <div class="col-md-3">
              <label class="form-label">Название</label>
              <input
                v-model="newMenu.name"
                type="text"
                class="form-control"
                required
              />
            </div>

            <div class="col-md-3">
              <label class="form-label">Категория</label>
              <select
                v-model="newMenu.group_id"
                class="form-select"
                required
              >
                <option :value="null">Выберите категорию...</option>
                <option
                  v-for="cat in categories"
                  :key="cat.id"
                  :value="cat.id"
                >
                  {{ cat.name }}
                </option>
              </select>
            </div>

            <div class="col-md-2">
              <label class="form-label">Цена</label>
              <input
                v-model.number="newMenu.price"
                type="number"
                step="0.01"
                min="0"
                class="form-control"
              />
            </div>

            <div class="col-md-3">
              <label class="form-label">Картинка</label>
              <input
                type="file"
                class="form-control"
                accept="image/*"
                @change="onNewPictureChange"
              />
            </div>

            <div class="col-md-1 d-grid">
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="loadingAdd"
              >
                Добавить
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- Статистика (по ценам) -->
    <div class="alert alert-light border d-flex flex-wrap gap-3 mb-4">
      <div>Всего позиций: <strong>{{ menuStats.total }}</strong></div>
      <div>Средняя цена: <strong>{{ formatPrice(menuStats.avg) }}</strong></div>
      <div>Макс. цена: <strong>{{ formatPrice(menuStats.max) }}</strong></div>
      <div>Мин. цена: <strong>{{ formatPrice(menuStats.min) }}</strong></div>
    </div>

    <!-- Фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <h5 class="card-title mb-3">Фильтры</h5>

        <div class="row g-2">
          <div class="col-md-2">
            <input
              v-model="filterId"
              type="text"
              class="form-control"
              placeholder="Фильтр по ID"
            />
          </div>
          <div class="col-md-3">
            <input
              v-model="filterName"
              type="text"
              class="form-control"
              placeholder="Фильтр по названию"
            />
          </div>
          <div class="col-md-3">
            <select
              v-model="filterCategoryId"
              class="form-select"
            >
              <option value="">Все категории</option>
              <option
                v-for="cat in categories"
                :key="cat.id"
                :value="String(cat.id)"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div class="col-md-2">
            <input
              v-model="filterPriceMin"
              type="number"
              step="0.01"
              class="form-control"
              placeholder="Мин. цена"
            />
          </div>
          <div class="col-md-2">
            <input
              v-model="filterPriceMax"
              type="number"
              step="0.01"
              class="form-control"
              placeholder="Макс. цена"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Список позиций -->
    <div class="card">
      <div class="card-body">
        <h5 class="card-title mb-3">Список позиций</h5>

        <div v-if="loadingList" class="text-muted">Загрузка...</div>
        <div v-else-if="error" class="text-danger">{{ error }}</div>
        <div v-else>
          <div v-if="filteredMenu.length === 0" class="text-muted">
            Позиции пока не добавлены
          </div>

          <div
            v-else
            class="list-group"
          >
            <div
              v-for="item in filteredMenu"
              :key="item.id"
              class="list-group-item d-flex align-items-center"
            >
              <img
                v-if="item.pictureUrl"
                :src="item.pictureUrl"
                alt=""
                class="rounded me-3"
                style="width: 64px; height: 64px; object-fit: cover"
              />

              <div class="flex-grow-1">
                <div class="fw-semibold">{{ item.name }}</div>
                <small class="text-muted">
                  ID: {{ item.id }} ·
                  Категория: {{ categoryName(item.group_id) || "—" }}
                  <span v-if="item.price !== null">
                    · Цена: {{ formatPrice(item.price) }}
                  </span>
                </small>
              </div>

              <div class="btn-group">
                <button
                  type="button"
                  class="btn btn-outline-primary btn-sm"
                  @click="startEdit(item)"
                >
                  Редактировать
                </button>
                <button
                  type="button"
                  class="btn btn-outline-danger btn-sm"
                  @click="onDeleteMenu(item.id)"
                >
                  Удалить
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка редактирования -->
    <div
      class="modal fade"
      id="editMenuModal"
      tabindex="-1"
      aria-hidden="true"
      ref="editModalRef"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <form @submit.prevent="onSaveEdit">
            <div class="modal-header">
              <h5 class="modal-title">
                Редактировать позицию #{{ editMenu.id }}
              </h5>
              <button
                type="button"
                class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              ></button>
            </div>

            <div class="modal-body">
              <div class="row g-3">
                <div class="col-md-4">
                  <label class="form-label">Название</label>
                  <input
                    v-model="editMenu.name"
                    type="text"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-md-4">
                  <label class="form-label">Категория</label>
                  <select
                    v-model="editMenu.group_id"
                    class="form-select"
                    required
                  >
                    <option :value="null">Выберите категорию...</option>
                    <option
                      v-for="cat in categories"
                      :key="cat.id"
                      :value="cat.id"
                    >
                      {{ cat.name }}
                    </option>
                  </select>
                </div>

                <div class="col-md-4">
                  <label class="form-label">Цена</label>
                  <input
                    v-model.number="editMenu.price"
                    type="number"
                    step="0.01"
                    min="0"
                    class="form-control"
                  />
                </div>

                <div class="col-md-6">
                  <label class="form-label">Картинка</label>
                  <input
                    type="file"
                    class="form-control"
                    accept="image/*"
                    @change="onEditPictureChange"
                  />
                  <div v-if="editMenu.pictureUrl" class="mt-2">
                    <img
                      :src="editMenu.pictureUrl"
                      alt=""
                      class="rounded"
                      style="width: 120px; height: 120px; object-fit: cover"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button
                type="button"
                class="btn btn-secondary"
                data-bs-dismiss="modal"
              >
                Закрыть
              </button>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="loadingEdit"
              >
                Сохранить изменения
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/styles/admin.css";

const categories = ref([]);
const menu = ref([]);
const loadingList = ref(false);
const loadingAdd = ref(false);
const loadingEdit = ref(false);
const error = ref("");

const menuStats = ref({
  total: 0,
  avg: 0,
  max: 0,
  min: 0,
});

const newMenu = ref({
  name: "",
  group_id: null,
  price: 0,
  pictureFile: null,
});

const editMenu = ref({
  id: null,
  name: "",
  group_id: null,
  price: 0,
  pictureUrl: null,
  pictureFile: null,
});

// фильтры
const filterId = ref("");
const filterName = ref("");
const filterCategoryId = ref("");
const filterPriceMin = ref("");
const filterPriceMax = ref("");

const editModalRef = ref(null);
let editModalInstance = null;

function formatPrice(value) {
  const num = Number(value || 0);
  return num.toFixed(2);
}

function categoryName(id) {
  const c = categories.value.find((x) => x.id === id);
  return c ? c.name : "";
}

const filteredMenu = computed(() => {
  return menu.value.filter((item) => {
    if (filterId.value.trim()) {
      if (String(item.id) !== filterId.value.trim()) return false;
    }

    if (filterName.value.trim()) {
      if (
        !item.name
          .toLowerCase()
          .includes(filterName.value.trim().toLowerCase())
      ) {
        return false;
      }
    }

    if (filterCategoryId.value) {
      if (String(item.group_id) !== filterCategoryId.value) return false;
    }

    const price = Number(item.price || 0);
    if (filterPriceMin.value !== "") {
      if (price < Number(filterPriceMin.value)) return false;
    }
    if (filterPriceMax.value !== "") {
      if (price > Number(filterPriceMax.value)) return false;
    }

    return true;
  });
});

async function fetchCategories() {
  const { data } = await axios.get("/api/categories/");
  categories.value = data;
}

async function fetchMenu() {
  loadingList.value = true;
  error.value = "";
  try {
    const { data } = await axios.get("/api/menu/");
    menu.value = data.map((item) => ({
      ...item,
      name: item.name ?? item.title ?? "",
      group_id: item.group_id ?? item.group ?? item.category ?? null,
      price: item.price ?? 0,
      pictureUrl: item.picture || item.image || null,
    }));
  } catch (e) {
    error.value = "Не удалось загрузить меню";
  } finally {
    loadingList.value = false;
  }
}

async function fetchMenuStats() {
  try {
    const { data } = await axios.get("/api/menu/stats/");
    menuStats.value = {
      total: data.total ?? data.count ?? 0,
      avg: Number(data.avg ?? 0),
      max: Number(data.max ?? 0),
      min: Number(data.min ?? 0),
    };
  } catch {
    // статистика не критична
  }
}

function onNewPictureChange(event) {
  const file = event.target.files?.[0] || null;
  newMenu.value.pictureFile = file;
}

function onEditPictureChange(event) {
  const file = event.target.files?.[0] || null;
  editMenu.value.pictureFile = file;
  if (file) {
    editMenu.value.pictureUrl = URL.createObjectURL(file);
  }
}

async function onAddMenu() {
  if (!newMenu.value.name || !newMenu.value.group_id) return;

  loadingAdd.value = true;
  try {
    const formData = new FormData();
    formData.append("name", newMenu.value.name);
    formData.append("group_id", newMenu.value.group_id);
    formData.append("price", String(newMenu.value.price || 0));
    if (newMenu.value.pictureFile) {
      formData.append("picture", newMenu.value.pictureFile);
    }

    const { data } = await axios.post("/api/menu/", formData);
    menu.value.push({
      ...data,
      name: data.name ?? data.title ?? newMenu.value.name,
      group_id: data.group_id ?? data.group ?? data.category ?? newMenu.value.group_id,
      price: data.price ?? newMenu.value.price,
      pictureUrl: data.picture || data.image || null,
    });

    newMenu.value = {
      name: "",
      group_id: null,
      price: 0,
      pictureFile: null,
    };

    await fetchMenuStats();
  } catch {
    alert("Ошибка при добавлении позиции меню");
  } finally {
    loadingAdd.value = false;
  }
}

function startEdit(item) {
  editMenu.value = {
    id: item.id,
    name: item.name,
    group_id: item.group_id,
    price: item.price ?? 0,
    pictureUrl: item.pictureUrl,
    pictureFile: null,
  };

  if (!editModalInstance && editModalRef.value) {
    // eslint-disable-next-line no-undef
    editModalInstance = new bootstrap.Modal(editModalRef.value);
  }
  editModalInstance?.show();
}

async function onSaveEdit() {
  if (!editMenu.value.id) return;

  loadingEdit.value = true;
  try {
    const formData = new FormData();
    formData.append("name", editMenu.value.name);
    formData.append("group_id", editMenu.value.group_id);
    formData.append("price", String(editMenu.value.price || 0));
    if (editMenu.value.pictureFile) {
      formData.append("picture", editMenu.value.pictureFile);
    }

    const { data } = await axios.patch(
      `/api/menu/${editMenu.value.id}/`,
      formData
    );

    const idx = menu.value.findIndex((m) => m.id === editMenu.value.id);
    if (idx !== -1) {
      menu.value[idx] = {
        ...menu.value[idx],
        ...data,
        name: data.name ?? data.title ?? editMenu.value.name,
        group_id:
          data.group_id ?? data.group ?? data.category ?? editMenu.value.group_id,
        price: data.price ?? editMenu.value.price,
        pictureUrl: data.picture || data.image || menu.value[idx].pictureUrl,
      };
    }

    await fetchMenuStats();
    editModalInstance?.hide();
  } catch {
    alert("Ошибка при сохранении изменений");
  } finally {
    loadingEdit.value = false;
  }
}

async function onDeleteMenu(id) {
  if (!confirm("Удалить позицию меню?")) return;

  try {
    await axios.delete(`/api/menu/${id}/`);
    menu.value = menu.value.filter((m) => m.id !== id);
    await fetchMenuStats();
  } catch {
    alert("Ошибка при удалении");
  }
}

onMounted(async () => {
  await Promise.all([fetchCategories(), fetchMenu(), fetchMenuStats()]);
});
</script>
