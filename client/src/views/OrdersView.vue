<script setup>
import { onBeforeMount, ref, nextTick } from "vue";
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

const customers = ref([]);
const menu = ref([]);

const filters = ref({
  customer: "",
  status: "",
});

const createForm = ref({
  customer: null,
  status: "",
});

const editForm = ref({
  id: null,
  customer: null,
  status: "",
  total_price: 0,
});

const orderItems = ref([]);

const addPosForm = ref({
  menu: null,
  qty: 1,
});

const openModalBtn = ref(null);

const totpDialogVisible = ref(false);
const totpUrl = ref("");
const qrDataUrl = ref("");
const totpCode = ref("");
const totpError = ref(false);
const pendingAction = ref({
  type: "",
  id: null,
});

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

async function fetchCustomers() {
  const r = await axios.get("/api/customers/");
  customers.value = r.data || [];
}

async function fetchMenu() {
  const r = await axios.get("/api/menu/");
  menu.value = r.data || [];
}

async function fetchItems() {
  const r = await axios.get("/api/orders/", { params: filters.value });
  items.value = r.data || [];
}

async function fetchStats() {
  const r = await axios.get("/api/orders/stats/", { params: filters.value });
  stats.value = r.data;
}

async function fetchOrderItems(orderId) {
  const r = await axios.get("/api/order-items/", { params: { order: orderId } });
  orderItems.value = r.data || [];
}

async function applyFilters() {
  await fetchItems();
  await fetchStats();
}

function customerName(id) {
  const found = customers.value.find((c) => c.id === id);
  if (found) return found.name;
  return `#${id}`;
}

function menuTitle(id) {
  const found = menu.value.find((m) => m.id === id);
  if (found) return found.title;
  return `#${id}`;
}

function menuPrice(id) {
  const found = menu.value.find((m) => m.id === id);
  if (!found) return "";
  if (found.price == null) return "";
  return found.price;
}

async function createOrder() {
  if (!createForm.value.customer) return;

  const r = await axios.post("/api/orders/", {
    customer: createForm.value.customer,
    status: createForm.value.status || "NEW",
  });

  createForm.value = { customer: null, status: "" };
  await applyFilters();

  await openEdit(r.data);
}

async function openEdit(o) {
  editForm.value = {
    id: o.id,
    customer: o.customer,
    status: o.status,
    total_price: o.total_price || 0,
  };

  addPosForm.value = { menu: null, qty: 1 };

  await fetchOrderItems(o.id);

  await nextTick();
  if (openModalBtn.value) {
    openModalBtn.value.click();
  }
}

