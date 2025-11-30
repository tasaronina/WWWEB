<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import "@/styles/admin.css"

const orders = ref([])
const customers = ref([])
const menu = ref([])
const loading = ref(false)
const error = ref("")

const orderToAdd = ref({ customer_id: null, status: "NEW" })
const orderToEdit = ref({ id: null, customer_id: null, status: "" })

// позиции для модалки
const orderItemsForEdit = ref([])
const newItemForOrder = ref({ menu_id: "", qty: 1 })
const modalItemsLoading = ref(false)

function menuTitle(m) {
  if (!m) return "-"
  return m.name ?? m.title ?? `#${m.id}`
}

function formatPrice(value) {
  if (value === null || value === undefined) return "-"
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toFixed(2)
}

// текущая сумма в модалке
const currentOrderTotal = computed(() => {
  return orderItemsForEdit.value.reduce((sum, it) => {
    const price = Number(it.menu?.price ?? 0)
    const qty = Number(it.qty ?? 0)
    return sum + price * qty
  }, 0)
})

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
  menu.value = data
}

async function fetchOrderItems(orderId) {
  modalItemsLoading.value = true
  try {
    const { data } = await axios.get(`/api/order-items/?order_id=${orderId}`)
    orderItemsForEdit.value = data
  } catch (e) {
    error.value = String(e)
  } finally {
    modalItemsLoading.value = false
  }
}

async function onOrderAdd() {
  if (!orderToAdd.value.customer_id) return

  // создаём заказ и сразу получаем его данные
  const { data: createdOrder } = await axios.post("/api/orders/", {
    customer_id: Number(orderToAdd.value.customer_id),
    status: orderToAdd.value.status || "NEW",
  })

  // очищаем форму добавления
  orderToAdd.value = { customer_id: null, status: "NEW" }

  // обновляем список заказов (чтобы он появился в таблице)
  await fetchOrders()

  // сразу открываем модалку редактирования для только что созданного заказа
  onOrderEditClick(createdOrder)
}

function onOrderEditClick(o) {
  orderToEdit.value = {
    id: o.id,
    customer_id: o.customer?.id ?? o.customer,
    status: o.status,
  }
  newItemForOrder.value = { menu_id: "", qty: 1 }
  fetchOrderItems(o.id)
  // bootstrap модалка подключена глобально через main.js
  new bootstrap.Modal(document.getElementById("editOrderModal")).show()
}

async function onOrderUpdate() {
  if (!orderToEdit.value.customer_id) return

  await axios.put(`/api/orders/${orderToEdit.value.id}/`, {
    customer_id: Number(orderToEdit.value.customer_id),
    status: orderToEdit.value.status,
  })

  await fetchOrders()

  // закрываем модалку после сохранения
  const modalEl = document.getElementById("editOrderModal")
  if (modalEl && window.bootstrap) {
    const instance = window.bootstrap.Modal.getInstance(modalEl)
    if (instance) {
      instance.hide()
    }
  }
}
async function onRemoveClick(o) {
  if (!confirm(`Удалить заказ #${o.id}?`)) return
  await axios.delete(`/api/orders/${o.id}/`)
  await fetchOrders()
}

async function onOrderItemSave(it) {
  if (!orderToEdit.value.id) return
  const orderId = orderToEdit.value.id
  const menuId = it.menu?.id ?? it.menu_id
  const qty = Number(it.qty) || 1

  await axios.put(`/api/order-items/${it.id}/`, {
    order_id: orderId,
    menu_id: menuId,
    qty,
  })

  await Promise.all([fetchOrderItems(orderId), fetchOrders()])
}

async function onOrderItemRemove(it) {
  if (!orderToEdit.value.id) return
  if (!confirm("Удалить позицию из заказа?")) return
  const orderId = orderToEdit.value.id

  await axios.delete(`/api/order-items/${it.id}/`)

  await Promise.all([fetchOrderItems(orderId), fetchOrders()])
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
  await Promise.all([fetchOrderItems(orderToEdit.value.id), fetchOrders()])
}

onBeforeMount(async () => {
  loading.value = true
  error.value = ""
  try {
    await Promise.all([fetchCustomers(), fetchOrders(), fetchMenu()])
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Добавить заказ</h1>

    <div v-if="error" class="alert alert-danger" role="alert">
      {{ error }}
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
              <th style="width: 160px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="text-center text-muted">Загрузка...</td>
            </tr>
            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>
                {{ o.customer?.name ?? (o.customer ? `#${o.customer}` : "—") }}
              </td>
              <td>{{ formatPrice(o.total_price) }}</td>
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
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Редактировать заказ #{{ orderToEdit.id }}</h5>
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
                  <option v-for="c in customers" :key="c.id" :value="c.id">
                    {{ c.name }}
                  </option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label">Статус</label>
                <select v-model="orderToEdit.status" class="form-select">
                  <option value="NEW">NEW</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="DONE">DONE</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>
            </div>

            <hr class="my-3" />

            <h6 class="mb-2">Состав заказа</h6>

            <div v-if="modalItemsLoading" class="text-muted small mb-2">
              Загрузка позиций...
            </div>

            <div class="table-responsive mb-2">
              <table class="table table-sm align-middle mb-0">
                <thead>
                  <tr>
                    <th>Позиция меню</th>
                    <th style="width: 110px">Кол-во</th>
                    <th style="width: 160px">Действия</th>
                  </tr>
                </thead>
                <tbody>
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
                    <td colspan="3" class="text-center text-muted small">
                      Позиции ещё не добавлены
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div
              class="d-flex flex-column flex-md-row gap-2 align-items-md-center mb-3"
            >
              <select
                v-model="newItemForOrder.menu_id"
                class="form-select form-select-sm"
              >
                <option value="">Позиция меню...</option>
                <option v-for="m in menu" :key="m.id" :value="m.id">
                  {{ menuTitle(m) }}
                </option>
              </select>
              <input
                v-model.number="newItemForOrder.qty"
                type="number"
                min="1"
                class="form-control form-control-sm"
                style="max-width: 120px"
              />
              <button
                class="btn btn-sm btn-primary"
                type="button"
                @click="onOrderItemAdd"
              >
                Добавить позицию
              </button>
            </div>

            <div class="text-end text-muted small">
              Сумма заказа сейчас:
              <strong>{{ formatPrice(currentOrderTotal) }}</strong>
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
