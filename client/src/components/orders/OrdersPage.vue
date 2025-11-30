<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import "@/styles/admin.css"

const orders = ref([])
const customers = ref([])
const menuItems = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

const orderToAdd = ref({ customer_id: "", status: "NEW" })
const orderToEdit = ref({ id: null, customer_id: "", status: "" })

const orderItemsForEdit = ref([])
const newItemForOrder = ref({ menu_id: "", qty: 1 })
const modalItemsLoading = ref(false)

function formatNumber(value) {
  if (value === null || value === undefined) return "-"
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toFixed(2)
}

function menuTitle(item) {
  return item?.name ?? item?.title ?? (item?.id ? `Позиция #${item.id}` : "-")
}

const currentOrderTotal = computed(() =>
  orderItemsForEdit.value.reduce((sum, it) => {
    const price = Number(it.menu?.price ?? 0)
    const qty = Number(it.qty ?? 0)
    const p = Number.isNaN(price) ? 0 : price
    const q = Number.isNaN(qty) ? 0 : qty
    return sum + p * q
  }, 0),
)

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
    error.value = String(e)
  } finally {
    loading.value = false
  }
})

async function onOrderAdd() {
  if (!orderToAdd.value.customer_id) return

  const payload = {
    customer_id: Number(orderToAdd.value.customer_id),
    status: orderToAdd.value.status || "NEW",
  }

  const { data } = await axios.post("/api/orders/", payload)

  orderToAdd.value = { customer_id: "", status: "NEW" }

  await refreshOrders()
  openEditModal(data)
}

