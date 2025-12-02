<script setup>
import axios from "axios"
import { ref, onMounted, computed } from "vue"
import { downloadExport, ensureCsrf } from "@/api"
import "@/styles/admin.css"

axios.defaults.withCredentials = true

const canAdmin = ref(false)
async function detectAdmin(){
  try{
    const { data } = await axios.get("/api/auth/me/")
    // поддерживаем оба формата: плоский и user-вложенный
    const u = data?.user || data || {}
    canAdmin.value = !!(u.is_superuser || u.is_staff)
  }catch{
    canAdmin.value = false
  }
  return canAdmin.value
}

const orders  = ref([])
const menu    = ref([])
const items   = ref([])
const stats   = ref(null)
const loading = ref(false)
const error   = ref("")

const form = ref({ order_id: "", menu_id: "", qty: 1 })

const filters = ref({ id:"", order:"", menuText:"", qty:"" })

function menuTitle(m){
  if(!m) return ""
  if(typeof m === "object") return m.name ?? m.title ?? `Позиция #${m.id}`
  return `Позиция #${m}`
}

async function fetchOrders(){
  const { data } = await axios.get("/api/orders/")
  orders.value = Array.isArray(data) ? data : (data?.results ?? [])
}
async function fetchMenu(){
  const { data } = await axios.get("/api/menu/")
  menu.value = Array.isArray(data) ? data : (data?.results ?? [])
}
async function fetchItems(){
  const { data } = await axios.get("/api/order-items/")
  items.value = Array.isArray(data) ? data : (data?.results ?? [])
}
async function fetchStats(){
  try{
    const { data } = await axios.get("/api/order-items/stats/")
    stats.value = data
  }catch{
    stats.value = null
  }
}

onMounted(async ()=>{
  await detectAdmin()
  loading.value = true; error.value = ""
  try{
    await Promise.all([fetchOrders(), fetchMenu(), fetchItems(), fetchStats()])
  }catch(e){
    error.value = "Не удалось загрузить позиции заказа"
  }finally{
    loading.value = false
  }
})

async function onCreate(){
  if(!canAdmin.value) return
  if(!form.value.order_id || !form.value.menu_id) return
  await ensureCsrf()
  await axios.post("/api/order-items/", {
    order_id: Number(form.value.order_id),
    menu_id:  Number(form.value.menu_id),
    qty:      Math.max(1, Number(form.value.qty) || 1)
  })
  form.value = { order_id:"", menu_id:"", qty:1 }
  await Promise.all([fetchItems(), fetchStats()])
}

async function onDelete(it){
  if(!canAdmin.value) return
  if(!confirm("Удалить позицию?")) return
  await ensureCsrf()
  await axios.delete(`/api/order-items/${it.id}/`)
  await Promise.all([fetchItems(), fetchStats()])
}

async function onSave(it){
  if(!canAdmin.value) return
  await ensureCsrf()
  await axios.patch(`/api/order-items/${it.id}/`, { qty: Math.max(1, Number(it.qty)||1) })
  await Promise.all([fetchItems(), fetchStats()])
}

function buildExportParams(){ return {} }
async function onExport(type){
  if(!canAdmin.value) return
  // ожидаем /api/order-items/export/?type=excel|word
  await downloadExport("order-items", buildExportParams(), type, "order_items")
}

