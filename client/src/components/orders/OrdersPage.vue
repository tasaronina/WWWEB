<template>
  <div class="container my-4">
    <h1 class="mb-3">Заказы (админ)</h1>

    <div v-if="error" class="alert alert-danger mb-3">Ошибка: {{ error }}</div>


    <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
      <button class="btn btn-primary" @click="openCreateModal">Создать заказ</button>

      <div class="ms-auto small text-muted d-flex flex-wrap gap-3">
        <span>Всего заказов: <strong>{{ stats.total }}</strong></span>
        <span>Средний ID: <strong>{{ stats.avgId }}</strong></span>
        <span>Макс ID: <strong>{{ stats.maxId }}</strong></span>
        <span>Мин ID: <strong>{{ stats.minId }}</strong></span>
      </div>
    </div>

    <!-- Фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-center">
          <div class="col-md-3">
            <input v-model="filters.id" type="text" class="form-control" placeholder="Фильтр по ID" />
          </div>
          <div class="col-md-4">
            <input v-model="filters.customer" type="text" class="form-control" placeholder="Фильтр по клиенту" />
          </div>
          <div class="col-md-3">
            <select v-model="filters.status" class="form-select">
              <option value="">Все статусы</option>
              <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-outline-secondary" @click="resetFilters">Сброс</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Таблица заказов -->
    <div class="card">
      <div class="table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th style="width:90px">ID</th>
              <th>Клиент</th>
              <th style="width:140px">Сумма</th>
              <th style="width:140px">Статус</th>
              <th style="width:220px">Создан</th>
              <th style="width:200px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="text-center text-muted py-4">Загрузка…</td>
            </tr>

            <tr v-for="o in filteredOrders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ displayCustomer(o.customer) }}</td>
              <td>{{ formatMoney(o.total) }}</td>
              <td><span class="badge bg-secondary">{{ o.status }}</span></td>
              <td>{{ formatDate(o.created || o.created_at) }}</td>
              <td>
                <div class="btn-group">
                  <button class="btn btn-outline-primary btn-sm" @click="openEditModal(o)">Редактировать</button>
                  <button class="btn btn-outline-danger btn-sm" @click="removeOrder(o)">Удалить</button>
                </div>
              </td>
            </tr>

            <tr v-if="!loading && !filteredOrders.length">
              <td colspan="6" class="text-center text-muted py-4">Заказов пока нет</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модалка: создание заказа -->
    <div class="modal fade" id="createOrderModal" tabindex="-1" ref="createModalRef" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <form @submit.prevent="saveCreateDraft">
            <div class="modal-header">
              <h5 class="modal-title">Создать заказ</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
            </div>

            <div class="modal-body">
              <div class="row g-3 mb-3">
                <div class="col-md-6">
                  <label class="form-label">Клиент</label>
                  <select v-model="createDraft.customer_id" class="form-select" required>
                    <option value="">Выберите клиента…</option>
                    <option v-for="c in customers" :key="c.id" :value="c.id">
                      {{ c.name || c.title || ('Клиент #' + c.id) }}
                    </option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Статус</label>
                  <select v-model="createDraft.status" class="form-select" required>
                    <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
              </div>

              <hr class="my-2" />

              <h6 class="mb-2">Состав заказа</h6>

              <div class="row g-2 align-items-end mb-2">
                <div class="col-md-7">
                  <label class="form-label">Добавить позицию</label>
                  <input
                    v-model="createAdd.query"
                    list="menu-datalist-create"
                    class="form-control"
                    placeholder="Вводите название или ID…"
                    @change="syncCreateSelectedFromQuery"
                  />
                  <datalist id="menu-datalist-create">
                    <option v-for="m in menu" :key="m.id" :value="m.id + ' — ' + menuTitle(m)"></option>
                  </datalist>
                </div>
                <div class="col-md-3">
                  <label class="form-label">Кол-во</label>
                  <input v-model.number="createAdd.qty" type="number" min="1" class="form-control" />
                </div>
                <div class="col-md-2 d-grid">
                  <button type="button" class="btn btn-outline-primary" @click="addToCreateDraft">+</button>
                </div>
              </div>

              <div class="table-responsive">
                <table class="table align-middle">
                  <thead>
                    <tr>
                      <th style="width:90px">ID</th>
                      <th>Позиция</th>
                      <th style="width:140px">Цена</th>
                      <th style="width:120px">Кол-во</th>
                      <th style="width:140px">Сумма</th>
                      <th style="width:120px"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(it, idx) in createDraft.items" :key="'draft-'+idx">
                      <td>{{ it.menu_id }}</td>
                      <td>{{ menuTitleById(it.menu_id) }}</td>
                      <td>{{ formatMoney(menuPriceById(it.menu_id)) }}</td>
                      <td><input v-model.number="it.qty" type="number" min="1" class="form-control form-control-sm"/></td>
                      <td>{{ formatMoney(menuPriceById(it.menu_id) * it.qty) }}</td>
                      <td>
                        <button class="btn btn-sm btn-outline-danger" type="button" @click="createDraft.items.splice(idx,1)">Удалить</button>
                      </td>
                    </tr>
                    <tr v-if="!createDraft.items.length">
                      <td colspan="6" class="text-center text-muted py-3">Позиции не добавлены</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Закрыть</button>
              <button class="btn btn-primary" type="submit" :disabled="saving">Создать</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Модалка: редактирование заказа -->
    <div class="modal fade" id="editOrderModal" tabindex="-1" ref="editModalRef" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content" v-if="edit.order">
          <form @submit.prevent="saveEditOrder">
            <div class="modal-header">
              <h5 class="modal-title">Заказ #{{ edit.order.id }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
            </div>

            <div class="modal-body">
              <div class="row g-3 mb-3">
                <div class="col-md-6">
                  <label class="form-label">Статус</label>
                  <select v-model="edit.order.status" class="form-select">
                    <option v-for="s in STATUSES" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Сумма (пересчёт по позициям)</label>
                  <input class="form-control" :value="formatMoney(sumEditItems)" disabled />
                </div>
              </div>

              <h6 class="mb-2">Добавить позицию</h6>
              <div class="row g-2 align-items-end mb-2">
                <div class="col-md-7">
                  <input
                    v-model="edit.add.query"
                    list="menu-datalist-edit"
                    class="form-control"
                    placeholder="Вводите название или ID…"
                    @change="syncEditSelectedFromQuery"
                  />
                  <datalist id="menu-datalist-edit">
                    <option v-for="m in menu" :key="m.id" :value="m.id + ' — ' + menuTitle(m)"></option>
                  </datalist>
                </div>
                <div class="col-md-3">
                  <input v-model.number="edit.add.qty" type="number" min="1" class="form-control" />
                </div>
                <div class="col-md-2 d-grid">
                  <button type="button" class="btn btn-outline-primary" @click="addItemToOrder">+</button>
                </div>
              </div>

              <div class="table-responsive">
                <table class="table align-middle">
                  <thead>
                    <tr>
                      <th style="width:90px">ID</th>
                      <th>Позиция</th>
                      <th style="width:140px">Цена</th>
                      <th style="width:120px">Кол-во</th>
                      <th style="width:140px">Сумма</th>
                      <th style="width:120px"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="it in edit.items" :key="it.id">
                      <td>{{ it.id }}</td>
                      <td>{{ menuTitleById(it.menu_id) }}</td>
                      <td>{{ formatMoney(menuPriceById(it.menu_id)) }}</td>
                      <td>
                        <input v-model.number="it.qty" type="number" min="1"
                               class="form-control form-control-sm"
                               @change="updateItemQty(it)" />
                      </td>
                      <td>{{ formatMoney(menuPriceById(it.menu_id) * it.qty) }}</td>
                      <td>
                        <button type="button" class="btn btn-sm btn-outline-danger" @click="deleteItem(it)">Удалить</button>
                      </td>
                    </tr>
                    <tr v-if="!edit.items.length">
                      <td colspan="6" class="text-center text-muted py-3">Состав заказа пуст</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Закрыть</button>
              <button class="btn btn-primary" type="submit" :disabled="saving">Сохранить</button>
            </div>
          </form>
        </div>

        <div class="modal-content" v-else>
          <div class="modal-body py-5 text-center text-muted">Загрузка…</div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import axios from "axios"
