<template>
  <v-container class="py-6">
    <div class="text-h5 mb-3">Добавить позицию заказа</div>

    <v-alert v-if="error" type="error" class="mb-3">Не удалось загрузить позиции заказа</v-alert>

    <v-alert v-if="stats" variant="outlined" class="mb-3">
      <div class="d-flex flex-wrap ga-6">
        <span>Всего позиций: <strong>{{ stats.count }}</strong></span>
        <span>Средний ID: <strong>{{ stats.avg?.toFixed ? stats.avg.toFixed(2) : stats.avg }}</strong></span>
        <span>Максимальный ID: <strong>{{ stats.max }}</strong></span>
        <span>Минимальный ID: <strong>{{ stats.min }}</strong></span>
      </div>
    </v-alert>

    <v-row class="mb-3" v-if="canAdmin">
      <v-col cols="12" md="4">
        <v-select v-model="form.order_id" :items="orders" item-title="id" item-value="id" label="Заказ" :return-object="false" />
      </v-col>
      <v-col cols="12" md="5">
        <v-select v-model="form.menu_id" :items="menu" :item-title="m=>menuTitle(m)" item-value="id" label="Позиция меню" />
      </v-col>
      <v-col cols="12" md="2">
        <v-text-field v-model.number="form.qty" type="number" min="1" label="Кол-во" />
      </v-col>
      <v-col cols="12" md="1">
        <v-btn color="primary" block @click="onCreate">Создать</v-btn>
      </v-col>
    </v-row>

    <v-card class="mb-3">
      <v-card-text>
        <v-row class="align-center">
          <v-col cols="12" md="3"><v-text-field v-model="filters.id" label="Фильтр по ID" /></v-col>
          <v-col cols="12" md="3"><v-text-field v-model="filters.order" label="Фильтр по заказу" /></v-col>
          <v-col cols="12" md="4"><v-text-field v-model="filters.menuText" label="Фильтр по позиции" /></v-col>
          <v-col cols="12" md="1"><v-text-field v-model="filters.qty" label="Кол-во" /></v-col>
          <v-col cols="12" md="1"><v-btn variant="outlined" block @click="resetFilters">Сброс</v-btn></v-col>
        </v-row>
        <div class="mt-2 d-flex ga-2" v-if="canAdmin">
          <v-btn color="success" @click="onExport('excel')">Экспорт в Excel</v-btn>
          <v-btn color="primary" @click="onExport('word')">Экспорт в Word</v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-data-table :headers="headers" :items="filteredList" :loading="loading" item-key="id">
      <template #item.menu="{ item }">{{ item.menu?.name ?? item.menu?.title ?? ('Позиция #'+(item.menu?.id ?? item.menu_id)) }}</template>
      <template #item.qty="{ item }">
        <template v-if="canAdmin">
          <v-text-field v-model.number="item.qty" type="number" min="1" density="compact" />
        </template>
        <template v-else>{{ item.qty }}</template>
      </template>
      <template #item.actions="{ item }" v-if="canAdmin">
        <v-btn size="small" color="success" class="mr-2" @click="onSave(item)">Сохранить</v-btn>
        <v-btn size="small" variant="outlined" color="error" @click="onDelete(item)">Удалить</v-btn>
      </template>
      <template #no-data><div class="py-6 text-medium-emphasis">Позиции заказа пока не добавлены</div></template>
    </v-data-table>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { downloadExport, ensureCsrf } from '@/api'

axios.defaults.withCredentials = true
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const headers = [
  { title:'ID', value:'id', width:90 },
  { title:'Заказ', value:'order', width:100 },
  { title:'Позиция меню', value:'menu' },
  { title:'Кол-во', value:'qty', width:110 },
  { title:'Действия', value:'actions', width:150, sortable:false },
]

const canAdmin = ref(false)
async function detectAdmin(){
  try{ const { data } = await axios.get('/api/auth/me/'); const u = data?.user || data || {}; canAdmin.value = !!(u.is_superuser || u.is_staff) }catch{ canAdmin.value = false }
  return canAdmin.value
}

const orders  = ref([])
const menu    = ref([])
const items   = ref([])
const stats   = ref(null)
const loading = ref(false)
const error   = ref('')

const form = ref({ order_id: '', menu_id: '', qty: 1 })
const filters = ref({ id:'', order:'', menuText:'', qty:'' })

function menuTitle(m){ if(!m) return ''; if(typeof m==='object') return m.name ?? m.title ?? `Позиция #${m.id}`; return `Позиция #${m}` }

async function fetchOrders(){ const { data } = await axios.get('/api/orders/'); orders.value = Array.isArray(data) ? data : (data?.results ?? []) }
async function fetchMenu(){ const { data } = await axios.get('/api/menu/');   menu.value   = Array.isArray(data) ? data : (data?.results ?? []) }
async function fetchItems(){ const { data } = await axios.get('/api/order-items/'); items.value = Array.isArray(data) ? data : (data?.results ?? []) }
async function fetchStats(){ try{ const { data } = await axios.get('/api/order-items/stats/'); stats.value = data }catch{ stats.value = null } }

onMounted(async()=>{ await detectAdmin(); loading.value=true; error.value=''; try{ await Promise.all([fetchOrders(), fetchMenu(), fetchItems(), fetchStats()]) }catch{ error.value='Не удалось загрузить позиции заказа' } finally { loading.value=false } })

async function onCreate(){ if(!canAdmin.value) return; if(!form.value.order_id || !form.value.menu_id) return; await ensureCsrf(); await axios.post('/api/order-items/', { order_id:Number(form.value.order_id), menu_id:Number(form.value.menu_id), qty:Math.max(1, Number(form.value.qty)||1) }); form.value={ order_id:'', menu_id:'', qty:1 }; await Promise.all([fetchItems(), fetchStats()]) }
async function onDelete(it){ if(!canAdmin.value) return; if(!confirm('Удалить позицию?')) return; await ensureCsrf(); await axios.delete(`/api/order-items/${it.id}/`); await Promise.all([fetchItems(), fetchStats()]) }
async function onSave(it){ if(!canAdmin.value) return; await ensureCsrf(); await axios.patch(`/api/order-items/${it.id}/`, { qty: Math.max(1, Number(it.qty)||1) }); await Promise.all([fetchItems(), fetchStats()]) }

function buildExportParams(){ return {} }
async function onExport(type){ if(!canAdmin.value) return; await downloadExport('order-items', buildExportParams(), type, 'order_items') }

const filteredList = computed(()=>{
  const id = filters.value.id.trim(); const ord = filters.value.order.trim(); const mtxt = filters.value.menuText.trim().toLowerCase(); const q = filters.value.qty.trim()
  return items.value.filter(it=>{
    if(id && !String(it.id).includes(id)) return false
    if(ord && !String(it.order?.id ?? it.order_id).includes(ord)) return false
    const title = (it.menu?.name ?? it.menu?.title ?? `Позиция #${it.menu?.id ?? it.menu_id}`) + ''
    if(mtxt && !title.toLowerCase().includes(mtxt)) return false
    if(q && !String(it.qty).includes(q)) return false
    return true
  })
})
function resetFilters(){ filters.value = { id:'', order:'', menuText:'', qty:'' } }
</script>