const filteredList = computed(()=>{
  const id   = filters.value.id.trim()
  const ord  = filters.value.order.trim()
  const mtxt = filters.value.menuText.trim().toLowerCase()
  const q    = filters.value.qty.trim()
  return items.value.filter(it=>{
    if(id && !String(it.id).includes(id)) return false
    if(ord && !String(it.order?.id ?? it.order_id).includes(ord)) return false
    const title = (it.menu?.name ?? it.menu?.title ?? `Позиция #${it.menu?.id ?? it.menu_id}`) + ""
    if(mtxt && !title.toLowerCase().includes(mtxt)) return false
    if(q && !String(it.qty).includes(q)) return false
    return true
  })
})
function resetFilters(){ filters.value = { id:"", order:"", menuText:"", qty:"" } }
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Добавить позицию заказа</h1>

    <div v-if="error" class="alert alert-danger">Не удалось загрузить позиции заказа</div>

    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего позиций: <strong>{{ stats.count }}</strong></span>
        <span>Средний ID: <strong>{{ stats.avg?.toFixed ? stats.avg.toFixed(2) : stats.avg }}</strong></span>
        <span>Максимальный ID: <strong>{{ stats.max }}</strong></span>
        <span>Минимальный ID: <strong>{{ stats.min }}</strong></span>
      </div>
    </div>

    <!-- создание (только админ) -->
    <div class="row g-2 align-items-end mb-3" v-if="canAdmin">
      <div class="col-md-4">
        <label class="form-label">Заказ</label>
        <select v-model="form.order_id" class="form-select">
          <option value="">Выберите заказ...</option>
          <option v-for="o in orders" :key="o.id" :value="o.id">
            #{{ o.id }} — {{ o.customer?.name ?? 'без клиента' }}
          </option>
        </select>
      </div>
      <div class="col-md-5">
        <label class="form-label">Позиция меню</label>
        <select v-model="form.menu_id" class="form-select">
          <option value="">Выберите позицию меню...</option>
          <option v-for="m in menu" :key="m.id" :value="m.id">{{ menuTitle(m) }}</option>
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label">Кол-во</label>
        <input v-model.number="form.qty" type="number" min="1" class="form-control" />
      </div>
      <div class="col-md-1 d-grid">
        <button class="btn btn-primary" type="button" @click="onCreate">Создать</button>
      </div>
    </div>

    <!-- фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-3">
            <input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" />
          </div>
          <div class="col-md-3">
            <input v-model="filters.order" type="text" class="form-control" placeholder="Фильтр по заказу" />
          </div>
          <div class="col-md-4">
            <input v-model="filters.menuText" type="text" class="form-control" placeholder="Фильтр по позиции" />
          </div>
          <div class="col-md-1">
            <input v-model="filters.qty" type="text" class="form-control" placeholder="Кол-во" />
          </div>
          <div class="col-md-1 d-grid">
            <button class="btn btn-outline-secondary" @click="resetFilters">Сброс</button>
          </div>
        </div>

        <div class="mt-3 d-flex gap-2" v-if="canAdmin">
          <button class="btn btn-success" type="button" @click="onExport('excel')">Экспорт в Excel</button>
          <button class="btn btn-primary" type="button" @click="onExport('word')">Экспорт в Word</button>
        </div>
      </div>
    </div>

    <!-- таблица -->
    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th style="width: 90px;">ID</th>
              <th style="width: 100px;">Заказ</th>
              <th>Позиция меню</th>
              <th style="width: 110px;">Кол-во</th>
              <th style="width: 150px;" v-if="canAdmin">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="5" class="text-center text-muted">Загрузка...</td></tr>
            <tr v-for="it in filteredList" :key="it.id">
              <td>{{ it.id }}</td>
              <td>#{{ it.order?.id ?? it.order_id }}</td>
              <td>{{ it.menu?.name ?? it.menu?.title ?? ('Позиция #' + (it.menu?.id ?? it.menu_id)) }}</td>
              <td>
                <template v-if="canAdmin">
                  <input v-model.number="it.qty" type="number" min="1" class="form-control form-control-sm" />
                </template>
                <template v-else>{{ it.qty }}</template>
              </td>
              <td v-if="canAdmin">
                <button class="btn btn-sm btn-success me-2" @click="onSave(it)">Сохранить</button>
                <button class="btn btn-sm btn-danger" @click="onDelete(it)">Удалить</button>
              </td>
            </tr>
            <tr v-if="!loading && !filteredList.length">
              <td :colspan="canAdmin?5:4" class="text-center text-muted">Позиции заказа пока не добавлены</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
