<script setup>
import axios from "axios"
import { ref, computed, onBeforeMount } from "vue"
import "@/styles/admin.css"

// ---------------- state ----------------
const orders = ref([])
const customers = ref([])
const menuItems = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

// Добавление
const orderToAdd = ref({ customer_id: "", status: "NEW" })

// Редактирование
const orderToEdit = ref({ id: null, customer_id: "", status: "NEW" })

// Состав заказа в модалке
const orderItemsForEdit = ref([]) // { id, order, menu|menu_id, qty, _origQty }
const newItemForOrder = ref({ menu_id: "", qty: 1 })
const modalItemsLoading = ref(false)

// Единые фильтры (как на всех страницах)
const filters = ref({ id: "", customer: "", status: "all", date: "" })

// ⚠️ Набор статусов строго под твой сериалайзер
const STATUS_OPTIONS = ["NEW", "IN_PROGRESS", "DONE", "CANCELLED"]

// ---------------- utils ----------------
function formatNumber(v) {
  if (v === null || v === undefined) return "—"
  const n = Number(v)
  return Number.isNaN(n) ? "—" : n.toFixed(2)
}
function customerLabel(raw) {
  if (!raw) return ""
  if (typeof raw === "object") {
    return raw.name ?? raw.fio ?? raw.username ?? raw.email ?? `Клиент #${raw.id ?? ""}`
  }
  return `Клиент #${raw}`
}
const menuMap = computed(() => {
  const m = new Map()
  for (const it of menuItems.value) m.set(it.id, it)
  return m
})
function menuTitle(raw) {
  if (!raw) return ""
  if (typeof raw === "object") return raw.name ?? raw.title ?? `Позиция #${raw.id ?? ""}`
  const found = menuMap.value.get(raw)
  return found ? (found.name ?? found.title ?? `Позиция #${found.id}`) : `Позиция #${raw}`
}
function menuPrice(raw) {
  if (!raw) return 0
  if (typeof raw === "object") return Number(raw.price || 0)
  const found = menuMap.value.get(raw)
  return Number(found?.price || 0)
}
const currentOrderTotal = computed(() =>
  orderItemsForEdit.value.reduce((sum, it) => {
    const price = menuPrice(it.menu ?? it.menu_id)
    const qty = Number(it.qty || 0)
    return sum + price * (Number.isNaN(qty) ? 0 : qty)
  }, 0),
)

// ---------------- fetch ----------------
async function fetchCustomers() {
  const { data } = await axios.get("/api/customers/")
  customers.value = data
}
async function fetchOrders() {
  const { data } = await axios.get("/api/orders/")
  orders.value = data
}
async function fetchMenu() {
  const { data } = await axios.get("/api/menu/")
  menuItems.value = data
}
async function fetchStats() {
  const { data } = await axios.get("/api/orders/stats/")
  stats.value = data
}
async function fetchOrderItems(orderId) {
  modalItemsLoading.value = true
  try {
    const { data } = await axios.get(`/api/order-items/?order_id=${orderId}`)
    orderItemsForEdit.value = data.map((it) => ({
      ...it,
      qty: it.qty ?? 1,
      _origQty: Number(it.qty ?? 1),
    }))
  } finally {
    modalItemsLoading.value = false
  }
}
async function refreshOrders() {
  await Promise.all([fetchOrders(), fetchStats()])
}

onBeforeMount(async () => {
  loading.value = true
  error.value = ""
  try {
    await Promise.all([fetchCustomers(), fetchMenu(), fetchOrders(), fetchStats()])
  } catch (e) {
    console.error(e)
    error.value = "Не удалось загрузить данные"
  } finally {
    loading.value = false
  }
})

// ---------------- CRUD ----------------
async function onOrderAdd() {
  if (!orderToAdd.value.customer_id) return
  const payload = {
    customer_id: Number(orderToAdd.value.customer_id),
    status: orderToAdd.value.status || "NEW",
  }
  const { data } = await axios.post("/api/orders/", payload)
  orderToAdd.value = { customer_id: "", status: "NEW" }
  await refreshOrders()
  openEditModal(data) // сразу открыть состав
}

