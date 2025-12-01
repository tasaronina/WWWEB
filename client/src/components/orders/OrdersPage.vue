<script setup>
import axios from "axios"
import { ref, computed, onBeforeMount } from "vue"
import "bootstrap/dist/js/bootstrap.bundle.min.js"
import "@/styles/admin.css"

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

const orders = ref([])
const customers = ref([])
const menuItems = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

const orderToAdd = ref({ customer_id: "", status: "NEW" })
const orderToEdit = ref({ id: null, customer_id: "", status: "NEW" })
const orderItemsForEdit = ref([])
const newItemForOrder = ref({ menu_id: "", qty: 1 })
const modalItemsLoading = ref(false)

const filters = ref({ id: "", customer: "", status: "all", date: "" })
const STATUS_OPTIONS = ["NEW", "IN_PROGRESS", "DONE", "CANCELLED"]

function formatNumber(v) { if (v === null || v === undefined) return "—"; const n = Number(v); return Number.isNaN(n) ? "—" : n.toFixed(2) }
function customerLabel(raw) { if (!raw) return ""; if (typeof raw === "object") return raw.name ?? raw.fio ?? raw.username ?? raw.email ?? `Клиент #${raw.id ?? ""}`; return `Клиент #${raw}` }
const menuMap = computed(() => { const m = new Map(); for (const it of menuItems.value) m.set(it.id, it); return m })
function menuTitle(raw) { if (!raw) return ""; if (typeof raw === "object") return raw.name ?? raw.title ?? `Позиция #${raw.id ?? ""}`; const found = menuMap.value.get(raw); return found ? (found.name ?? found.title ?? `Позиция #${found.id}`) : `Позиция #${raw}` }
function menuPrice(raw) { if (!raw) return 0; if (typeof raw === "object") return Number(raw.price || 0); const found = menuMap.value.get(raw); return Number(found?.price || 0) }
const currentOrderTotal = computed(() => orderItemsForEdit.value.reduce((s, it) => s + menuPrice(it.menu ?? it.menu_id) * Number(it.qty || 0), 0))

async function fetchCustomers() { const { data } = await axios.get("/api/customers/"); customers.value = data }
async function fetchOrders() { const { data } = await axios.get("/api/orders/"); orders.value = data }
async function fetchMenu() { const { data } = await axios.get("/api/menu/"); menuItems.value = data }
async function fetchStats() { const { data } = await axios.get("/api/orders/stats/"); stats.value = data }
async function fetchOrderItems(orderId) {
  modalItemsLoading.value = true
  try {
    const { data } = await axios.get(`/api/order-items/?order_id=${orderId}`)
    orderItemsForEdit.value = data.map((it) => ({ ...it, qty: it.qty ?? 1, _origQty: Number(it.qty ?? 1) }))
  } finally { modalItemsLoading.value = false }
}
async function refreshOrders() { await Promise.all([fetchOrders(), fetchStats()]) }

onBeforeMount(async () => {
  canAdmin.value = await detectAdmin()
  loading.value = true; error.value = ""
  try { await Promise.all([fetchCustomers(), fetchMenu(), fetchOrders(), fetchStats()]) }
  catch (e) { error.value = "Не удалось загрузить данные" }
  finally { loading.value = false }
})

async function onOrderAdd() {
  if (!canAdmin.value) return
  if (!orderToAdd.value.customer_id) return
  const payload = { customer_id: Number(orderToAdd.value.customer_id), status: orderToAdd.value.status || "NEW" }
  const { data } = await axios.post("/api/orders/", payload)
  orderToAdd.value = { customer_id: "", status: "NEW" }
  await refreshOrders()
  openEditModal(data)
}

function openEditModal(order) {
  if (!canAdmin.value) return
  orderToEdit.value = { id: order.id, customer_id: order.customer?.id ?? order.customer_id ?? order.customer ?? "", status: order.status || "NEW" }
  newItemForOrder.value = { menu_id: "", qty: 1 }
  fetchOrderItems(order.id)
  const el = document.getElementById("editOrderModal")
  if (el && window.bootstrap) window.bootstrap.Modal.getOrCreateInstance(el).show()
}

function onOrderEditClick(order) { if (!canAdmin.value) return; openEditModal(order) }

