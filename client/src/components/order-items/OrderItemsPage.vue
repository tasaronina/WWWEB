<script setup>
import { ref, computed, onMounted, onBeforeMount } from "vue";
import { apiGet, apiPost, apiPatch, apiDelete } from "@/api";
import axios from "axios";
import "@/styles/admin.css";

axios.defaults.withCredentials = true

const canAdmin = ref(false)
async function detectAdmin(){
  if (typeof window!=="undefined" && (window.IS_ADMIN===true||window.__CAN_ADMIN__===true||window.vCanAdmin===true)) return true
  try{ if(localStorage.getItem("is_admin")==="1") return true }catch{}
  const eps=["/api/me/","/api/auth/me/","/api/users/me/","/api/user/","/api/whoami/"]
  for(const ep of eps){
    try{
      const {data}=await axios.get(ep)
      if(!data) continue
      const role=(data.role||"").toString().toLowerCase()
      if(data.is_superuser||data.is_staff||data.is_admin||["admin","staff","manager","superuser"].includes(role)) return true
    }catch{}
  }
  return false
}

const items = ref([]);
const orders = ref([]);
const menuItems = ref([]);
const stats = ref({});

const loading = ref(false);
const error = ref("");

const newItem = ref({ order_id: "", menu_id: "", qty: 1 });

const filters = ref({ id: "", order: "", menu: "", qty: "" });

const ordersMap = computed(() => { const m = new Map(); orders.value.forEach((o) => m.set(o.id, o)); return m; });
const menuMap = computed(() => { const m = new Map(); menuItems.value.forEach((mi) => m.set(mi.id, mi)); return m; });

function rawId(x) { return typeof x === "object" ? x?.id : x }

function customerLabel(raw) {
  if (!raw) return "";
  if (typeof raw === "object") return raw.name || raw.fio || raw.username || raw.email || `Клиент #${raw.id ?? ""}`;
  const found = ordersMap.value.get(raw);
  if (found && typeof found.customer === "object") {
    const c = found.customer;
    return c.name || c.fio || c.username || c.email || `Клиент #${c.id ?? ""}`;
  }
  return `Клиент #${raw}`;
}
function orderLabel(raw) {
  if (!raw) return "";
  if (typeof raw === "object") { const id = raw.id ?? ""; const client = customerLabel(raw.customer); return client ? `#${id} — ${client}` : `#${id}`; }
  const found = ordersMap.value.get(raw);
  if (found) { const client = customerLabel(found.customer); return client ? `#${found.id} — ${client}` : `#${found.id}`; }
  return `#${raw}`;
}
function menuLabel(raw) {
  if (!raw) return "";
  if (typeof raw === "object") return raw.name || raw.title || `Поз. #${raw.id ?? ""}`;
  const found = menuMap.value.get(raw);
  if (found) return found.name || found.title || `Поз. #${found.id}`;
  return `Поз. #${raw}`;
}

const itemStats = computed(() => {
  const ids = items.value.map((i) => i.id);
  if (!ids.length) return { count: 0, avg: null, max: null, min: null };
  const sumIds = ids.reduce((acc, x) => acc + x, 0);
  return { count: ids.length, avg: sumIds / ids.length, max: Math.max(...ids), min: Math.min(...ids) };
});

const filteredItems = computed(() => {
  const idPart = filters.value.id.trim();
  const orderPart = filters.value.order.trim().toLowerCase();
  const menuPart = filters.value.menu.trim().toLowerCase();
  const qtyPart = filters.value.qty.trim();
  return items.value.filter((it) => {
    if (idPart && !String(it.id).includes(idPart)) return false;
    if (orderPart && !orderLabel(it.order).toLowerCase().includes(orderPart)) return false;
    if (menuPart && !menuLabel(it.menu).toLowerCase().includes(menuPart)) return false;
    const qtyVal = it.qty ?? it.quantity ?? "";
    if (qtyPart && !String(qtyVal).includes(qtyPart)) return false;
    return true;
  });
});

function resetFilters(){ filters.value = { id: "", order: "", menu: "", qty: "" } }

async function loadData() {
  loading.value = true; error.value = "";
  try {
    const [itemsData, ordersData, menuData, statsData] = await Promise.all([
      apiGet("order-items/"), apiGet("orders/"), apiGet("menu/"), apiGet("order-items/stats/"),
    ]);
    orders.value = ordersData;
    menuItems.value = menuData;
    stats.value = statsData || {};
    items.value = itemsData.map((it) => ({ ...it, isEditing: false, edits: null }));
  } catch (e) {
    error.value = "Не удалось загрузить позиции заказа";
  } finally { loading.value = false }
}

