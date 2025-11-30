<script setup>
import { ref, computed, onMounted } from "vue";
import { apiGet, apiPost, apiPatch, apiDelete } from "@/api";

const items = ref([]);
const orders = ref([]);
const menuItems = ref([]);
const stats = ref({});

const loading = ref(false);
const error = ref("");

// форма добавления позиции
const newItem = ref({
  order_id: "",
  menu_id: "",
  qty: 1,
});

// фильтры
const filters = ref({
  id: "",
  order: "",
  menu: "",
  qty: "",
});

const ordersMap = computed(() => {
  const m = new Map();
  orders.value.forEach((o) => m.set(o.id, o));
  return m;
});

const menuMap = computed(() => {
  const m = new Map();
  menuItems.value.forEach((mItem) => m.set(mItem.id, mItem));
  return m;
});

function rawId(x) {
  return typeof x === "object" ? x?.id : x;
}

function customerLabel(raw) {
  if (!raw) return "";
  if (typeof raw === "object") {
    return (
      raw.name ||
      raw.fio ||
      raw.username ||
      raw.email ||
      `Клиент #${raw.id ?? ""}`
    );
  }
  const found = ordersMap.value.get(raw);
  if (found && typeof found.customer === "object") {
    const c = found.customer;
    return (
      c.name ||
      c.fio ||
      c.username ||
      c.email ||
      `Клиент #${c.id ?? ""}`
    );
  }
  return `Клиент #${raw}`;
}

function orderLabel(raw) {
  if (!raw) return "";
  if (typeof raw === "object") {
    const id = raw.id ?? "";
    const client = customerLabel(raw.customer);
    return client ? `#${id} — ${client}` : `#${id}`;
  }
  const found = ordersMap.value.get(raw);
  if (found) {
    const client = customerLabel(found.customer);
    return client ? `#${found.id} — ${client}` : `#${found.id}`;
  }
  return `#${raw}`;
}

function menuLabel(raw) {
  if (!raw) return "";
  if (typeof raw === "object") {
    return raw.name || raw.title || `Поз. #${raw.id ?? ""}`;
  }
  const found = menuMap.value.get(raw);
  if (found) return found.name || found.title || `Поз. #${found.id}`;
  return `Поз. #${raw}`;
}

// статистика по ID позиций
const itemStats = computed(() => {
  const list = items.value;
  const count = list.length;
  const ids = list.map((i) => i.id);
  if (!ids.length) return { count: 0, avg: null, max: null, min: null };
  const sumIds = ids.reduce((acc, x) => acc + x, 0);
  return {
    count,
    avg: sumIds / ids.length,
    max: Math.max(...ids),
    min: Math.min(...ids),
  };
});

// фильтрация
const filteredItems = computed(() => {
  const idPart = filters.value.id.trim();
  const orderPart = filters.value.order.trim().toLowerCase();
  const menuPart = filters.value.menu.trim().toLowerCase();
  const qtyPart = filters.value.qty.trim();

  return items.value.filter((it) => {
    if (idPart && !String(it.id).includes(idPart)) return false;

    if (orderPart) {
      const label = orderLabel(it.order).toLowerCase();
      if (!label.includes(orderPart)) return false;
    }

    if (menuPart) {
      const label = menuLabel(it.menu).toLowerCase();
      if (!label.includes(menuPart)) return false;
    }

    const qtyVal = it.qty ?? it.quantity ?? "";
    if (qtyPart && !String(qtyVal).includes(qtyPart)) return false;

    return true;
  });
});

function resetFilters() {
  filters.value.id = "";
  filters.value.order = "";
  filters.value.menu = "";
  filters.value.qty = "";
}

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    const [itemsData, ordersData, menuData, statsData] = await Promise.all([
      apiGet("order-items/"),
      apiGet("orders/"),
      apiGet("menu/"),
      apiGet("order-items/stats/"),
    ]);

    orders.value = ordersData;
    menuItems.value = menuData;
    stats.value = statsData || {};

    // чистые строки без редактируемых полей
    items.value = itemsData.map((it) => ({
      ...it,
      isEditing: false,             // режим редактирования выключен
      edits: null,                  // временные значения при редактировании
    }));
  } catch (e) {
    console.error(e);
    error.value = "Не удалось загрузить позиции заказа";
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!newItem.value.order_id || !newItem.value.menu_id) return;

  try {
    await apiPost("order-items/", {
      order_id: Number(newItem.value.order_id),
      menu_id: Number(newItem.value.menu_id),
      qty: Number(newItem.value.qty || 1),
    });
    newItem.value = { order_id: "", menu_id: "", qty: 1 };
    await loadData();
  } catch (e) {
    console.error(e);
    error.value = "Не удалось создать позицию заказа";
  }
}

// === Редактирование строки ===
function startEditRow(row) {
  row.isEditing = true;
  row.edits = {
    order_id: rawId(row.order),
    menu_id: rawId(row.menu),
    qty: Number(row.qty ?? row.quantity ?? 1),
  };
}

function cancelEditRow(row) {
  row.isEditing = false;
  row.edits = null;
}

