<script setup>
import { onBeforeMount, ref, computed } from "vue";
import axios from "axios";
import { useUserStore } from "@/stores/user_store";
import QRCode from "qrcode";

const userStore = useUserStore();

const items = ref([]);
const stats = ref(null);
const categories = ref([]);

const userInfo = ref({
  is_authenticated: false,
  is_staff: false,
  second: false,
});

const isAdmin = computed(() => !!userInfo.value.is_authenticated && !!userInfo.value.is_staff);

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

const editDialogVisible = ref(false);

const totpDialogVisible = ref(false);
const totpUrl = ref("");
const qrDataUrl = ref("");
const totpCode = ref("");
const totpError = ref(false);
const pendingDeleteId = ref(null);

async function buildQr(u) {
  if (!u) {
    qrDataUrl.value = "";
    return;
  }
  qrDataUrl.value = await QRCode.toDataURL(u, { width: 220, margin: 1 });
}

async function fetchUserInfo() {
  const r = await axios.get("/api/user/info/");
  userInfo.value = r.data || userInfo.value;
}

function buildQuery() {
  const q = [];
  if (filters.value.title) q.push("title=" + encodeURIComponent(filters.value.title));
  if (filters.value.group) q.push("group=" + encodeURIComponent(filters.value.group));
  if (filters.value.price_min) q.push("price_min=" + encodeURIComponent(filters.value.price_min));
  if (filters.value.price_max) q.push("price_max=" + encodeURIComponent(filters.value.price_max));
  return q.join("&");
}

async function fetchCategories() {
  try {
    const r = await axios.get("/api/categories/");
    categories.value = r.data || [];
  } catch (e) {
    categories.value = [];
  }
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
  if (!isAdmin.value) return;

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
  if (!isAdmin.value) return;

  editForm.value = {
    id: m.id,
    title: m.title,
    group: m.group,
    price: m.price,
    description: m.description || "",
  };
  editDialogVisible.value = true;
}

async function saveEdit() {
  if (!isAdmin.value) return;

  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/menu/${id}/`, {
    title: editForm.value.title,
    group: editForm.value.group,
    price: editForm.value.price || "0",
    description: editForm.value.description || "",
  });

  editDialogVisible.value = false;
  await applyFilters();
}

async function openTotpDialog(deleteId) {
  if (!isAdmin.value) return;

  pendingDeleteId.value = deleteId;
  totpDialogVisible.value = true;

  totpError.value = false;
  totpCode.value = "";
  totpUrl.value = "";
  qrDataUrl.value = "";

  const u = await userStore.getTotp();
  totpUrl.value = u || "";
  await buildQr(totpUrl.value);
}

function closeTotpDialog() {
  totpDialogVisible.value = false;

  totpError.value = false;
  totpCode.value = "";
  totpUrl.value = "";
  qrDataUrl.value = "";

  pendingDeleteId.value = null;
}

async function confirmTotpAndDelete() {
  if (!isAdmin.value) return;

  totpError.value = false;

  const ok = await userStore.verifyTotp(totpCode.value);
  await fetchUserInfo();

  if (!ok) {
    totpError.value = true;
    totpCode.value = "";
    return;
  }

  const id = pendingDeleteId.value;
  closeTotpDialog();

  if (id) {
    await axios.delete(`/api/menu/${id}/`);
    await applyFilters();
  }
}

async function deleteItem(id) {
  if (!isAdmin.value) return;

  if (userInfo.value.is_staff && !userInfo.value.second) {
    await openTotpDialog(id);
    return;
  }

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
  const found = categories.value.find((c) => c.id === id);
  if (found) return found.name;
  return `#${id}`;
}

