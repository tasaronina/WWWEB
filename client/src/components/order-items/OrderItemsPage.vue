<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import "@/styles/admin.css"

const orders = ref([])
const menu = ref([])
const orderItems = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

const newOrderId = ref(null)
const newMenuId = ref(null)
const newQty = ref(1)

function formatNumber(value) {
  if (value === null || value === undefined) return "-"
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toFixed(2)
}

function menuTitle(m) {
  return m?.name ?? m?.title ?? (m?.id ? `Позиция #${m.id}` : "-")
}

async function fetchOrders() {
  const { data } = await axios.get("/api/orders/")
  orders.value = data
}

async function fetchMenu() {
  const { data } = await axios.get("/api/menu/")
  menu.value = data
}

async function fetchOrderItems() {
  const { data } = await axios.get("/api/order-items/")
  orderItems.value = data.map((it) => ({
    ...it,
    _editOrderId: it.order?.id ?? it.order ?? null,
    _editMenuId: it.menu?.id ?? it.menu ?? null,
  }))
}

async function fetchStats() {
  const { data } = await axios.get("/api/order-items/stats/")
  stats.value = data
}

async function createItem() {
  if (!newOrderId.value || !newMenuId.value || !newQty.value) return
  await axios.post("/api/order-items/", {
    order_id: Number(newOrderId.value),
    menu_id: Number(newMenuId.value),
    qty: Number(newQty.value),
  })
  newOrderId.value = null
  newMenuId.value = null
  newQty.value = 1
  await Promise.all([fetchOrderItems(), fetchStats()])
}

async function updateItem(it) {
  await axios.put(`/api/order-items/${it.id}/`, {
    qty: Number(it.qty),
    order_id: Number(it._editOrderId),
    menu_id: Number(it._editMenuId),
  })
  await Promise.all([fetchOrderItems(), fetchStats()])
}

async function removeItem(id) {
  if (!confirm("Удалить позицию заказа?")) return
  await axios.delete(`/api/order-items/${id}/`)
  await Promise.all([fetchOrderItems(), fetchStats()])
}

onBeforeMount(async () => {
  loading.value = true
  error.value = ""
  try {
    await Promise.all([
      fetchOrders(),
      fetchMenu(),
      fetchOrderItems(),
      fetchStats(),
    ])
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container my-4 page">
    <h1 class="mb-3">Добавить позицию заказа</h1>

    <div v-if="error" class="alert alert-danger alert-inline">
      Ошибка: {{ error }}
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-4">
            <label class="form-label">Заказ</label>
            <select v-model="newOrderId" class="form-select">
              <option :value="null" disabled>Заказ...</option>
              <option v-for="o in orders" :key="o.id" :value="o.id">
                Заказ #{{ o.id }}
              </option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Позиция меню</label>
            <select v-model="newMenuId" class="form-select">
              <option :value="null" disabled>Позиция меню...</option>
              <option v-for="m in menu" :key="m.id" :value="m.id">
                {{ menuTitle(m) }}
              </option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label">Кол-во</label>
            <input
              v-model.number="newQty"
              type="number"
              min="1"
              class="form-control"
            />
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" type="button" @click="createItem">
              Создать
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего позиций: <strong>{{ stats.count }}</strong></span>
        <span
          >Среднее кол-во в строке:
          <strong>{{ formatNumber(stats.avg) }}</strong></span
        >
        <span>Макс. кол-во: <strong>{{ stats.max }}</strong></span>
        <span>Мин. кол-во: <strong>{{ stats.min }}</strong></span>
      </div>
    </div>

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table table-bordered align-middle">
          <thead>
            <tr>
              <th style="width: 80px">ID</th>
              <th style="width: 120px">Заказ</th>
              <th>Позиция меню</th>
              <th style="width: 120px">Кол-во</th>
              <th style="width: 160px">Сменить заказ (ID)</th>
              <th style="width: 220px">Сменить позицию (ID)</th>
              <th style="width: 160px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in orderItems" :key="it.id">
              <td>{{ it.id }}</td>
              <td>#{{ it.order?.id ?? it.order }}</td>
              <td>
                {{ menuTitle(it.menu) }}
              </td>
              <td>
                <input
                  v-model.number="it.qty"
                  type="number"
                  min="1"
                  class="form-control form-control-sm"
                />
              </td>
              <td>
                <input
                  v-model.number="it._editOrderId"
                  type="number"
                  min="1"
                  class="form-control form-control-sm"
                  placeholder="ID заказа"
                />
              </td>
              <td>
                <input
                  v-model.number="it._editMenuId"
                  type="number"
                  min="1"
                  class="form-control form-control-sm"
                  placeholder="ID меню"
                />
              </td>
              <td>
                <button
                  class="btn btn-sm btn-success me-2"
                  type="button"
                  @click="updateItem(it)"
                >
                  Сохранить
                </button>
                <button
                  class="btn btn-sm btn-danger"
                  type="button"
                  @click="removeItem(it.id)"
                >
                  Удалить
                </button>
              </td>
            </tr>
            <tr v-if="!loading && !orderItems.length">
              <td colspan="7" class="text-center text-muted">Пусто</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
