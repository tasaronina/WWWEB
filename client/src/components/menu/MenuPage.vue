<template>
  <v-container class="py-6" v-if="ready">
    <div class="text-h5 mb-4">Позиции меню</div>

    <v-alert v-if="!canAdmin" variant="outlined" class="mb-4 d-flex align-center ga-4 flex-wrap">
      <div class="font-weight-medium">Режим добавления:</div>
      <v-radio-group v-model="addMode" inline hide-details>
        <v-radio label="В один заказ" value="one" />
        <v-radio label="Раздельно (каждая позиция — отдельный заказ)" value="sep" />
      </v-radio-group>
      <template v-if="addMode==='one'">
        <div class="ms-auto d-flex align-center ga-3">
          <span class="text-medium-emphasis">Текущий заказ: <strong>{{ currentOrderId ? ('#'+currentOrderId) : '— (создастся при добавлении)' }}</strong></span>
          <v-btn size="small" variant="outlined" @click="startNewOrder">Начать новый</v-btn>
        </div>
      </template>
      <span class="text-medium-emphasis" v-if="flash">{{ flash }}</span>
    </v-alert>

    <v-card v-if="canAdmin" class="mb-4">
      <v-card-text>
        <div class="text-subtitle-1 mb-3">Добавить позицию</div>
        <v-form @submit.prevent="onCreate">
          <v-row class="align-end">
            <v-col cols="12" md="4"><v-text-field v-model="createForm.title" label="Название" /></v-col>
            <v-col cols="12" md="3">
              <v-select v-model="createForm.group_id" :items="categories" item-title="title" item-value="id" label="Категория" clearable />
            </v-col>
            <v-col cols="12" md="2"><v-text-field v-model.number="createForm.price" type="number" label="Цена" /></v-col>
            <v-col cols="12" md="3"><v-file-input v-model="createFile" label="Фото" accept="image/*" /></v-col>
          </v-row>
          <v-btn color="primary" class="mt-2" :loading="creating" type="submit">Добавить</v-btn>
        </v-form>
      </v-card-text>
    </v-card>

    <v-alert variant="outlined" class="mb-3 d-flex flex-wrap ga-6">
      <div>Всего позиций: <strong>{{ stats.total }}</strong></div>
      <div>Средняя цена: <strong>{{ money(stats.avg) }}</strong></div>
      <div>Макс. цена: <strong>{{ money(stats.max) }}</strong></div>
      <div>Мин. цена: <strong>{{ money(stats.min) }}</strong></div>
    </v-alert>

    <v-card class="mb-3">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6"><v-text-field v-model="filters.search" label="Фильтр по названию" /></v-col>
          <v-col cols="12" md="6"><v-select v-model="filters.category" :items="categories" item-title="title" item-value="id" label="Категория" clearable /></v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-data-table :headers="headers" :items="filteredMenu" :loading="loading" item-key="id">
      <template #item.picture="{ item }">
        <div class="thumb-64"><img v-if="item.pictureUrl" :src="item.pictureUrl" alt="" /><div v-else class="thumb-empty">нет</div></div>
      </template>
      <template #item.category="{ item }">{{ categoryName(item.group_id) || '—' }}</template>
      <template #item.actions="{ item }">
        <template v-if="!canAdmin">
          <div class="d-flex align-center ga-2">
            <v-text-field v-model.number="qty[item.id]" type="number" min="1" density="compact" style="max-width: 100px" @focus="initQty(item.id)" />
            <v-btn size="small" color="primary" :loading="adding[item.id]===true" @click="addToCart(item.id)">Добавить</v-btn>
          </div>
        </template>
        <template v-else>
          <v-btn size="small" variant="outlined" class="mr-2" @click="startEdit(item)">Редактировать</v-btn>
          <v-btn size="small" variant="outlined" color="error" @click="onDelete(item.id)">Удалить</v-btn>
        </template>
      </template>
      <template #no-data><div class="py-6 text-medium-emphasis">Ничего не найдено</div></template>
    </v-data-table>

    <v-dialog v-model="editOpen" max-width="800" v-if="canAdmin">
      <v-card>
        <v-card-title class="text-h6">Редактировать позицию #{{ editForm.id }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6"><v-text-field v-model="editForm.title" label="Название" /></v-col>
            <v-col cols="12" md="6"><v-select v-model="editForm.group_id" :items="categories" item-title="title" item-value="id" label="Категория" clearable /></v-col>
            <v-col cols="12" md="4"><v-text-field v-model.number="editForm.price" label="Цена" type="number" /></v-col>
            <v-col cols="12" md="8">
              <v-file-input v-model="editFile" label="Фото" accept="image/*" />
              <div class="d-flex align-center ga-4 mt-2">
                <div class="thumb-64 border">
                  <img v-if="editPreview" :src="editPreview" alt="" />
                  <img v-else-if="editForm.pictureUrl" :src="editForm.pictureUrl" alt="" />
                  <div v-else class="thumb-empty">нет</div>
                </div>
                <v-checkbox v-model="editForm.delete_picture" label="Удалить фото" />
              </div>
            </v-col>
          </v-row>
          <v-alert v-if="editError" type="error" class="mt-2">{{ editError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editOpen=false">Закрыть</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveEdit">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
  <v-container v-else class="py-10 text-center text-medium-emphasis">Загрузка…</v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

axios.defaults.withCredentials = true
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

async function ensureCsrf(){ try{ await axios.get('/api/csrf/') }catch{} }

const headers = [
  { title:'ID', value:'id', width:80 },
  { title:'Фото', value:'picture', width:100, sortable:false },
  { title:'Название', value:'title' },
  { title:'Категория', value:'category', width:200 },
  { title:'Цена', value:'price', width:120 },
  { title:'Действия', value:'actions', width:220, sortable:false },
]

const ready = ref(false)
const canAdmin = ref(false)
const addMode  = ref('one')
const flash    = ref('')
const currentOrderId = ref(null)
const newOrderNext   = ref(false)

const categories = ref([])
const menu = ref([])
const loading = ref(false)

const filters = ref({ search:'', category:'' })
const qty = ref({})
const adding = ref({})

const createForm = ref({ title:'', group_id:null, price:0 })
const createFile = ref(null)
const creating = ref(false)

const editOpen = ref(false)
const editError = ref('')
const editForm = ref({ id:null, title:'', group_id:null, price:0, pictureUrl:null, delete_picture:false })
const editFile = ref(null)
const editPreview = ref(null)
watch(editFile,(f)=>{ editPreview.value = f ? URL.createObjectURL(f) : null; if(f) editForm.value.delete_picture=false })

function money(v){ return Number(v||0).toFixed(2) }
function categoryName(id){ const c = categories.value.find(c=>String(c.id)===String(id)); return c? (c.title||c.name):'' }
function initQty(id){ if(!qty.value[id] || qty.value[id] < 1) qty.value[id] = 1 }
function startNewOrder(){ currentOrderId.value = null; newOrderNext.value = true; flash.value = 'Новый заказ: добавьте первую позицию'; setTimeout(()=> flash.value = '', 1500) }

const filteredMenu = computed(()=>{
  const q = filters.value.search.trim().toLowerCase()
  const cat = String(filters.value.category||'')
  return menu.value.filter(m=>{
    if(q && !(m.title||'').toLowerCase().includes(q)) return false
    if(cat && String(m.group_id)!==cat) return false
    return true
  })
})

const stats = computed(()=>{
  const arr = menu.value.map(m=>Number(m.price||0))
  const total = menu.value.length
  return { total, avg: total ? arr.reduce((a,b)=>a+b,0)/total : 0, max: arr.length ? Math.max(...arr) : 0, min: arr.length ? Math.min(...arr) : 0 }
})

async function detectAdmin(){
  try{ const { data } = await axios.get('/api/auth/me/'); const u = data?.user || data || {}; canAdmin.value = !!(u.is_staff || u.is_superuser) }catch{ canAdmin.value = false }
}
async function loadCategories(){
  try{ const { data } = await axios.get('/api/categories/'); const arr = Array.isArray(data) ? data : (data?.results ?? []); categories.value = arr.map(c=>({ id:c.id, title:c.title||c.name||'' })) }catch{ categories.value = [] }
}
async function loadMenu(){
  loading.value = true
  try{
    const { data } = await axios.get('/api/menu/')
    const list = Array.isArray(data) ? data : (data?.results ?? data ?? [])
    menu.value = list.map(x=>{
      const groupId = x.group_id ?? (x.group && typeof x.group==='object' ? x.group.id : x.group) ?? (x.category && typeof x.category==='object' ? x.category.id : x.category) ?? null
      return { id:x.id, title:x.title ?? x.name ?? '', group_id:Number(groupId)||null, price:Number(x.price??0), pictureUrl:x.picture || x.image || null }
    })
  } finally { loading.value = false }
}

async function onCreate(){
  creating.value = true
  try{
    await ensureCsrf()
    const fd = new FormData()
    fd.append('title', createForm.value.title)
    fd.append('name',  createForm.value.title)
    if(Number.isFinite(Number(createForm.value.group_id))){ const gid = String(createForm.value.group_id); fd.append('group_id', gid); fd.append('group', gid); fd.append('category', gid) }
    fd.append('price', String(Number(createForm.value.price||0)))
    if(createFile.value){ fd.append('picture', createFile.value); fd.append('image', createFile.value) }
    const { data } = await axios.post('/api/menu/', fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    menu.value.push({ id:data.id, title:data.title ?? data.name ?? createForm.value.title, group_id: data.group_id ?? (data.group?.id) ?? data.category ?? createForm.value.group_id ?? null, price:data.price ?? createForm.value.price, pictureUrl: data.picture || data.image || null })
    menu.value.sort((a,b)=>a.id-b.id)
    createForm.value = { title:'', group_id:null, price:0 }; createFile.value=null
  } finally { creating.value = false }
}

function startEdit(m){ editError.value=''; editForm.value = { id:m.id, title:m.title, group_id:m.group_id, price:Number(m.price||0), pictureUrl:m.pictureUrl, delete_picture:false }; editFile.value=null; editOpen.value=true }
async function saveEdit(){
  saving.value = true; editError.value=''
  try{
    await ensureCsrf()
    const fd = new FormData()
    fd.append('title', editForm.value.title)
    fd.append('name',  editForm.value.title)
    if(Number.isFinite(Number(editForm.value.group_id))){ const gid = String(editForm.value.group_id); fd.append('group_id', gid); fd.append('group', gid); fd.append('category', gid) }
    fd.append('price', String(Number(editForm.value.price||0)))
    if(editFile.value){ fd.append('picture', editFile.value); fd.append('image', editFile.value) }
    if(editForm.value.delete_picture){ fd.append('delete_picture','1'); fd.append('remove_picture','1') }
    const { data } = await axios.patch(`/api/menu/${editForm.value.id}/`, fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    const i = menu.value.findIndex(x=>x.id===editForm.value.id)
    if(i>-1){ menu.value[i] = { id:data.id, title:data.title ?? data.name ?? editForm.value.title, group_id: data.group_id ?? (data.group?.id) ?? data.category ?? editForm.value.group_id ?? null, price:data.price ?? editForm.value.price, pictureUrl: data.picture || data.image || (editForm.value.delete_picture ? null : menu.value[i].pictureUrl) } }
    menu.value.sort((a,b)=>a.id-b.id)
    editOpen.value=false
  } catch { editError.value='Не удалось сохранить. Проверьте поля или права.' }
  finally { saving.value = false }
}
async function onDelete(id){ if(!confirm('Удалить позицию меню?')) return; await ensureCsrf(); await axios.delete(`/api/menu/${id}/`); menu.value = menu.value.filter(x=>x.id!==id) }

async function addToCart(menuId){
  if (adding.value[menuId]) return
  adding.value[menuId] = true
  try{
    initQty(menuId)
    const count = Math.max(1, Number(qty.value[menuId] || 1))
    await ensureCsrf()
    const payload = { menu_id: menuId, qty: count }
    if (addMode.value === 'one'){
      if (currentOrderId.value) payload.order_id = currentOrderId.value; else payload.new_order = true
      if (newOrderNext.value) payload.new_order = true
    }
    if (addMode.value === 'sep') payload.new_order = true
    const { data } = await axios.post('/api/orders/add-to-cart/', payload)
    const createdOrderId = data?.order_id || data?.item?.order || data?.item?.order_id || data?.item?.order?.id || null
    if (addMode.value === 'one'){ if (!currentOrderId.value || newOrderNext.value) currentOrderId.value = createdOrderId; newOrderNext.value = false } else { currentOrderId.value = null }
    flash.value = `Добавлено: #${menuId} × ${count}${createdOrderId ? ' → заказ #'+createdOrderId : ''}`
    qty.value[menuId] = 1
    setTimeout(()=>{ flash.value='' }, 1500)
  } finally { adding.value[menuId] = false }
}

onMounted(async()=>{ await detectAdmin(); await Promise.allSettled([loadCategories(), loadMenu()]); ready.value=true })
</script>

<style scoped>
.thumb-64{ width:64px;height:64px;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:.5rem;background:#f8f9fa }
.thumb-64 img{ width:100%;height:100%;object-fit:cover }
.thumb-empty{ font-size:.85rem;color:#6c757d }
</style>
