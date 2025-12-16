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

  qrDataUrl.value = await QRCode.toDataURL(u, {
    width: 220,
    margin: 1,
  });
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

onBeforeMount(async () => {
  await fetchUserInfo();
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

    <div
      v-if="totpDialogVisible"
      class="modal fade show"
      style="display: block;"
      tabindex="-1"
      aria-modal="true"
      role="dialog"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">2FA подтверждение</h5>
            <button type="button" class="btn-close" @click="closeTotpDialog"></button>
          </div>

          <div class="modal-body d-flex flex-column" style="gap: 12px;">
            <div class="text-muted" style="font-size: 14px;">
              Отсканируйте QR-код и введите код.
            </div>

            <div class="d-flex justify-content-center" v-if="qrDataUrl">
              <img :src="qrDataUrl" alt="QR" style="width: 220px; height: 220px;" />
            </div>

            <div v-if="!qrDataUrl" class="text-muted" style="font-size: 14px;">
              Не удалось получить QR. Обновите страницу и попробуйте снова.
            </div>

            <input class="form-control" placeholder="код из приложения" v-model="totpCode" />

            <div v-if="totpError" class="text-danger" style="font-size: 14px;">
              Неверный код
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" @click="closeTotpDialog">Отмена</button>
            <button class="btn btn-danger" type="button" @click="confirmTotpAndDelete">Удалить</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="totpDialogVisible" class="modal-backdrop fade show"></div>

  </div>
</template>

<style></style>