import { ref, computed, onMounted } from "vue"
import "bootstrap/dist/js/bootstrap.bundle.min.js"
import "@/styles/admin.css"

axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

axios.defaults.withCredentials = true

const STATUSES = ["NEW", "IN_PROGRESS", "DONE", "CANCELLED"]


const loading = ref(false)
const saving  = ref(false)
const error   = ref("")

const orders = ref([])
const customers = ref([])
const menu = ref([])

const filters = ref({ id:"", customer:"", status:"" })
const stats = ref({ total: 0, avgId: "—", maxId: "—", minId: "—" })


const createModalRef = ref(null)
let createModal
const createDraft = ref({ customer_id: "", status: "NEW", items: [] })
const createAdd = ref({ query: "", qty: 1 })


const editModalRef = ref(null)
let editModal
const edit = ref({
  order: null,
  items: [],
  add: { query: "", qty: 1 },
})


function formatMoney(v){
  const n = Number(v || 0)
  return n.toFixed(2)
}
function formatDate(v){
  if(!v) return "—"
  try {
    const d = new Date(v)
    if (isNaN(d.getTime())) return String(v)
    return d.toISOString()
  } catch {
    return String(v)
  }
}
function displayCustomer(c){
  if(typeof c === "string") return c
  if(c && (c.name || c.title)) return c.name || c.title
  if(c && c.id) return "Клиент #" + c.id
  return "—"
}
function menuTitle(m){
  return m?.name ?? m?.title ?? ("Позиция #" + m?.id)
}
function menuTitleById(id){
  const m = menu.value.find(x => x.id === id)
  return menuTitle(m)
}
function menuPriceById(id){
  const m = menu.value.find(x => x.id === id)
  return Number(m?.price ?? 0)
}


