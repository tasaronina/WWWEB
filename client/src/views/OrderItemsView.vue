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
  editDialogVisible.value = true;
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/order-items/${id}/`, {
    order: editForm.value.order,
    menu: editForm.value.menu,
    qty: Math.max(1, Number(editForm.value.qty || 1)),
  });

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
    await axios.delete(`/api/order-items/${id}/`);
    await applyFilters();
  }
}

async function deleteItem(id) {
  if (userInfo.value.is_staff && !userInfo.value.second) {
    await openTotpDialog(id);
    return;
  }

  await axios.delete(`/api/order-items/${id}/`);
  await applyFilters();
}

function menuTitle(id) {
  const found = menu.value.find((m) => m.id === id);
  if (found) return found.title;
  return `#${id}`;
}

const orderSelectItems = () => orders.value.map((o) => ({ title: `#${o.id}`, value: o.id }));
const menuSelectItems = () =>
  menu.value.map((m) => ({ title: `${m.title} (#${m.id})`, value: m.id }));

onBeforeMount(async () => {
  await fetchUserInfo();
  await fetchOrders();
  await fetchMenu();
  await applyFilters();
});
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-3">
      <div class="text-h6">Позиции заказов</div>
      <div class="text-medium-emphasis" v-if="stats">
        Всего позиций: <b>{{ stats.total }}</b>,
        Мин: <b>{{ stats.min_qty }}</b>,
        Макс: <b>{{ stats.max_qty }}</b>,
        Среднее: <b>{{ stats.avg_qty }}</b>
      </div>
    </div>

    <v-card variant="flat" border class="mb-4">
      <v-card-title class="text-subtitle-1">Добавить позицию</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="createItem">
          <v-row>
            <v-col cols="12" md="4">
              <v-select
                v-model="createForm.order"
                :items="orderSelectItems()"
                item-title="title"
                item-value="value"
                label="Заказ"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="4">
              <v-select
                v-model="createForm.menu"
                :items="menuSelectItems()"
                item-title="title"
                item-value="value"
                label="Меню"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="2">
              <v-text-field
                v-model.number="createForm.qty"
                type="number"
                min="1"
                label="Кол-во"
                variant="outlined"
              />
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
            <v-col cols="12" md="3">
              <v-text-field v-model="filters.order" label="Заказ (id)" variant="outlined" />
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field v-model="filters.menu" label="Меню (id)" variant="outlined" />
            </v-col>
            <v-col cols="12" md="2">
              <v-text-field v-model="filters.qty_min" label="Кол-во от" variant="outlined" />
            </v-col>
            <v-col cols="12" md="2">
              <v-text-field v-model="filters.qty_max" label="Кол-во до" variant="outlined" />
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
              <th style="width: 140px;">Заказ</th>
              <th>Меню</th>
              <th style="width: 140px;">Кол-во</th>
              <th style="width: 260px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td>#{{ it.id }}</td>
              <td>#{{ it.order }}</td>
              <td>{{ menuTitle(it.menu) }}</td>
              <td>{{ it.qty }}</td>
              <td class="d-flex ga-2">
                <v-btn size="small" variant="outlined" @click="openEdit(it)">Редактировать</v-btn>
                <v-btn size="small" variant="outlined" color="error" @click="deleteItem(it.id)">Удалить</v-btn>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td colspan="5" class="text-medium-emphasis text-center py-4">Нет данных</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- edit dialog -->
    <v-dialog v-model="editDialogVisible" max-width="640">
      <v-card>
        <v-card-title>Редактировать позицию</v-card-title>
        <v-card-text>
          <v-form @submit.prevent.stop="saveEdit">
            <v-select
              v-model="editForm.order"
              :items="orderSelectItems()"
              item-title="title"
              item-value="value"
              label="Заказ"
              variant="outlined"
            />
            <v-select
              v-model="editForm.menu"
              :items="menuSelectItems()"
              item-title="title"
              item-value="value"
              label="Меню"
              variant="outlined"
            />
            <v-text-field
              v-model.number="editForm.qty"
              type="number"
              min="1"
              label="Кол-во"
              variant="outlined"
            />
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