onBeforeMount(async () => {
  await fetchUserInfo();

  if (isAdmin.value) {
    await fetchCategories();
  }

  await applyFilters();
});
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-3">
      <div class="text-h6">Меню</div>

      <div class="d-flex align-center ga-2">
        <v-btn variant="outlined" size="small" color="success" @click="exportExcel">Excel</v-btn>
        <v-btn variant="outlined" size="small" color="primary" @click="exportWord">Word</v-btn>
      </div>
    </div>

    <div class="text-medium-emphasis mb-3" v-if="stats">
      Кол-во: <b>{{ stats.count }}</b>,
      Средняя цена: <b>{{ stats.avg }}</b>,
      Мин: <b>{{ stats.min }}</b>,
      Макс: <b>{{ stats.max }}</b>
    </div>

    <v-card v-if="isAdmin" variant="flat" border class="mb-4">
      <v-card-title class="text-subtitle-1">Добавить позицию меню</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="createItem">
          <v-row>
            <v-col cols="12" md="4">
              <v-text-field v-model="createForm.title" label="Название" variant="outlined" />
            </v-col>

            <v-col cols="12" md="3">
              <v-select
                v-model="createForm.group"
                :items="categories"
                item-title="name"
                item-value="id"
                label="Категория"
                variant="outlined"
                :return-object="false"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field v-model="createForm.price" label="Цена" variant="outlined" />
            </v-col>

            <v-col cols="12" md="3">
              <v-text-field v-model="createForm.description" label="Описание" variant="outlined" />
            </v-col>

            <v-col cols="12" class="d-flex justify-end">
              <v-btn type="submit" color="primary">Добавить</v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-card variant="flat" border class="mb-4">
      <v-card-title class="text-subtitle-1">Фильтры</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="applyFilters">
          <v-row>
            <v-col cols="12" md="4">
              <v-text-field v-model="filters.title" label="Название" variant="outlined" />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field v-model="filters.group" label="Категория (id)" variant="outlined" />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field v-model="filters.price_min" label="Цена от" variant="outlined" />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field v-model="filters.price_max" label="Цена до" variant="outlined" />
            </v-col>

            <v-col cols="12" md="2" class="d-flex align-end justify-end">
              <v-btn type="submit" color="primary" block>Применить</v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-card variant="flat" border>
      <v-card-title class="text-subtitle-1">Таблица</v-card-title>
      <v-card-text>
        <v-table>
          <thead>
            <tr>
              <th style="width: 90px;">ID</th>
              <th>Название</th>
              <th style="width: 220px;">Категория</th>
              <th style="width: 130px;">Цена</th>
              <th v-if="isAdmin" style="width: 260px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="m in items" :key="m.id">
              <td>#{{ m.id }}</td>
              <td>{{ m.title }}</td>
              <td>{{ categoryTitle(m.group) }}</td>
              <td>{{ m.price }}</td>
              <td v-if="isAdmin" class="d-flex ga-2">
                <v-btn size="small" variant="outlined" @click="openEdit(m)">Редактировать</v-btn>
                <v-btn size="small" variant="outlined" color="error" @click="deleteItem(m.id)">Удалить</v-btn>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td :colspan="isAdmin ? 5 : 4" class="text-medium-emphasis text-center py-4">Нет данных</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <v-dialog v-model="editDialogVisible" max-width="760">
      <v-card>
        <v-card-title>Редактировать позицию меню</v-card-title>
        <v-card-text>
          <v-form @submit.prevent.stop="saveEdit">
            <v-row>
              <v-col cols="12" md="5">
                <v-text-field v-model="editForm.title" label="Название" variant="outlined" />
              </v-col>

              <v-col cols="12" md="3">
                <v-select
                  v-model="editForm.group"
                  :items="categories"
                  item-title="name"
                  item-value="id"
                  label="Категория"
                  variant="outlined"
                  :return-object="false"
                />
              </v-col>

              <v-col cols="12" md="2">
                <v-text-field v-model="editForm.price" label="Цена" variant="outlined" />
              </v-col>

              <v-col cols="12" md="2">
                <v-text-field v-model="editForm.description" label="Описание" variant="outlined" />
              </v-col>

              <v-col cols="12" class="d-flex justify-end">
                <v-btn color="primary" type="submit">Сохранить</v-btn>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="totpDialogVisible" max-width="560">
      <v-card>
        <v-card-title>2FA подтверждение</v-card-title>
        <v-card-text>
          <div class="text-medium-emphasis mb-3" style="font-size: 14px;">
            Отсканируйте QR-код и введите код.
          </div>

          <div class="d-flex justify-center mb-3" v-if="qrDataUrl">
            <img :src="qrDataUrl" alt="QR" style="width: 220px; height: 220px;" />
          </div>

          <div v-else class="text-medium-emphasis mb-3" style="font-size: 14px;">
            Не удалось получить QR. Обновите страницу и попробуйте снова.
          </div>

          <v-text-field v-model="totpCode" label="Код из приложения" variant="outlined" />

          <div v-if="totpError" class="text-error" style="font-size: 14px;">
            Неверный код
          </div>
        </v-card-text>

        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="closeTotpDialog">Отмена</v-btn>
          <v-btn color="error" @click="confirmTotpAndDelete">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style></style>