function extractId(val){
  if (val == null) return null
  if (typeof val === "number") return Number.isFinite(val) ? val : null
  if (typeof val === "object") {
    if ("id" in val) return extractId(val.id)
    return null
  }
 
  const m = String(val).match(/\d+/)
  return m ? Number(m[0]) : null
}
function toItemShape(x){
  const ord = x.order_id ?? extractId(x.order)
  const men = x.menu_id  ?? extractId(x.menu)

  return {
    id: extractId(x.id),
    order_id: extractId(ord),
    menu_id: extractId(men),
    qty: Number(x.qty ?? 1),
  }
}


async function fetchOrders(){
  const { data } = await axios.get("/api/orders/")
  orders.value = (data || []).map(o => ({
    ...o,
    id: extractId(o.id),
    total: Number(o.total ?? o.sum ?? 0),
    status: o.status ?? "NEW",
    created: o.created ?? o.created_at ?? null,
  }))
  if(orders.value.length){
    const ids = orders.value.map(o => Number(o.id)).filter(n => !isNaN(n))
    const cnt = ids.length
    stats.value.total = cnt
    stats.value.avgId = (ids.reduce((a,b)=>a+b,0)/cnt).toFixed(2)
    stats.value.maxId = Math.max(...ids)
    stats.value.minId = Math.min(...ids)
  }else{
    stats.value = { total: 0, avgId: "—", maxId: "—", minId: "—" }
  }
}

async function fetchCustomers(){
  try{
    const { data } = await axios.get("/api/customers/")
    customers.value = data || []
  }catch{ customers.value = [] }
}

async function fetchMenu(){
  const { data } = await axios.get("/api/menu/")
  menu.value = (data || []).map(m => ({
    id: extractId(m.id),
    name: m.name ?? m.title ?? "",
    price: Number(m.price ?? 0)
  }))
}


async function fetchOrderItems(orderId){
  try{
    const { data } = await axios.get(`/api/order-items/`, { params: { order_id: orderId } })
    return (data || []).map(toItemShape).filter(i => i.order_id === extractId(orderId))
  }catch{
    return []
  }
}


const filteredOrders = computed(()=>{
  const id = filters.value.id.trim()
  const cust = filters.value.customer.trim().toLowerCase()
  const st = filters.value.status
  return orders.value.filter(o=>{
    if(id && !String(o.id).includes(id)) return false
    const cName = (displayCustomer(o.customer) || "").toLowerCase()
    if(cust && !cName.includes(cust)) return false
    if(st && o.status !== st) return false
    return true
  })
})
function resetFilters(){ filters.value = { id:"", customer:"", status:"" } }