function openEditModal(order) {
  orderToEdit.value = {
    id: order.id,
    customer_id: order.customer?.id ?? order.customer_id ?? order.customer ?? "",
    status: order.status,
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

async function onOrderUpdate() {
  if (!orderToEdit.value.id || !orderToEdit.value.customer_id) return

  await axios.put(`/api/orders/${orderToEdit.value.id}/`, {
    customer_id: Number(orderToEdit.value.customer_id),
    status: orderToEdit.value.status,
  })

  await refreshOrders()

  const el = document.getElementById("editOrderModal")
  if (el && window.bootstrap) {
    const modal = window.bootstrap.Modal.getInstance(el)
    if (modal) modal.hide()
  }
}

async function onRemoveClick(order) {
  if (!confirm(`Удалить заказ #${order.id}?`)) return
  await axios.delete(`/api/orders/${order.id}/`)
  await refreshOrders()
}

async function onOrderItemSave(item) {
  if (!orderToEdit.value.id) return
  const payload = {
    order_id: orderToEdit.value.id,
    menu_id: item.menu?.id ?? item.menu_id,
    qty: Number(item.qty) || 1,
  }
  await axios.put(`/api/order-items/${item.id}/`, payload)
  await Promise.all([
    fetchOrderItems(orderToEdit.value.id),
    refreshOrders(),
  ])
}

async function onOrderItemRemove(item) {
  if (!orderToEdit.value.id) return
  if (!confirm("Удалить позицию из заказа?")) return
  await axios.delete(`/api/order-items/${item.id}/`)
  await Promise.all([
    fetchOrderItems(orderToEdit.value.id),
    refreshOrders(),
  ])
}

async function onOrderItemAdd() {
  if (!orderToEdit.value.id || !newItemForOrder.value.menu_id) return

  const payload = {
    order_id: orderToEdit.value.id,
    menu_id: Number(newItemForOrder.value.menu_id),
    qty: Number(newItemForOrder.value.qty) || 1,
  }

  await axios.post("/api/order-items/", payload)

  newItemForOrder.value = { menu_id: "", qty: 1 }

  await Promise.all([
    fetchOrderItems(orderToEdit.value.id),
    refreshOrders(),
  ])
}
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Добавить заказ</h1>

    <div v-if="error" class="alert alert-danger alert-inline">
      Ошибка: {{ error }}
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-5">
            <label class="form-label">Клиент</label>
            <select v-model="orderToAdd.customer_id" class="form-select">
              <option value="">Клиент...</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">
                {{ c.name }}
              </option>
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
            <button class="btn btn-primary" type="button" @click="onOrderAdd">
              Добавить
            </button>
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
            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ o.customer?.name ?? `Клиент #${o.customer}` }}</td>
              <td>{{ formatNumber(o.total_price) }}</td>
              <td>{{ o.status }}</td>
              <td>
                {{
                  o.created_at
                    ? new Date(o.created_at).toLocaleString()
                    : "—"
                }}
              </td>
              <td>
                <button
                  class="btn btn-sm btn-outline-primary me-2"
                  type="button"
                  @click="onOrderEditClick(o)"
                >
                  Редактировать
                </button>
                <button
                  class="btn btn-sm btn-outline-danger"
                  type="button"
                  @click="onRemoveClick(o)"
                >
                  Удалить
                </button>
              </td>
            </tr>
            <tr v-if="!loading && !orders.length">
              <td colspan="6" class="text-center text-muted">
                Заказов пока нет
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модалка редактирования заказа и состава -->
    <div
      id="editOrderModal"
      class="modal fade"
      tabindex="-1"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              Редактировать заказ #{{ orderToEdit.id }}
            </h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>

          <div class="modal-body">
            <div class="row g-3 mb-3">
              <div class="col-md-6">
                <label class="form-label">Клиент</label>
                <select v-model="orderToEdit.customer_id" class="form-select">
                  <option value="">Клиент...</option>
                  <option v-for="c in customers" :key="c.id" :value="c.id">
                    {{ c.name }}
                  </option>
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
                  <tr v-if="modalItemsLoading">
                    <td colspan="3" class="text-center text-muted">
                      Загрузка позиций...
                    </td>
                  </tr>
                  <tr v-for="it in orderItemsForEdit" :key="it.id">
                    <td>{{ menuTitle(it.menu) }}</td>
                    <td>
                      <input
                        v-model.number="it.qty"
                        type="number"
                        min="1"
                        class="form-control form-control-sm"
                      />
                    </td>
                    <td>
                      <button
                        class="btn btn-sm btn-success me-2"
                        type="button"
                        @click="onOrderItemSave(it)"
                      >
                        Сохранить
                      </button>
                      <button
                        class="btn btn-sm btn-danger"
                        type="button"
                        @click="onOrderItemRemove(it)"
                      >
                        Удалить
                      </button>
                    </td>
                  </tr>
                  <tr v-if="!modalItemsLoading && !orderItemsForEdit.length">
                    <td colspan="3" class="text-center text-muted">
                      Позиции ещё не добавлены
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="border-top pt-3 mt-3">
              <div class="row g-2 align-items-end">
                <div class="col-md-6">
                  <label class="form-label">Позиция меню</label>
                  <select
                    v-model="newItemForOrder.menu_id"
                    class="form-select"
                  >
                    <option value="">Позиция меню...</option>
                    <option v-for="m in menuItems" :key="m.id" :value="m.id">
                      {{ menuTitle(m) }}
                    </option>
                  </select>
                </div>
                <div class="col-md-2">
                  <label class="form-label">Кол-во</label>
                  <input
                    v-model.number="newItemForOrder.qty"
                    type="number"
                    min="1"
                    class="form-control"
                  />
                </div>
                <div class="col-md-3 d-grid">
                  <button
                    class="btn btn-primary"
                    type="button"
                    @click="onOrderItemAdd"
                  >
                    Добавить позицию
                  </button>
                </div>
              </div>

              <div class="mt-3 text-end">
                Сумма заказа сейчас:
                <strong>{{ formatNumber(currentOrderTotal) }}</strong>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              Закрыть
            </button>
            <button
              type="button"
              class="btn btn-primary"
              @click="onOrderUpdate"
            >
              Сохранить изменения заказа
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
