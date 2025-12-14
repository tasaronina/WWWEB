<template>
  <v-container class="py-6">
    <div class="d-flex align-center mb-3 ga-3">
      <div class="text-h5">Мои заказы</div>
      <v-btn variant="outlined" size="small" :loading="loading" @click="loadOrdersAndItems">Обновить</v-btn>
    </div>

    <v-data-table :headers="headers" :items="orders" :loading="loading" item-key="id">
      <template #item.customer="{ item }">{{ item.customer?.name || item.user || 'я' }}</template>
      <template #item.items="{ item }">
        <div v-if="(itemsByOrder[item.id] || []).length">
          <div v-for="it in itemsByOrder[item.id]" :key="it.id" class="text-body-2">
            {{ it.menu?.name || it.menu?.title || ('Позиция #' + (it.menu_id || '')) }} × {{ it.qty }}
          </div>
        </div>
        <span v-else class="text-medium-emphasis">Состав заказа пуст</span>
      </template>
      <template #item.total="{ item }"><strong>{{ price(total(item.id)) }}</strong></template>
      <template #item.actions="{ item }">
        <v-btn size="small" class="mr-2" @click="openEdit(item)">Редактировать</v-btn>
        <v-btn size="small" color="error" variant="outlined" @click="deleteOrder(item.id)">Удалить</v-btn>
      </template>
      <template #no-data><div class="py-6 text-medium-emphasis">Заказов пока нет</div></template>
    </v-data-table>

    <v-dialog v-model="editOpen" max-width="900">
      <v-card>
        <v-card-title class="text-h6">Заказ #{{ editing.id }}</v-card-title>
        <v-card-text>
          <v-row class="mb-2">
            <v-col cols="12" md="6"><v-select v-model="editing.status" :items="['NEW','IN_PROGRESS','DONE','CANCELLED']" label="Статус" /></v-col>
          </v-row>
          <v-table density="comfortable">
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
                <td><v-text-field v-model.number="row.qty" type="number" min="0" density="compact" /></td>
                <td>{{ price(row.price * row.qty) }}</td>
                <td><v-btn size="small" variant="outlined" color="error" @click="row.qty=0">Удалить</v-btn></td>
              </tr>
              <tr v-if="!editing.rows.length"><td colspan="6" class="text-center text-medium-emphasis py-4">Пусто</td></tr>
            </tbody>
          </v-table>
          <v-alert v-if="errorMsg" type="error" class="mt-2">{{ errorMsg }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editOpen=false">Закрыть</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveEdit">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api, { ensureCsrf } from '@/api'

const orders = ref([])
const itemsByOrder = ref({})
const loading = ref(false)

const editOpen = ref(false)
const editing = reactive({ id:null, status:'NEW', rows:[] })
const saving = ref(false)
const errorMsg = ref('')

const headers = [
  { title:'ID', value:'id', width:100 },
  { title:'Клиент', value:'customer' },
  { title:'Состав', value:'items' },
  { title:'Сумма', value:'total', width:140 },
  { title:'Статус', value:'status', width:160 },
  { title:'Создан', value:'created_at', width:220 },
  { title:'Действия', value:'actions', width:180, sortable:false },
]

function price(v){ return Number(v||0).toFixed(2) }
function normalizeOrderId(raw){ if (raw && typeof raw==='object') return raw.id ?? null; return raw ?? null }

async function loadOrdersAndItems(){
  loading.value = true
  try{
    const [{ data: ordersResp }, { data: itemsResp }] = await Promise.all([
      api.get('/api/orders/'),
      api.get('/api/order-items/'),
    ])
    orders.value = Array.isArray(ordersResp) ? ordersResp : []
    const grouped = {}
    const list = Array.isArray(itemsResp) ? itemsResp : []
    for (const it of list){ const oid = normalizeOrderId(it.order) ?? it.order_id ?? it.orderId; if(!oid) continue; (grouped[oid] ||= []).push(it) }
    itemsByOrder.value = grouped
  } finally { loading.value = false }
}

function total(orderId){ const arr = itemsByOrder.value[orderId] || []; return arr.reduce((s,it)=> s + Number(it?.menu?.price ?? it?.price ?? 0) * Number(it?.qty ?? 0), 0) }

function openEdit(order){
  const rows = (itemsByOrder.value[order.id] || []).map(it => ({ id:it.id, name:it.menu?.name || it.menu?.title || `#${it.menu_id}`, price:Number(it.menu?.price ?? it.price ?? 0), qty:Number(it.qty ?? 0) }))
  editing.id = order.id; editing.status = order.status || 'NEW'; editing.rows = rows; errorMsg.value = ''; editOpen.value = true
}

async function saveEdit(){
  if (!editing.id) return
  saving.value = true
  errorMsg.value = ''
  try{
    await ensureCsrf()
    await api.patch(`/api/orders/${editing.id}/`, { status: editing.status })
    const original = itemsByOrder.value[editing.id] || []
    const byId = Object.fromEntries(original.map(r => [r.id, r]))
    for (const row of editing.rows){
      if (!byId[row.id]) continue
      if (row.qty <= 0){ await api.delete(`/api/order-items/${row.id}/`) }
      else if (row.qty !== Number(byId[row.id]?.qty)){ await api.patch(`/api/order-items/${row.id}/`, { qty: row.qty }) }
    }
    await loadOrdersAndItems()
    editOpen.value = false
  } catch{ errorMsg.value = 'Не удалось сохранить изменения.' }
  finally { saving.value = false }
}

async function deleteOrder(orderId){ if(!confirm(`Удалить заказ #${orderId}?`)) return; await ensureCsrf(); await api.delete(`/api/orders/${orderId}/`); await loadOrdersAndItems() }

onMounted(loadOrdersAndItems)
</script>