function openCreateModal(){
  createDraft.value = { customer_id: "", status: "NEW", items: [] }
  createAdd.value = { query: "", qty: 1 }
  createModal ??= window.bootstrap.Modal.getOrCreateInstance(createModalRef.value)
  createModal.show()
}

function syncCreateSelectedFromQuery(){
  const id = Number(String(createAdd.value.query).split("—")[0].trim())
  if(!isNaN(id)) createAdd.value.query = String(id)
}

function addToCreateDraft(){
  const id = Number(createAdd.value.query)
  if(isNaN(id) || !menu.value.some(m=>m.id===id)) return
  const qty = Number(createAdd.value.qty || 1)
  const idx = createDraft.value.items.findIndex(i => i.menu_id === id)
  if(idx>=0) createDraft.value.items[idx].qty += qty
  else createDraft.value.items.push({ menu_id: id, qty })
  createAdd.value = { query: "", qty: 1 }
}

async function saveCreateDraft(){
  if(!createDraft.value.customer_id) return
  saving.value = true
  try{
    const { data: created } = await axios.post("/api/orders/", {
      customer_id: Number(createDraft.value.customer_id),
      status: createDraft.value.status
    })
    for(const it of createDraft.value.items){
      await axios.post("/api/order-items/", {
        order_id: extractId(created.id ?? created),
        menu_id: it.menu_id,
        qty: it.qty
      })
    }
    await fetchOrders()
    createModal?.hide()
  }catch(e){
    console.error(e)
  }finally{
    saving.value = false
  }
}


function openEditModal(order){
  edit.value.order = { id: extractId(order.id), status: order.status }
  edit.value.items = []
  edit.value.add = { query: "", qty: 1 }
  editModal ??= window.bootstrap.Modal.getOrCreateInstance(editModalRef.value)
  editModal.show()
  fetchOrderItems(order.id).then(list=>{
    edit.value.items = list
  }).catch(()=>{ edit.value.items = [] })
}

function syncEditSelectedFromQuery(){
  const id = Number(String(edit.value.add.query).split("—")[0].trim())
  if(!isNaN(id)) edit.value.add.query = String(id)
}

async function addItemToOrder(){
  const orderId = edit.value.order?.id
  if(!orderId) return
  const id = Number(edit.value.add.query)
  if(isNaN(id) || !menu.value.some(m=>m.id===id)) return
  const qty = Number(edit.value.add.qty || 1)
  const { data } = await axios.post("/api/order-items/", { order_id: orderId, menu_id: id, qty })
  edit.value.items.push(toItemShape(data))
  edit.value.add = { query: "", qty: 1 }
}

async function updateItemQty(it){
  await axios.patch(`/api/order-items/${it.id}/`, { qty: Number(it.qty||1) })
}

async function deleteItem(it){
  if(!confirm("Удалить позицию?")) return
  await axios.delete(`/api/order-items/${it.id}/`)
  edit.value.items = edit.value.items.filter(x => x.id !== it.id)
}

const sumEditItems = computed(()=>{
  return edit.value.items.reduce((s, it) => s + menuPriceById(it.menu_id) * it.qty, 0)
})

async function saveEditOrder(){
  if(!edit.value.order) return
  saving.value = true
  try{
    await axios.patch(`/api/orders/${edit.value.order.id}/`, { status: edit.value.order.status })
    await fetchOrders()
    editModal?.hide()
  }catch(e){
    console.error(e)
  }finally{
    saving.value = false
  }
}


async function removeOrder(o){
  if(!confirm(`Удалить заказ #${o.id}?`)) return
  await axios.delete(`/api/orders/${o.id}/`)
  await fetchOrders()
}


onMounted(async ()=>{
  loading.value = true; error.value=""
  try{
    await Promise.all([fetchOrders(), fetchCustomers(), fetchMenu()])
  }catch(e){
    error.value = "Не удалось загрузить данные"
  }finally{
    loading.value = false
  }
})
</script>

<style scoped>
.badge { font-weight: 600; }
</style>