async function syncOrderItems() {
  if (!canAdmin.value) return
  const promises = []
  if (newItemForOrder.value.menu_id) {
    promises.push(axios.post("/api/order-items/", { order_id: orderToEdit.value.id, menu_id: Number(newItemForOrder.value.menu_id), qty: Number(newItemForOrder.value.qty) || 1 }))
  }
  for (const it of orderItemsForEdit.value) {
    const newQty = Number(it.qty || 1)
    if (!Number.isNaN(newQty) && newQty >= 1 && it._origQty !== newQty) promises.push(axios.patch(`/api/order-items/${it.id}/`, { qty: newQty }))
  }
  if (promises.length) await Promise.all(promises)
  newItemForOrder.value = { menu_id: "", qty: 1 }
  await fetchOrderItems(orderToEdit.value.id)
}

async function onOrderUpdate() {
  if (!canAdmin.value) return
  if (!orderToEdit.value.id || !orderToEdit.value.customer_id) return
  await syncOrderItems()
  const STATUS_OPTIONS = ["NEW","IN_PROGRESS","DONE","CANCELLED"]
  const safeStatus = STATUS_OPTIONS.includes(orderToEdit.value.status) ? orderToEdit.value.status : "NEW"
  await axios.patch(`/api/orders/${orderToEdit.value.id}/`, { customer_id: Number(orderToEdit.value.customer_id), status: safeStatus })
  await refreshOrders()
  const el = document.getElementById("editOrderModal")
  if (el && window.bootstrap) window.bootstrap.Modal.getInstance(el)?.hide()
}

async function onRemoveClick(order) {
  if (!canAdmin.value) return
  if (!confirm(`Удалить заказ #${order.id}?`)) return
  await axios.delete(`/api/orders/${order.id}/`)
  await refreshOrders()
}

async function onOrderItemSave(item) {
  if (!canAdmin.value) return
  await axios.patch(`/api/order-items/${item.id}/`, { order_id: orderToEdit.value.id, menu_id: item.menu?.id ?? item.menu_id, qty: Number(item.qty) || 1 })
  await Promise.all([fetchOrderItems(orderToEdit.value.id), refreshOrders()])
}
async function onOrderItemRemove(item) {
  if (!canAdmin.value) return
  if (!confirm("Удалить позицию из заказа?")) return
  await axios.delete(`/api/order-items/${item.id}/`)
  await Promise.all([fetchOrderItems(orderToEdit.value.id), refreshOrders()])
}
async function onOrderItemAdd() {
  if (!canAdmin.value) return
  if (!orderToEdit.value.id || !newItemForOrder.value.menu_id) return
  await axios.post("/api/order-items/", { order_id: orderToEdit.value.id, menu_id: Number(newItemForOrder.value.menu_id), qty: Number(newItemForOrder.value.qty) || 1 })
  newItemForOrder.value = { menu_id: "", qty: 1 }
  await Promise.all([fetchOrderItems(orderToEdit.value.id), refreshOrders()])
}