async function handleCreate() {
  if (!canAdmin.value) return;
  if (!newItem.value.order_id || !newItem.value.menu_id) return;
  try {
    await apiPost("order-items/", {
      order_id: Number(newItem.value.order_id),
      menu_id: Number(newItem.value.menu_id),
      qty: Number(newItem.value.qty || 1),
    });
    newItem.value = { order_id: "", menu_id: "", qty: 1 };
    await loadData();
  } catch (e) { error.value = "Не удалось создать позицию заказа" }
}

function startEditRow(row) {
  if (!canAdmin.value) return;
  row.isEditing = true;
  row.edits = { order_id: rawId(row.order), menu_id: rawId(row.menu), qty: Number(row.qty ?? row.quantity ?? 1) };
}
function cancelEditRow(row) { row.isEditing = false; row.edits = null }
async function saveEditRow(row) {
  if (!canAdmin.value || !row?.edits) return;
  try {
    await apiPatch(`order-items/${row.id}/`, {
      order_id: Number(row.edits.order_id),
      menu_id: Number(row.edits.menu_id),
      qty: Number(row.edits.qty || 1),
    });
    await loadData();
  } catch (e) { error.value = "Не удалось сохранить позицию" }
  finally { row.isEditing = false; row.edits = null }
}
async function handleDeleteRow(row) {
  if (!canAdmin.value) return;
  if (!confirm(`Удалить позицию #${row.id}?`)) return;
  try { await apiDelete(`order-items/${row.id}/`); await loadData() }
  catch (e) { error.value = "Не удалось удалить позицию" }
}

onBeforeMount(async ()=>{ canAdmin.value = await detectAdmin() })
onMounted(loadData);
</script>

<template>
  <div class="container mt-4">
    <h1 class="mb-3">Добавить позицию заказа</h1>

    <div class="alert alert-light border mb-4">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего позиций: <strong>{{ itemStats.count }}</strong></span>
        <span>Средний ID: <strong>{{ itemStats.avg != null ? itemStats.avg.toFixed(2) : "—" }}</strong></span>
        <span>Максимальный ID: <strong>{{ itemStats.max ?? "—" }}</strong></span>
        <span>Минимальный ID: <strong>{{ itemStats.min ?? "—" }}</strong></span>
      </div>
    </div>

    <form class="row g-3 align-items-end mb-4" @submit.prevent="handleCreate" v-if="canAdmin">
      <div class="col-md-4">
        <label class="form-label">Заказ</label>
        <select v-model="newItem.order_id" class="form-select">
          <option value="">Выберите заказ...</option>
          <option v-for="o in orders" :key="o.id" :value="o.id">{{ orderLabel(o) }}</option>
        </select>
      </div>
      <div class="col-md-4">
        <label class="form-label">Позиция меню</label>
        <select v-model="newItem.menu_id" class="form-select">
          <option value="">Выберите позицию меню...</option>
          <option v-for="m in menuItems" :key="m.id" :value="m.id">{{ menuLabel(m) }}</option>
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

    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-2"><input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" /></div>
          <div class="col-md-3"><input v-model="filters.order" type="text" class="form-control" placeholder="Фильтр по заказу" /></div>
          <div class="col-md-3"><input v-model="filters.menu" type="text" class="form-control" placeholder="Фильтр по позиции" /></div>
          <div class="col-md-2"><input v-model="filters.qty" type="text" class="form-control" placeholder="Фильтр по кол-ву" /></div>
          <div class="col-md-2"><button type="button" class="btn btn-outline-secondary w-100" @click="resetFilters">Сброс</button></div>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

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
            <td>{{ row.id }}</td>

            <td v-if="!row.isEditing">{{ orderLabel(row.order) }}</td>
            <td v-else style="max-width: 220px">
              <select v-model="row.edits.order_id" class="form-select form-select-sm">
                <option v-for="o in orders" :key="o.id" :value="o.id">{{ orderLabel(o) }}</option>
              </select>
            </td>

            <td v-if="!row.isEditing">{{ menuLabel(row.menu) }}</td>
            <td v-else style="max-width: 240px">
              <select v-model="row.edits.menu_id" class="form-select form-select-sm">
                <option v-for="m in menuItems" :key="m.id" :value="m.id">{{ menuLabel(m) }}</option>
              </select>
            </td>

            <td v-if="!row.isEditing">{{ row.qty ?? row.quantity }}</td>
            <td v-else style="max-width: 110px">
              <input v-model.number="row.edits.qty" type="number" min="1" class="form-control form-control-sm" />
            </td>

            <td>
              <template v-if="!row.isEditing && canAdmin">
                <button class="btn btn-sm btn-outline-primary me-2" @click="startEditRow(row)">Редактировать</button>
                <button class="btn btn-sm btn-danger" @click="handleDeleteRow(row)">Удалить</button>
              </template>
              <template v-else-if="row.isEditing && canAdmin">
                <button class="btn btn-sm btn-success me-2" @click="saveEditRow(row)">Сохранить</button>
                <button class="btn btn-sm btn-outline-secondary" @click="cancelEditRow(row)">Отмена</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