function openEditModal(order) {
  orderToEdit.value = {
    id: order.id,
    customer_id: order.customer?.id ?? order.customer_id ?? order.customer ?? "",
    status: order.status || "NEW",
  }
  newItemForOrder.value = { menu_id: "", qty: 1 }
  fetchOrderItems(order.id)

  const el = document.getElementById("editOrderModal")
  if (el && window.bootstrap) {
    const modal = window.bootstrap.Modal.getOrCreateInstance(el)
    modal.show()
  }
}

function onOrderEditClick(order) {
  openEditModal(order)
}

async function syncOrderItems() {
  const promises = []
  // новая позиция
  if (newItemForOrder.value.menu_id) {
    promises.push(
      axios.post("/api/order-items/", {
        order_id: orderToEdit.value.id,
        menu_id: Number(newItemForOrder.value.menu_id),
        qty: Number(newItemForOrder.value.qty) || 1,
      }),
    )
  }
  // изменённые qty
  for (const it of orderItemsForEdit.value) {
    const newQty = Number(it.qty || 1)
    if (Number.isNaN(newQty) || newQty < 1) continue
    if (it._origQty !== newQty) {
      promises.push(axios.patch(`/api/order-items/${it.id}/`, { qty: newQty }))
    }
  }
  if (promises.length) await Promise.all(promises)
  newItemForOrder.value = { menu_id: "", qty: 1 }
  await fetchOrderItems(orderToEdit.value.id)
}

async function onOrderUpdate() {
  if (!orderToEdit.value.id || !orderToEdit.value.customer_id) return

  // сначала синхронизируем состав
  await syncOrderItems()

  // затем обновляем сам заказ (строго допустимые статусы)
  const safeStatus = STATUS_OPTIONS.includes(orderToEdit.value.status)
    ? orderToEdit.value.status
    : "NEW"

  await axios.patch(`/api/orders/${orderToEdit.value.id}/`, {
    customer_id: Number(orderToEdit.value.customer_id),
    status: safeStatus,
  })

  await refreshOrders()

  const el = document.getElementById("editOrderModal")
  if (el && window.bootstrap) {
    const modal = window.bootstrap.Modal.getInstance(el)
    modal?.hide()
  }
}

async function onRemoveClick(order) {
  if (!confirm(`Удалить заказ #${order.id}?`)) return
  await axios.delete(`/api/orders/${order.id}/`)
  await refreshOrders()
}

// быстрые действия по строкам состава
async function onOrderItemSave(item) {
  await axios.patch(`/api/order-items/${item.id}/`, {
    order_id: orderToEdit.value.id,
    menu_id: item.menu?.id ?? item.menu_id,
    qty: Number(item.qty) || 1,
  })
  await Promise.all([fetchOrderItems(orderToEdit.value.id), refreshOrders()])
}
async function onOrderItemRemove(item) {
  if (!confirm("Удалить позицию из заказа?")) return
  await axios.delete(`/api/order-items/${item.id}/`)
  await Promise.all([fetchOrderItems(orderToEdit.value.id), refreshOrders()])
}
async function onOrderItemAdd() {
  if (!orderToEdit.value.id || !newItemForOrder.value.menu_id) return
  await axios.post("/api/order-items/", {
    order_id: orderToEdit.value.id,
    menu_id: Number(newItemForOrder.value.menu_id),
    qty: Number(newItemForOrder.value.qty) || 1,
  })
  newItemForOrder.value = { menu_id: "", qty: 1 }
  await Promise.all([fetchOrderItems(orderToEdit.value.id), refreshOrders()])
}

