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

const editDialogVisible = ref(false);

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
  qrDataUrl.value = await QRCode.toDataURL(u, { width: 220, margin: 1 });
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

const customerSelectItems = () =>
  customers.value.map((c) => ({ title: `${c.name} (#${c.id})`, value: c.id }));

const menuSelectItems = () =>
  menu.value.map((m) => ({ title: `${m.title} (${m.price}) #${m.id}`, value: m.id }));

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
  editDialogVisible.value = true;
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
  <div>
    <div class="d-flex justify-space-between align-center mb-3">
      <div class="text-h6">Заказы</div>
    </div>

    <div class="text-medium-emphasis mb-4" v-if="stats">
      Всего заказов: <b>{{ stats.total_orders }}</b>
      <span class="mx-2">|</span>
      Позиций: <b>{{ stats.items_total }}</b>
      <span class="mx-2">|</span>
      Кол-во (шт): <b>{{ stats.qty_total }}</b>
      <span class="mx-2">|</span>
      Выручка: <b>{{ stats.revenue }}</b>
    </div>
    <div class="text-medium-emphasis mb-4" v-else>Статистика: —</div>

    <v-card variant="flat" border class="mb-4">
      <v-card-title class="text-subtitle-1">Добавить заказ</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="createOrder">
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="createForm.customer"
                :items="customerSelectItems()"
                item-title="title"
                item-value="value"
                label="Клиент"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="createForm.status"
                label="Статус"
                placeholder="например NEW"
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
            <v-col cols="12" md="4">
              <v-text-field v-model="filters.customer" label="Клиент (id)" variant="outlined" />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field v-model="filters.status" label="Статус" variant="outlined" />
            </v-col>
            <v-col cols="12" md="4" class="d-flex align-end justify-end">
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
              <th>Клиент</th>
              <th style="width: 160px;">Статус</th>
              <th style="width: 160px;">Сумма</th>
              <th style="width: 280px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="o in items" :key="o.id">
              <td>#{{ o.id }}</td>
              <td>{{ customerName(o.customer) }}</td>
              <td>{{ o.status }}</td>
              <td>{{ o.total_price }}</td>
              <td class="d-flex ga-2">
                <v-btn size="small" variant="outlined" @click="openEdit(o)">Редактировать</v-btn>
                <v-btn size="small" variant="outlined" color="error" @click="deleteOrder(o.id)">Удалить</v-btn>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td colspan="5" class="text-medium-emphasis text-center py-4">Нет данных</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- edit order dialog -->
    <v-dialog v-model="editDialogVisible" max-width="1100">
      <v-card>
        <v-card-title>Редактировать заказ #{{ editForm.id }}</v-card-title>

        <v-card-text>
          <v-card variant="flat" border class="mb-4">
            <v-card-title class="text-subtitle-1">Шапка</v-card-title>
            <v-card-text>
              <v-form @submit.prevent.stop="saveOrder">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="editForm.customer"
                      :items="customerSelectItems()"
                      item-title="title"
                      item-value="value"
                      label="Клиент"
                      variant="outlined"
                    />
                  </v-col>

                  <v-col cols="12" md="4">
                    <v-text-field v-model="editForm.status" label="Статус" variant="outlined" />
                  </v-col>

                  <v-col cols="12" md="2" class="d-flex align-end justify-end">
                    <v-btn type="submit" color="primary" block>Сохранить</v-btn>
                  </v-col>

                  <v-col cols="12" class="text-medium-emphasis">
                    Текущая сумма: <b>{{ editForm.total_price }}</b>
                  </v-col>
                </v-row>
              </v-form>
            </v-card-text>
          </v-card>

          <v-card variant="flat" border class="mb-4">
            <v-card-title class="text-subtitle-1">Добавить позицию</v-card-title>
            <v-card-text>
              <v-form @submit.prevent.stop="addPosition">
                <v-row>
                  <v-col cols="12" md="7">
                    <v-select
                      v-model="addPosForm.menu"
                      :items="menuSelectItems()"
                      item-title="title"
                      item-value="value"
                      label="Позиция меню"
                      variant="outlined"
                    />
                  </v-col>

                  <v-col cols="12" md="3">
                    <v-text-field
                      v-model.number="addPosForm.qty"
                      type="number"
                      min="1"
                      label="Кол-во"
                      variant="outlined"
                    />
                  </v-col>

                  <v-col cols="12" md="2" class="d-flex align-end justify-end">
                    <v-btn type="submit" color="success" block>Добавить</v-btn>
                  </v-col>
                </v-row>
              </v-form>
            </v-card-text>
          </v-card>

          <v-card variant="flat" border>
            <v-card-title class="text-subtitle-1">Состав заказа</v-card-title>
            <v-card-text>
              <v-table>
                <thead>
                  <tr>
                    <th style="width: 90px;">ID</th>
                    <th>Позиция</th>
                    <th style="width: 120px;">Цена</th>
                    <th style="width: 120px;">Кол-во</th>
                    <th style="width: 140px;">Сумма</th>
                    <th style="width: 160px;">Действия</th>
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
                      <v-btn
                        size="small"
                        variant="outlined"
                        color="error"
                        @click="deletePosition(it.id)"
                      >
                        Удалить
                      </v-btn>
                    </td>
                  </tr>

                  <tr v-if="orderItems.length === 0">
                    <td colspan="6" class="text-medium-emphasis text-center py-4">Пока нет позиций</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-card-text>

        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="editDialogVisible = false">Закрыть</v-btn>
        </v-card-actions>
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
          <v-btn color="error" @click="confirmTotpAndRun">Подтвердить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style></style>