async function saveEditRow(row) {
  if (!row?.edits) return;
  try {
    await apiPatch(`order-items/${row.id}/`, {
      order_id: Number(row.edits.order_id),
      menu_id: Number(row.edits.menu_id),
      qty: Number(row.edits.qty || 1),
    });
    await loadData();
  } catch (e) {
    console.error(e);
    error.value = "Не удалось сохранить позицию";
  } finally {
    row.isEditing = false;
    row.edits = null;
  }
}

async function handleDeleteRow(row) {
  if (!confirm(`Удалить позицию #${row.id}?`)) return;
  try {
    await apiDelete(`order-items/${row.id}/`);
    await loadData();
  } catch (e) {
    console.error(e);
    error.value = "Не удалось удалить позицию";
  }
}

onMounted(loadData);
</script>

<template>
  <div class="container mt-4">
    <h1 class="mb-3">Добавить позицию заказа</h1>

    <!-- статистика -->
    <div class="alert alert-light border mb-4">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего позиций: <strong>{{ itemStats.count }}</strong></span>
        <span>
          Средний ID:
          <strong>{{ itemStats.avg != null ? itemStats.avg.toFixed(2) : "—" }}</strong>
        </span>
        <span>Максимальный ID: <strong>{{ itemStats.max ?? "—" }}</strong></span>
        <span>Минимальный ID: <strong>{{ itemStats.min ?? "—" }}</strong></span>
      </div>
    </div>

    <!-- форма добавления -->
    <form class="row g-3 align-items-end mb-4" @submit.prevent="handleCreate">
      <div class="col-md-4">
        <label class="form-label">Заказ</label>
        <select v-model="newItem.order_id" class="form-select">
          <option value="">Выберите заказ...</option>
          <option v-for="o in orders" :key="o.id" :value="o.id">
            {{ orderLabel(o) }}
          </option>
        </select>
      </div>
      <div class="col-md-4">
        <label class="form-label">Позиция меню</label>
        <select v-model="newItem.menu_id" class="form-select">
          <option value="">Выберите позицию меню...</option>
          <option v-for="m in menuItems" :key="m.id" :value="m.id">
            {{ menuLabel(m) }}
          </option>
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label">Кол-во</label>
        <input v-model.number="newItem.qty" type="number" min="1" class="form-control" />
      </div>
      <div class="col-md-2">
        <button type="submit" class="btn btn-primary w-100">Создать</button>
      </div>
    </form>

    <!-- фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-2">
            <input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" />
          </div>
          <div class="col-md-3">
            <input v-model="filters.order" type="text" class="form-control" placeholder="Фильтр по заказу" />
          </div>
          <div class="col-md-3">
            <input v-model="filters.menu" type="text" class="form-control" placeholder="Фильтр по позиции" />
          </div>
          <div class="col-md-2">
            <input v-model="filters.qty" type="text" class="form-control" placeholder="Фильтр по кол-ву" />
          </div>
          <div class="col-md-2">
            <button type="button" class="btn btn-outline-secondary w-100" @click="resetFilters">Сброс</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- таблица -->
    <div class="table-responsive">
      <table class="table table-striped align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Заказ</th>
            <th>Позиция меню</th>
            <th>Кол-во</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredItems.length">
            <td colspan="5" class="text-center text-muted">Позиции заказа пока не добавлены</td>
          </tr>

          <tr v-for="row in filteredItems" :key="row.id">
            <!-- ID -->
            <td>{{ row.id }}</td>

            <!-- Заказ -->
            <td v-if="!row.isEditing">{{ orderLabel(row.order) }}</td>
            <td v-else style="max-width: 220px">
              <select v-model="row.edits.order_id" class="form-select form-select-sm">
                <option v-for="o in orders" :key="o.id" :value="o.id">
                  {{ orderLabel(o) }}
                </option>
              </select>
            </td>

            <!-- Позиция меню -->
            <td v-if="!row.isEditing">{{ menuLabel(row.menu) }}</td>
            <td v-else style="max-width: 240px">
              <select v-model="row.edits.menu_id" class="form-select form-select-sm">
                <option v-for="m in menuItems" :key="m.id" :value="m.id">
                  {{ menuLabel(m) }}
                </option>
              </select>
            </td>

            <!-- Количество -->
            <td v-if="!row.isEditing">{{ row.qty ?? row.quantity }}</td>
            <td v-else style="max-width: 110px">
              <input v-model.number="row.edits.qty" type="number" min="1" class="form-control form-control-sm" />
            </td>

            <!-- Действия -->
            <td>
              <template v-if="!row.isEditing">
                <button class="btn btn-sm btn-outline-primary me-2" @click="startEditRow(row)">
                  Редактировать
                </button>
                <button class="btn btn-sm btn-danger" @click="handleDeleteRow(row)">
                  Удалить
                </button>
              </template>

              <template v-else>
                <button class="btn btn-sm btn-success me-2" @click="saveEditRow(row)">
                  Сохранить
                </button>
                <button class="btn btn-sm btn-outline-secondary" @click="cancelEditRow(row)">
                  Отмена
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