// ---------------- filters ----------------
const filteredOrders = computed(() => {
  const idPart = filters.value.id.trim()
  const customerPart = filters.value.customer.trim().toLowerCase()
  const status = filters.value.status
  const date = filters.value.date

  return orders.value.filter((o) => {
    if (idPart && !String(o.id).includes(idPart)) return false
    if (customerPart) {
      const name = customerLabel(o.customer).toLowerCase()
      if (!name.includes(customerPart)) return false
    }
    if (status !== "all" && o.status !== status) return false
    if (date) {
      const only = o.created_at ? new Date(o.created_at).toISOString().slice(0, 10) : ""
      if (only !== date) return false
    }
    return true
  })
})
function resetFilters() {
  filters.value = { id: "", customer: "", status: "all", date: "" }
}
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Добавить заказ</h1>

    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <!-- Добавление -->
    <div class="card mb-4">
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
              <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" type="button" @click="onOrderAdd">Добавить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Статистика -->
    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего заказов: <strong>{{ stats.count }}</strong></span>
        <span>Средний ID: <strong>{{ formatNumber(stats.avg) }}</strong></span>
        <span>Максимальный ID: <strong>{{ stats.max }}</strong></span>
        <span>Минимальный ID: <strong>{{ stats.min }}</strong></span>
      </div>
    </div>

    <!-- Фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-2">
            <input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" />
          </div>
          <div class="col-md-3">
            <input v-model="filters.customer" type="text" class="form-control" placeholder="Фильтр по клиенту" />
          </div>
          <div class="col-md-3">
            <select v-model="filters.status" class="form-select">
              <option value="all">Все статусы</option>
              <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="col-md-3">
            <input v-model="filters.date" type="date" class="form-control" />
          </div>
          <div class="col-md-1 d-grid">
            <button class="btn btn-outline-secondary" @click="resetFilters">Сброс</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Таблица -->
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
            <tr v-if="loading">
              <td colspan="6" class="text-center text-muted">Загрузка...</td>
            </tr>
            <tr v-for="o in filteredOrders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ customerLabel(o.customer) }}</td>
              <td>{{ formatNumber(o.total_price) }}</td>
              <td>{{ o.status }}</td>
              <td>{{ o.created_at ? new Date(o.created_at).toLocaleString() : "—" }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-2" type="button" @click="onOrderEditClick(o)">
                  Редактировать
                </button>
                <button class="btn btn-sm btn-outline-danger" type="button" @click="onRemoveClick(o)">
                  Удалить
                </button>
              </td>
            </tr>
            <tr v-if="!loading && !filteredOrders.length">
              <td colspan="6" class="text-center text-muted">Заказов пока нет</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модалка -->
    <div id="editOrderModal" class="modal fade" tabindex="-1" aria-hidden="true">
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
                  <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
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
                  <tr v-if="modalItemsLoading">
                    <td colspan="3" class="text-center text-muted">Загрузка позиций...</td>
                  </tr>
                  <tr v-for="it in orderItemsForEdit" :key="it.id">
                    <td>{{ menuTitle(it.menu ?? it.menu_id) }}</td>
                    <td>
                      <input v-model.number="it.qty" type="number" min="1" class="form-control form-control-sm" />
                    </td>
                    <td>
                      <button class="btn btn-sm btn-success me-2" type="button" @click="onOrderItemSave(it)">
                        Сохранить
                      </button>
                      <button class="btn btn-sm btn-danger" type="button" @click="onOrderItemRemove(it)">
                        Удалить
                      </button>
                    </td>
                  </tr>
                  <tr v-if="!modalItemsLoading && !orderItemsForEdit.length">
                    <td colspan="3" class="text-center text-muted">Позиции ещё не добавлены</td>
                  </tr>
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

              <div class="mt-3 text-end">
                Сумма заказа сейчас: <strong>{{ formatNumber(currentOrderTotal) }}</strong>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button type="button" class="btn btn-primary" @click="onOrderUpdate">
              Сохранить изменения заказа
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
