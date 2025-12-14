<template>
  <v-container class="py-6">
    <div class="text-h5 mb-4">Клиенты</div>

    <v-alert variant="outlined" class="mb-4">
      <div class="d-flex flex-wrap ga-6">
        <div>Всего: <strong>{{ stats.total }}</strong></div>
        <div>Средний ID: <strong>{{ stats.avgId }}</strong></div>
        <div>Макс ID: <strong>{{ stats.maxId }}</strong></div>
        <div>Мин ID: <strong>{{ stats.minId }}</strong></div>
      </div>
    </v-alert>

    <v-card class="mb-3">
      <v-card-text>
        <v-row class="align-end">
          <v-col cols="12" md="5">
            <v-text-field v-model="createForm.name" label="Имя клиента" />
          </v-col>
          <v-col cols="12" md="5">
            <v-file-input v-model="createFile" label="Фото" accept="image/*" />
          </v-col>
          <v-col cols="12" md="2">
            <v-btn color="primary" :loading="creating" block @click="createCustomer">Добавить</v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="mb-3">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6"><v-text-field v-model="filterId" label="Фильтр по ID" /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="filterName" label="Фильтр по имени" /></v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-data-table :headers="headers" :items="filtered" :loading="loading" item-key="id">
      <template #item.photo="{ item }">
        <div class="thumb-64">
          <img v-if="item.photoUrl" :src="item.photoUrl" alt="" />
          <div v-else class="thumb-empty">нет</div>
        </div>
      </template>
      <template #item.actions="{ item }">
        <v-btn size="small" variant="outlined" class="mr-2" @click="startEdit(item)">Редактировать</v-btn>
        <v-btn size="small" variant="outlined" color="error" @click="removeCustomer(item.id)">Удалить</v-btn>
      </template>
      <template #no-data><div class="py-6 text-medium-emphasis">Ничего не найдено</div></template>
    </v-data-table>

    <v-dialog v-model="editOpen" max-width="600">
      <v-card>
        <v-card-title class="text-h6">Редактировать клиента #{{ editForm.id }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="editForm.name" label="Имя" />
          <v-file-input v-model="editFile" label="Фото" accept="image/*" class="mt-2" />
          <div class="d-flex align-center ga-4 mt-2">
            <div class="thumb-64 border">
              <img v-if="editPreview" :src="editPreview" alt="" />
              <img v-else-if="editForm.photoUrl" :src="editForm.photoUrl" alt="" />
              <div v-else class="thumb-empty">нет</div>
            </div>
            <v-checkbox v-model="editForm.delete_photo" label="Удалить фото" />
          </div>
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
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

axios.defaults.withCredentials = true
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const headers = [
  { title: 'ID', value: 'id', width: 90 },
  { title: 'Фото', value: 'photo', width: 110, sortable: false },
  { title: 'Имя', value: 'name' },
  { title: 'Действия', value: 'actions', width: 210, sortable: false },
]

const customers = ref([])
const loading = ref(false)

const createForm = ref({ name: '' })
const createFile = ref(null)
const creating = ref(false)

const editForm = ref({ id:null, name:'', photoUrl:null, delete_photo:false })
const editFile = ref(null)
const editPreview = ref(null)
const editOpen = ref(false)
const saving = ref(false)

const filterId = ref('')
const filterName = ref('')

const filtered = computed(()=>{
  const id = filterId.value.trim()
  const q = filterName.value.trim().toLowerCase()
  return customers.value.filter(c=>{
    if(id && !String(c.id).includes(id)) return false
    if(q && !(c.name||'').toLowerCase().includes(q)) return false
    return true
  })
})

const stats = computed(()=>{
  const ids = customers.value.map(x=>x.id)
  const total = customers.value.length
  return {
    total,
    avgId: total ? (ids.reduce((a,b)=>a+b,0)/total).toFixed(2) : '—',
    maxId: ids.length? Math.max(...ids) : '—',
    minId: ids.length? Math.min(...ids) : '—',
  }
})

async function load(){
  loading.value = true
  try{
    const { data } = await axios.get('/api/customers/')
    customers.value = (data||[]).map(x=>({ id:x.id, name:x.name||x.title||'', photoUrl: x.photo || x.image || x.picture || null })).sort((a,b)=>a.id-b.id)
  } finally { loading.value = false }
}

async function createCustomer(){
  if(!createForm.value.name) return
  creating.value = true
  try{
    const fd = new FormData()
    fd.append('name', createForm.value.name)
    if(createFile.value){ fd.append('photo', createFile.value); fd.append('image', createFile.value); fd.append('picture', createFile.value) }
    const { data } = await axios.post('/api/customers/', fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    customers.value.push({ id:data.id, name:data.name||createForm.value.name, photoUrl: data.photo || data.image || data.picture || null })
    customers.value.sort((a,b)=>a.id-b.id)
    createForm.value = { name:'' }; createFile.value = null
  } finally { creating.value = false }
}

function startEdit(c){ editForm.value = { id:c.id, name:c.name, photoUrl:c.photoUrl, delete_photo:false }; editFile.value=null; editPreview.value=null; editOpen.value=true }
watch(editFile,(f)=>{ editPreview.value = f ? URL.createObjectURL(f) : null; if(f) editForm.value.delete_photo=false })

async function saveEdit(){
  saving.value = true
  try{
    const fd = new FormData()
    fd.append('name', editForm.value.name)
    if(editForm.value.delete_photo){ fd.append('delete_photo','1'); fd.append('remove_photo','1') }
    if(editFile.value){ fd.append('photo', editFile.value); fd.append('image', editFile.value); fd.append('picture', editFile.value) }
    const { data } = await axios.patch(`/api/customers/${editForm.value.id}/`, fd, { headers:{ 'Content-Type':'multipart/form-data' } })
    const i = customers.value.findIndex(x=>x.id===editForm.value.id)
    if(i>-1){ customers.value[i] = { id:data.id, name:data.name ?? editForm.value.name, photoUrl: data.photo || data.image || data.picture || (editForm.value.delete_photo ? null : customers.value[i].photoUrl) } }
    customers.value.sort((a,b)=>a.id-b.id)
    editOpen.value = false
  } finally { saving.value = false }
}

async function removeCustomer(id){ if(!confirm('Удалить клиента?')) return; await axios.delete(`/api/customers/${id}/`); customers.value = customers.value.filter(x=>x.id!==id) }

onMounted(load)
</script>

<style scoped>
.thumb-64{ width:64px;height:64px;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:.5rem;background:#f8f9fa }
.thumb-64 img{ width:100%;height:100%;object-fit:cover }
.thumb-empty{ font-size:.85rem;color:#6c757d }
</style>
