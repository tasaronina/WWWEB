<template>
  <v-container class="py-6">
    <div class="text-h5 mb-4">Категории</div>

    <v-alert variant="outlined" class="mb-4">
      <div class="d-flex flex-wrap ga-6">
        <div>Всего категорий: <strong>{{ stats.total }}</strong></div>
        <div>Средний ID: <strong>{{ stats.avgId }}</strong></div>
        <div>Максимальный ID: <strong>{{ stats.maxId }}</strong></div>
        <div>Минимальный ID: <strong>{{ stats.minId }}</strong></div>
      </div>
    </v-alert>

    <v-card class="mb-4">
      <v-card-text>
        <div class="text-subtitle-1 mb-3">Добавить категорию</div>
        <v-form @submit.prevent="createCategory">
          <v-row class="align-end">
            <v-col cols="12" md="6">
              <v-text-field v-model="createForm.name" label="Название" placeholder="Например, Супы" />
            </v-col>
            <v-col cols="12" md="2">
              <v-btn color="primary" :loading="creating" type="submit" block>Добавить</v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-card class="mb-3">
      <v-card-text>
        <v-row class="ga-2">
          <v-col cols="12" md="2"><v-text-field v-model="filters.id" label="Фильтр по ID" density="compact" /></v-col>
          <v-col cols="12" md="4"><v-text-field v-model="filters.name" label="Фильтр по названию" density="compact" /></v-col>
          <v-col cols="12" md="2"><v-btn variant="outlined" @click="resetFilters" block>Сброс</v-btn></v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-data-table :items="filtered" :headers="headers" :loading="loading" item-key="id" class="rounded-lg elevation-1">
      <template #item.actions="{ item }">
        <v-btn size="small" variant="outlined" class="mr-2" @click="startEdit(item)">Редактировать</v-btn>
        <v-btn size="small" variant="outlined" color="error" @click="removeCategory(item.id)">Удалить</v-btn>
      </template>
      <template #no-data>
        <div class="text-medium-emphasis py-6">Ничего не найдено</div>
      </template>
    </v-data-table>

    <v-dialog v-model="editOpen" max-width="480">
      <v-card>
        <v-card-title class="text-h6">Редактировать категорию #{{ editForm.id }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="editForm.name" label="Название" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editOpen=false">Отмена</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveEdit">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

axios.defaults.withCredentials = true
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const headers = [
  { title: 'ID', value: 'id', width: 90 },
  { title: 'Название', value: 'name' },
  { title: 'Действия', value: 'actions', width: 200, sortable: false },
]

const categories = ref([])
const loading = ref(false)

const filters = ref({ id: '', name: '' })
const creating = ref(false)
const createForm = ref({ name: '' })

const saving = ref(false)
const editOpen = ref(false)
const editForm = ref({ id: null, name: '' })

const filtered = computed(()=>{
  const id = filters.value.id.trim()
  const q = filters.value.name.trim().toLowerCase()
  return categories.value.filter(c=>{
    if(id && !String(c.id).includes(id)) return false
    if(q && !(c.name||'').toLowerCase().includes(q)) return false
    return true
  })
})

const stats = computed(()=>{
  const ids = categories.value.map(x=>x.id)
  const total = categories.value.length
  return {
    total,
    avgId: total ? (ids.reduce((a,b)=>a+b,0)/total).toFixed(2) : '—',
    maxId: ids.length? Math.max(...ids) : '—',
    minId: ids.length? Math.min(...ids) : '—',
  }
})

function resetFilters(){ filters.value = { id:'', name:'' } }

async function load(){
  loading.value = true
  try{
    const { data } = await axios.get('/api/categories/')
    categories.value = (Array.isArray(data)? data: data?.results||[]).sort((a,b)=>a.id-b.id)
  } finally { loading.value = false }
}

async function createCategory(){
  if(!createForm.value.name) return
  creating.value = true
  try{
    const { data } = await axios.post('/api/categories/', { name: createForm.value.name })
    categories.value.push({ id: data.id, name: data.name || createForm.value.name })
    categories.value.sort((a,b)=>a.id-b.id)
    createForm.value = { name: '' }
  } finally { creating.value = false }
}

function startEdit(c){ editForm.value = { id:c.id, name:c.name }; editOpen.value = true }
async function saveEdit(){
  saving.value = true
  try{
    const { data } = await axios.put(`/api/categories/${editForm.value.id}/`, { name: editForm.value.name })
    const i = categories.value.findIndex(x=>x.id===editForm.value.id)
    if(i>-1){ categories.value[i] = { id:data.id, name:data.name || editForm.value.name } }
    categories.value.sort((a,b)=>a.id-b.id)
    editOpen.value = false
  } finally { saving.value = false }
}
async function removeCategory(id){
  if(!confirm('Удалить категорию?')) return
  await axios.delete(`/api/categories/${id}/`)
  categories.value = categories.value.filter(x=>x.id!==id)
}

onMounted(load)
</script>
