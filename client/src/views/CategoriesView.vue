<script setup>
import { onBeforeMount, ref } from "vue";
import axios from "axios";
import { useUserStore } from "@/stores/user_store";
import QRCode from "qrcode";

const userStore = useUserStore();

const items = ref([]);
const stats = ref(null);

const userInfo = ref({
  is_authenticated: false,
  is_staff: false,
  second: false,
});

const filters = ref({ name: "" });
const createForm = ref({ name: "" });

const editForm = ref({ id: null, name: "" });
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

async function fetchItems() {
  const r = await axios.get("/api/categories/", { params: filters.value });
  items.value = r.data || [];
}

async function fetchStats() {
  const r = await axios.get("/api/categories/stats/", { params: filters.value });
  stats.value = r.data;
}

async function applyFilters() {
  await fetchItems();
  await fetchStats();
}

async function createItem() {
  if (!createForm.value.name) return;

  await axios.post("/api/categories/", { name: createForm.value.name });

  createForm.value.name = "";
  await applyFilters();
}

function openEdit(c) {
  editForm.value = { id: c.id, name: c.name };
  editDialogVisible.value = true;
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/categories/${id}/`, { name: editForm.value.name });
  editDialogVisible.value = false;

  await applyFilters();
}

async function openTotpDialog(deleteId) {
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
    await axios.delete(`/api/categories/${id}/`);
    await applyFilters();
  }
}

async function deleteItem(id) {
  if (userInfo.value.is_staff && !userInfo.value.second) {
    await openTotpDialog(id);
    return;
  }

  await axios.delete(`/api/categories/${id}/`);
  await applyFilters();
}

onBeforeMount(async () => {
  await fetchUserInfo();
  await applyFilters();
});
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-3">
      <div class="text-h6">Категории</div>
      <div class="text-medium-emphasis" v-if="stats">Всего категорий: <b>{{ stats.total }}</b></div>
    </div>

    <v-card variant="flat" border class="mb-4">
      <v-card-title class="text-subtitle-1">Добавить категорию</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="createItem">
          <v-row>
            <v-col cols="12" md="10">
              <v-text-field v-model="createForm.name" label="Название" variant="outlined" />
            </v-col>
            <v-col cols="12" md="2" class="d-flex align-end justify-end">
              <v-btn type="submit" color="primary" block>Добавить</v-btn>
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
            <v-col cols="12" md="10">
              <v-text-field
                v-model="filters.name"
                label="Название"
                placeholder="поиск..."
                variant="outlined"
              />
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
        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width: 120px;">ID</th>
              <th>Название</th>
              <th style="width: 260px;">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in items" :key="c.id">
              <td>#{{ c.id }}</td>
              <td>{{ c.name }}</td>
              <td class="d-flex ga-2">
                <v-btn size="small" variant="outlined" @click="openEdit(c)">Редактировать</v-btn>
                <v-btn size="small" variant="outlined" color="error" @click="deleteItem(c.id)">Удалить</v-btn>
              </td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="3" class="text-medium-emphasis text-center py-4">Нет данных</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- edit dialog -->
    <v-dialog v-model="editDialogVisible" max-width="520">
      <v-card>
        <v-card-title>Редактировать категорию</v-card-title>
        <v-card-text>
          <v-form @submit.prevent.stop="saveEdit">
            <v-text-field v-model="editForm.name" label="Название" variant="outlined" />
            <div class="d-flex justify-end">
              <v-btn color="primary" type="submit">Сохранить</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 2FA dialog -->
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
