<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import Cookies from "js-cookie"
import "@/styles/admin.css"

axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")

const orders = ref([])
const customers = ref([])
const loading = ref(false)
const error = ref("")

const orderToAdd = ref({ customer_id:null, status:"new" })
const orderToEdit = ref({ id:null, customer_id:null, status:"" })

async function fetchCustomers(){ const {data}=await axios.get("/api/customers/"); customers.value=data }
async function fetchOrders(){ const {data}=await axios.get("/api/orders/"); orders.value=data }

async function onOrderAdd(){
  if(!orderToAdd.value.customer_id) return
  await axios.post("/api/orders/", {
    customer_id: Number(orderToAdd.value.customer_id),
    status: orderToAdd.value.status
  })
  orderToAdd.value = { customer_id:null, status:"new" }
  await fetchOrders()
}

function onOrderEditClick(o){
  orderToEdit.value = {
    id:o.id,
    customer_id: o.customer?.id ?? o.customer,
    status:o.status
  }
  new bootstrap.Modal(document.getElementById("editOrderModal")).show()
}

async function onOrderUpdate(){
  if(!orderToEdit.value.customer_id) return
  await axios.put(`/api/orders/${orderToEdit.value.id}/`, {
    customer_id:Number(orderToEdit.value.customer_id),
    status:orderToEdit.value.status
  })
  await fetchOrders()
}

async function onRemoveClick(o){
  if(!confirm(`Удалить заказ #${o.id}?`)) return
  await axios.delete(`/api/orders/${o.id}/`)
  await fetchOrders()
}

onBeforeMount(async ()=>{
  loading.value = true; error.value = ""
  try{ await Promise.all([fetchCustomers(), fetchOrders()]) }
  catch(e){ error.value = String(e) }
  finally{ loading.value = false }
})
</script>

<template>
  <div class="page">
    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="section">
      <h3>Добавить заказ</h3>
      <form class="inline-form" @submit.prevent="onOrderAdd">
        <div class="form-floating">
          <select class="form-select" v-model="orderToAdd.customer_id" required>
            <option value="" disabled>Клиент…</option>
            <option v-for="c in customers" :key="c.id" :value="c.id">
              {{ c.name ?? c.fio ?? c.username ?? c.email ?? ('Клиент #'+c.id) }}
            </option>
          </select>
          <label>Клиент</label>
        </div>
        <div class="form-floating">
          <input class="form-control" v-model="orderToAdd.status" placeholder="Статус" />
          <label>Статус</label>
        </div>
        <button class="btn btn-primary">Добавить</button>
      </form>
    </div>

    <div class="section">
      <div class="table-wrap">
        <table class="table table-bordered align-middle">
          <thead>
            <tr>
              <th style="width:90px">ID</th><th>Клиент</th><th style="width:180px">Статус</th>
              <th style="width:220px">Создан</th><th style="width:160px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ o.customer?.name ?? o.customer?.fio ?? ('#' + o.customer?.id) }}</td>
              <td>{{ o.status }}</td>
              <td>{{ new Date(o.created_at).toLocaleString() }}</td>
              <td>
                <button class="btn btn-sm btn-outline-success me-2" @click="onOrderEditClick(o)" data-bs-toggle="modal" data-bs-target="#editOrderModal">✏️</button>
                <button class="btn btn-sm btn-outline-danger" @click="onRemoveClick(o)">🗑️</button>
              </td>
            </tr>
            <tr v-if="!loading && !orders.length"><td colspan="5" class="text-center text-muted">Пусто</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="editOrderModal" tabindex="-1">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Редактировать заказ</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="form-floating mb-3">
            <select class="form-select" v-model="orderToEdit.customer_id" required>
              <option value="" disabled>Клиент…</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">
                {{ c.name ?? c.fio ?? c.username ?? c.email ?? ('Клиент #'+c.id) }}
              </option>
            </select>
            <label>Клиент</label>
          </div>
          <div class="form-floating">
            <input class="form-control" v-model="orderToEdit.status" placeholder="Статус" />
            <label>Статус</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
          <button class="btn btn-primary" @click="onOrderUpdate" data-bs-dismiss="modal">Сохранить</button>
        </div>
      </div></div>
    </div>
  </div>
</template>
