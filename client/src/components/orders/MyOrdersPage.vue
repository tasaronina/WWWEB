<script setup>
import { ref, reactive, onMounted } from "vue"
import api, { ensureCsrf } from "@/api"
import "@/styles/admin.css"

const orders = ref([])
const itemsByOrder = ref({})
const loading = ref(false)

const editOpen = ref(false)
const editing = reactive({ id: null, status: "NEW", rows: [] })
const saving = ref(false)
const errorMsg = ref("")

function price(v){ return Number(v||0).toFixed(2) }

function normalizeOrderId(raw){
  if (raw && typeof raw === "object") return raw.id ?? null
  return raw ?? null
}

async function loadOrdersAndItems(){
  loading.value = true
  try{
    const [{ data: ordersResp }, { data: itemsResp }] = await Promise.all([
      api.get("/api/orders/"),
      api.get("/api/order-items/"),
    ])
    orders.value = Array.isArray(ordersResp) ? ordersResp : []
    const grouped = {}
    const list = Array.isArray(itemsResp) ? itemsResp : []
    for (const it of list){
      const oid = normalizeOrderId(it.order) ?? it.order_id ?? it.orderId
      if(!oid) continue
      ;(grouped[oid] ||= []).push(it)
    }
    itemsByOrder.value = grouped
  } finally { loading.value = false }
}

function total(orderId){
  const arr = itemsByOrder.value[orderId] || []
  return arr.reduce((s, it) => s + Number(it?.menu?.price ?? it?.price ?? 0) * Number(it?.qty ?? 0), 0)
}

function openEdit(order){
  const rows = (itemsByOrder.value[order.id] || []).map(it => ({
    id: it.id,
    name: it.menu?.name || it.menu?.title || `#${it.menu_id}`,
    price: Number(it.menu?.price ?? it.price ?? 0),
    qty: Number(it.qty ?? 0),
  }))
  editing.id = order.id
  editing.status = order.status || "NEW"
  editing.rows = rows
  errorMsg.value = ""
  editOpen.value = true
}

async function saveEdit(){
  if (!editing.id) return
  saving.value = true
  errorMsg.value = ""
  try{
    await ensureCsrf()
    await api.patch(`/api/orders/${editing.id}/`, { status: editing.status })
    const original = itemsByOrder.value[editing.id] || []
    const byId = Object.fromEntries(original.map(r => [r.id, r]))
    for (const row of editing.rows){
      if (!byId[row.id]) continue
      if (row.qty <= 0){
        await api.delete(`/api/order-items/${row.id}/`)
      } else if (row.qty !== Number(byId[row.id]?.qty)){
        await api.patch(`/api/order-items/${row.id}/`, { qty: row.qty })
      }
    }
    await loadOrdersAndItems()
    editOpen.value = false
  } catch(e){
    errorMsg.value = "Не удалось сохранить изменения."
  } finally {
    saving.value = false
  }
}

async function deleteOrder(orderId){
  if (!confirm(`Удалить заказ #${orderId}?`)) return
  await ensureCsrf()
  await api.delete(`/api/orders/${orderId}/`)
  await loadOrdersAndItems()
}

onMounted(loadOrdersAndItems)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex align-items-center mb-3">
      <h1 class="mb-0">Мои заказы</h1>
      <button class="btn btn-outline-secondary btn-sm ms-3" @click="loadOrdersAndItems" :disabled="loading">Обновить</button>
    </div>

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle">
          <thead>
            <tr>
              <th style="width:100px">ID</th>
              <th>Клиент</th>
              <th>Состав</th>
              <th style="width:140px">Сумма</th>
              <th style="width:160px">Статус</th>
              <th style="width:220px">Создан</th>
              <th style="width:180px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="7">Загрузка...</td></tr>

            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ o.customer?.name || o.user || "я" }}</td>
              <td>
                <ul class="small mb-0" v-if="(itemsByOrder[o.id] || []).length">
                  <li v-for="it in itemsByOrder[o.id]" :key="it.id">
                    {{ it.menu?.name || it.menu?.title || ("Позиция #" + (it.menu_id || "")) }} × {{ it.qty }}
                  </li>
                </ul>
                <span v-else class="text-muted">Состав заказа пуст</span>
              </td>
              <td><strong>{{ price(total(o.id)) }}</strong></td>
              <td><span class="badge bg-secondary">{{ o.status }}</span></td>
              <td>{{ o.created_at ? new Date(o.created_at).toLocaleString() : "—" }}</td>
              <td>
                <button class="btn btn-sm btn-primary me-2" @click="openEdit(o)">Редактировать</button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteOrder(o.id)">Удалить</button>
              </td>
            </tr>

            <tr v-if="!loading && !orders.length">
              <td colspan="7" class="text-muted text-center">Заказов пока нет</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="modal fade show" tabindex="-1" style="display:block" v-if="editOpen" @click.self="editOpen=false">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Заказ #{{ editing.id }}</h5>
            <button type="button" class="btn-close" @click="editOpen=false"></button>
          </div>
          <div class="modal-body">
            <div class="row g-3 mb-3">
              <div class="col-sm-6">
                <label class="form-label">Статус</label>
                <select v-model="editing.status" class="form-select">
                  <option value="NEW">NEW</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="DONE">DONE</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>
            </div>

            <div class="table-responsive">
              <table class="table align-middle">
                <thead>
                  <tr>
                    <th style="width:80px">ID</th>
                    <th>Позиция</th>
                    <th style="width:120px">Цена</th>
                    <th style="width:120px">Кол-во</th>
                    <th style="width:120px">Сумма</th>
                    <th style="width:100px">Удалить</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in editing.rows" :key="row.id">
                    <td>{{ row.id }}</td>
                    <td>{{ row.name }}</td>
                    <td>{{ price(row.price) }}</td>
                    <td><input type="number" min="0" class="form-control form-control-sm" v-model.number="row.qty" /></td>
                    <td>{{ price(row.price * row.qty) }}</td>
                    <td><button class="btn btn-sm btn-outline-danger" @click="row.qty = 0">Удалить</button></td>
                  </tr>
                  <tr v-if="!editing.rows.length">
                    <td colspan="6" class="text-center text-muted">Пусто</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="errorMsg" class="alert alert-danger mt-2">{{ errorMsg }}</div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="editOpen=false">Закрыть</button>
            <button class="btn btn-primary" :disabled="saving" @click="saveEdit">Сохранить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