async function saveOrder() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/orders/${id}/`, {
    customer: editForm.value.customer,
    status: editForm.value.status,
  });

  await applyFilters();

  const updated = items.value.find((x) => x.id === id);
  if (updated) {
    editForm.value.total_price = updated.total_price || 0;
  }
}

async function openTotpDialog(type, id) {
  pendingAction.value = { type: type, id: id };
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

  pendingAction.value = { type: "", id: null };
}

async function confirmTotpAndRun() {
  totpError.value = false;

  const ok = await userStore.verifyTotp(totpCode.value);
  await fetchUserInfo();

  if (!ok) {
    totpError.value = true;
    totpCode.value = "";
    return;
  }

  const t = pendingAction.value.type;
  const id = pendingAction.value.id;

  closeTotpDialog();

  if (t === "order" && id) {
    await axios.delete(`/api/orders/${id}/`);
    await applyFilters();
    return;
  }

  if (t === "position" && id) {
    await axios.delete(`/api/order-items/${id}/`);

    await fetchOrderItems(editForm.value.id);
    await applyFilters();

    const updated = items.value.find((x) => x.id === editForm.value.id);
    if (updated) {
      editForm.value.total_price = updated.total_price || 0;
    }

    return;
  }
}

async function deleteOrder(id) {
  if (userInfo.value.is_staff && !userInfo.value.second) {
    await openTotpDialog("order", id);
    return;
  }

  await axios.delete(`/api/orders/${id}/`);
  await applyFilters();
}

async function addPosition() {
  if (!editForm.value.id) return;
  if (!addPosForm.value.menu) return;

  await axios.post("/api/order-items/", {
    order: editForm.value.id,
    menu: addPosForm.value.menu,
    qty: addPosForm.value.qty || 1,
  });

  addPosForm.value = { menu: null, qty: 1 };

  await fetchOrderItems(editForm.value.id);
  await applyFilters();

  const updated = items.value.find((x) => x.id === editForm.value.id);
  if (updated) {
    editForm.value.total_price = updated.total_price || 0;
  }
}

async function deletePosition(id) {
  if (userInfo.value.is_staff && !userInfo.value.second) {
    await openTotpDialog("position", id);
    return;
  }

  await axios.delete(`/api/order-items/${id}/`);

  await fetchOrderItems(editForm.value.id);
  await applyFilters();

  const updated = items.value.find((x) => x.id === editForm.value.id);
  if (updated) {
    editForm.value.total_price = updated.total_price || 0;
  }
}

onBeforeMount(async () => {
  await fetchUserInfo();
  await fetchCustomers();
  await fetchMenu();
  await applyFilters();
});
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Заказы</h2>

    <div class="mb-3">
      <div class="text-muted" v-if="stats">
        Всего заказов: <b>{{ stats.total_orders }}</b>
        <span class="mx-2">|</span>
        Позиций: <b>{{ stats.items_total }}</b>
        <span class="mx-2">|</span>
        Кол-во (шт): <b>{{ stats.qty_total }}</b>
        <span class="mx-2">|</span>
        Выручка: <b>{{ stats.revenue }}</b>
      </div>
      <div class="text-muted" v-else>Статистика: —</div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Добавить заказ</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="createOrder">
          <div class="col-md-6">
            <label class="form-label">Клиент</label>
            <select class="form-select" v-model="createForm.customer">
              <option :value="null">—</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">
                {{ c.name }} (#{{ c.id }})
              </option>
            </select>
          </div>

          <div class="col-md-4">
            <label class="form-label">Статус</label>
            <input class="form-control" v-model="createForm.status" placeholder="например NEW" />
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
          <div class="col-md-4">
            <label class="form-label">Клиент (id)</label>
            <input class="form-control" v-model="filters.customer" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Статус</label>
            <input class="form-control" v-model="filters.status" />
          </div>
          <div class="col-md-4 d-flex align-items-end justify-content-end">
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
              <th>Клиент</th>
              <th style="width: 160px;">Статус</th>
              <th style="width: 160px;">Сумма</th>
              <th style="width: 220px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="o in items" :key="o.id">
              <td>#{{ o.id }}</td>
              <td>{{ customerName(o.customer) }}</td>
              <td>{{ o.status }}</td>
              <td>{{ o.total_price }}</td>
              <td class="d-flex gap-2">
                <button class="btn btn-sm btn-outline-secondary" @click="openEdit(o)">
                  Редактировать
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteOrder(o.id)">
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

    <button
      ref="openModalBtn"
      class="d-none"
      data-bs-toggle="modal"
      data-bs-target="#editOrderModal"
      type="button"
    >
      open
    </button>

    <div class="modal fade" id="editOrderModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">Редактировать заказ #{{ editForm.id }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">

            <div class="card mb-3">
              <div class="card-header">Шапка</div>
              <div class="card-body">
                <form class="row g-2" @submit.prevent.stop="saveOrder">
                  <div class="col-md-6">
                    <label class="form-label">Клиент</label>
                    <select class="form-select" v-model="editForm.customer">
                      <option v-for="c in customers" :key="c.id" :value="c.id">
                        {{ c.name }} (#{{ c.id }})
                      </option>
                    </select>
                  </div>

                  <div class="col-md-4">
                    <label class="form-label">Статус</label>
                    <input class="form-control" v-model="editForm.status" />
                  </div>

                  <div class="col-md-2 d-flex align-items-end justify-content-end">
                    <button class="btn btn-primary">Сохранить</button>
                  </div>

                  <div class="col-12 text-muted mt-2">
                    Текущая сумма: <b>{{ editForm.total_price }}</b>
                  </div>
                </form>
              </div>
            </div>

            <div class="card mb-3">
              <div class="card-header">Добавить позицию</div>
              <div class="card-body">
                <form class="row g-2" @submit.prevent.stop="addPosition">
                  <div class="col-md-7">
                    <label class="form-label">Позиция меню</label>
                    <select class="form-select" v-model="addPosForm.menu">
                      <option :value="null">—</option>
                      <option v-for="m in menu" :key="m.id" :value="m.id">
                        {{ m.title }} ({{ m.price }}) #{{ m.id }}
                      </option>
                    </select>
                  </div>

                  <div class="col-md-3">
                    <label class="form-label">Кол-во</label>
                    <input class="form-control" type="number" min="1" v-model.number="addPosForm.qty" />
                  </div>

                  <div class="col-md-2 d-flex align-items-end justify-content-end">
                    <button class="btn btn-success">Добавить</button>
                  </div>
                </form>
              </div>
            </div>

            <div class="card">
              <div class="card-header">Состав заказа</div>
              <div class="card-body table-responsive">
                <table class="table table-striped align-middle">
                  <thead>
                    <tr>
                      <th style="width: 90px;">ID</th>
                      <th>Позиция</th>
                      <th style="width: 120px;">Цена</th>
                      <th style="width: 120px;">Кол-во</th>
                      <th style="width: 140px;">Сумма</th>
                      <th style="width: 140px;">Действия</th>
                    </tr>
                  </thead>

                  <tbody>
                    <tr v-for="it in orderItems" :key="it.id">
                      <td>#{{ it.id }}</td>
                      <td>{{ menuTitle(it.menu) }}</td>
                      <td>{{ menuPrice(it.menu) }}</td>
                      <td>{{ it.qty }}</td>
                      <td>{{ it.line_price }}</td>
                      <td>
                        <button class="btn btn-sm btn-outline-danger" @click="deletePosition(it.id)">
                          Удалить
                        </button>
                      </td>
                    </tr>

                    <tr v-if="orderItems.length === 0">
                      <td colspan="6" class="text-muted text-center">Пока нет позиций</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal" type="button">Закрыть</button>
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
            <button class="btn btn-danger" type="button" @click="confirmTotpAndRun">Подтвердить</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="totpDialogVisible" class="modal-backdrop fade show"></div>

  </div>
</template>

<style></style>
