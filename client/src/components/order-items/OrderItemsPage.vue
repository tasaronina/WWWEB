<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import Cookies from "js-cookie"
import "@/styles/admin.css"

axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")

const orders = ref([])
const menu = ref([])
const orderItems = ref([])
const loading = ref(false)
const error = ref("")

const newOrderId = ref(null)
const newMenuId = ref(null)
const newQty = ref(1)

function menuTitle(m){ return m.name ?? m.title ?? `Позиция #${m.id}` }

async function fetchOrders(){ const {data}=await axios.get("/api/orders/"); orders.value=data }
async function fetchMenu(){ const {data}=await axios.get("/api/menu/"); menu.value=data }
async function fetchOrderItems(){ const {data}=await axios.get("/api/order-items/"); orderItems.value=data }

async function createItem(){
  if(!newOrderId.value || !newMenuId.value || !newQty.value) return
  await axios.post("/api/order-items/", {
    order_id:Number(newOrderId.value),
    menu_id:Number(newMenuId.value),
    qty:Number(newQty.value)
  })
  newOrderId.value = null; newMenuId.value = null; newQty.value = 1
  await fetchOrderItems()
}

async function updateItem(it){
  await axios.patch(`/api/order-items/${it.id}/`, {
    qty:Number(it.qty),
    ...(it._editOrderId ? { order_id:Number(it._editOrderId) } : {}),
    ...(it._editMenuId ? { menu_id:Number(it._editMenuId) } : {})
  })
  await fetchOrderItems()
}

async function removeItem(id){
  if(!confirm("Удалить позицию заказа?")) return
  await axios.delete(`/api/order-items/${id}/`)
  await fetchOrderItems()
}

onBeforeMount(async ()=>{
  loading.value = true; error.value = ""
  try{ await Promise.all([fetchOrders(), fetchMenu(), fetchOrderItems()]) }
  catch(e){ error.value = String(e) }
  finally{ loading.value = false }
})
</script>

<template>
  <div class="page">
    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="section">
      <h3>Добавить позицию заказа</h3>
      <div class="inline-form">
        <select class="form-select" v-model="newOrderId">
          <option :value="null" disabled>Заказ…</option>
          <option v-for="o in orders" :key="o.id" :value="o.id">Заказ #{{ o.id }}</option>
        </select>
        <select class="form-select" v-model="newMenuId">
          <option :value="null" disabled>Позиция меню…</option>
          <option v-for="m in menu" :key="m.id" :value="m.id">{{ menuTitle(m) }}</option>
        </select>
        <input type="number" class="form-control" v-model.number="newQty" min="1" style="width:110px" placeholder="Кол-во" />
        <button class="btn btn-primary" @click="createItem">Создать</button>
      </div>
    </div>

    <div class="section">
      <div class="table-wrap">
        <table class="table table-bordered align-middle">
          <thead>
            <tr>
              <th style="width:80px">ID</th><th style="width:120px">Заказ</th>
              <th>Позиция меню</th><th style="width:120px">Кол-во</th>
              <th style="width:160px">Сменить заказ</th><th style="width:220px">Сменить позицию</th>
              <th style="width:160px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in orderItems" :key="it.id">
              <td>{{ it.id }}</td>
              <td>#{{ it.order?.id ?? it.order }}</td>
              <td>{{ it.menu?.name ?? it.menu?.title ?? ('#' + (it.menu?.id ?? it.menu)) }}</td>
              <td><input type="number" class="form-control form-control-sm" v-model.number="it.qty" min="1" /></td>
              <td>
                <select class="form-select form-select-sm" v-model="it._editOrderId">
                  <option :value="null">—</option>
                  <option v-for="o in orders" :key="o.id" :value="o.id">Заказ #{{ o.id }}</option>
                </select>
              </td>
              <td>
                <select class="form-select form-select-sm" v-model="it._editMenuId">
                  <option :value="null">—</option>
                  <option v-for="m in menu" :key="m.id" :value="m.id">{{ menuTitle(m) }}</option>
                </select>
              </td>
              <td>
                <button class="btn btn-sm btn-success me-2" @click="updateItem(it)">Сохранить</button>
                <button class="btn btn-sm btn-danger" @click="removeItem(it.id)">Удалить</button>
              </td>
            </tr>
            <tr v-if="!loading && !orderItems.length"><td colspan="7" class="text-center text-muted">Пусто</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