const filteredOrders = computed(() => {
  const idPart = filters.value.id.trim()
  const customerPart = filters.value.customer.trim().toLowerCase()
  const status = filters.value.status
  const date = filters.value.date
  return orders.value.filter((o) => {
    if (idPart && !String(o.id).includes(idPart)) return false
    if (customerPart && !customerLabel(o.customer).toLowerCase().includes(customerPart)) return false
    if (status !== "all" && o.status !== status) return false
    if (date) {
      const only = o.created_at ? new Date(o.created_at).toISOString().slice(0, 10) : ""
      if (only !== date) return false
    }
    return true
  })
})
function resetFilters() { filters.value = { id: "", customer: "", status: "all", date: "" } }
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Добавить заказ</h1>

    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="card mb-4" v-if="canAdmin">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-5">
            <label class="form-label">Клиент</label>
            <select v-model="orderToAdd.customer_id" class="form-select">
              <option value="">Клиент...</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Статус</label>
            <select v-model="orderToAdd.status" class="form-select">
              <option value="NEW">NEW</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="DONE">DONE</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" type="button" @click="onOrderAdd">Добавить</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего заказов: <strong>{{ stats.count }}</strong></span>
        <span>Средний ID: <strong>{{ formatNumber(stats.avg) }}</strong></span>
        <span>Максимальный ID: <strong>{{ stats.max }}</strong></span>
        <span>Минимальный ID: <strong>{{ stats.min }}</strong></span>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-2"><input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" /></div>
          <div class="col-md-3"><input v-model="filters.customer" type="text" class="form-control" placeholder="Фильтр по клиенту" /></div>
          <div class="col-md-3">
            <select v-model="filters.status" class="form-select">
              <option value="all">Все статусы</option>
              <option value="NEW">NEW</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="DONE">DONE</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>
          <div class="col-md-3"><input v-model="filters.date" type="date" class="form-control" /></div>
          <div class="col-md-1 d-grid"><button class="btn btn-outline-secondary" @click="resetFilters">Сброс</button></div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th style="width: 90px">ID</th>
              <th>Клиент</th>
              <th style="width: 140px">Сумма</th>
              <th style="width: 180px">Статус</th>
              <th style="width: 220px">Создан</th>
              <th style="width: 170px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="6" class="text-center text-muted">Загрузка...</td></tr>
            <tr v-for="o in filteredOrders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ customerLabel(o.customer) }}</td>
              <td>{{ formatNumber(o.total_price) }}</td>
              <td>{{ o.status }}</td>
              <td>{{ o.created_at ? new Date(o.created_at).toLocaleString() : "—" }}</td>
              <td>
                <div v-if="canAdmin">
                  <button class="btn btn-sm btn-outline-primary me-2" type="button" @click="onOrderEditClick(o)">Редактировать</button>
                  <button class="btn btn-sm btn-outline-danger" type="button" @click="onRemoveClick(o)">Удалить</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filteredOrders.length"><td colspan="6" class="text-center text-muted">Заказов пока нет</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div id="editOrderModal" class="modal fade" tabindex="-1" aria-hidden="true" v-if="canAdmin">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Редактировать заказ #{{ orderToEdit.id }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>

          <div class="modal-body">
            <div class="row g-3 mb-3">
              <div class="col-md-6">
                <label class="form-label">Клиент</label>
                <select v-model="orderToEdit.customer_id" class="form-select">
                  <option value="">Клиент...</option>
                  <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label">Статус</label>
                <select v-model="orderToEdit.status" class="form-select">
                  <option value="NEW">NEW</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="DONE">DONE</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>
            </div>

            <h5 class="mt-2 mb-2">Состав заказа</h5>

            <div class="table-responsive mb-3">
              <table class="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Позиция меню</th>
                    <th style="width: 120px">Кол-во</th>
                    <th style="width: 160px">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="modalItemsLoading"><td colspan="3" class="text-center text-muted">Загрузка позиций...</td></tr>
                  <tr v-for="it in orderItemsForEdit" :key="it.id">
                    <td>{{ menuTitle(it.menu ?? it.menu_id) }}</td>
                    <td><input v-model.number="it.qty" type="number" min="1" class="form-control form-control-sm" /></td>
                    <td>
                      <button class="btn btn-sm btn-success me-2" type="button" @click="onOrderItemSave(it)">Сохранить</button>
                      <button class="btn btn-sm btn-danger" type="button" @click="onOrderItemRemove(it)">Удалить</button>
                    </td>
                  </tr>
                  <tr v-if="!modalItemsLoading && !orderItemsForEdit.length"><td colspan="3" class="text-center text-muted">Позиции ещё не добавлены</td></tr>
                </tbody>
              </table>
            </div>

            <div class="border-top pt-3 mt-3">
              <div class="row g-2 align-items-end">
                <div class="col-md-6">
                  <label class="form-label">Позиция меню</label>
                  <select v-model="newItemForOrder.menu_id" class="form-select">
                    <option value="">Позиция меню...</option>
                    <option v-for="m in menuItems" :key="m.id" :value="m.id">{{ menuTitle(m) }}</option>
                  </select>
                </div>
                <div class="col-md-2">
                  <label class="form-label">Кол-во</label>
                  <input v-model.number="newItemForOrder.qty" type="number" min="1" class="form-control" />
                </div>
                <div class="col-md-3 d-grid">
                  <button class="btn btn-primary" type="button" @click="onOrderItemAdd">Добавить позицию</button>
                </div>
              </div>

              <div class="mt-3 text-end">Сумма заказа сейчас: <strong>{{ formatNumber(currentOrderTotal) }}</strong></div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button type="button" class="btn btn-primary" @click="onOrderUpdate">Сохранить изменения заказа</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
