

<template>
  <div class="container my-4">
    <h1 class="mb-3">Категории</h1>

    <div class="alert alert-light border d-flex flex-wrap gap-4 mb-3">
      <div>Всего категорий: <strong>{{ stats.total }}</strong></div>
      <div>Средний ID: <strong>{{ stats.avgId }}</strong></div>
      <div>Максимальный ID: <strong>{{ stats.maxId }}</strong></div>
      <div>Минимальный ID: <strong>{{ stats.minId }}</strong></div>
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить категорию</h5>
        <div class="row g-2 align-items-end">
          <div class="col-md-6">
            <label class="form-label">Название</label>
            <input v-model="createForm.name" class="form-control" placeholder="Например, Супы" />
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" :disabled="creating" @click="createCategory">Добавить</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2">
          <div class="col-md-2"><input v-model="filters.id" class="form-control form-control-sm" placeholder="Фильтр по ID" /></div>
          <div class="col-md-4"><input v-model="filters.name" class="form-control form-control-sm" placeholder="Фильтр по названию" /></div>
          <div class="col-md-2 d-grid"><button class="btn btn-outline-secondary" @click="resetFilters">Сброс</button></div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead><tr><th style="width:90px;">ID</th><th>Название</th><th style="width:160px">Действия</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="3" class="text-center text-muted">Загрузка…</td></tr>
            <tr v-for="c in filtered" :key="c.id">
              <td>{{ c.id }}</td>
              <td class="fw-semibold">{{ c.name }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-2" @click="startEdit(c)">Редактировать</button>
                <button class="btn btn-sm btn-outline-danger" @click="removeCategory(c.id)">Удалить</button>
              </td>
            </tr>
            <tr v-if="!loading && !filtered.length"><td colspan="3" class="text-center text-muted">Ничего не найдено</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модалка редактирования -->
    <div class="modal fade" tabindex="-1" ref="editModalRef">
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="saveEdit">
            <div class="modal-header">
              <h5 class="modal-title">Редактировать категорию #{{ editForm.id }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <label class="form-label">Название</label>
              <input v-model="editForm.name" class="form-control" required />
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Отмена</button>
              <button class="btn btn-primary" :disabled="saving">Сохранить</button>
            </div>
          </form>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import {ref, computed, onMounted} from "vue"
import axios from "axios"
import "bootstrap/dist/js/bootstrap.bundle.min.js"
import "@/styles/admin.css"

axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

axios.defaults.withCredentials = true

const categories = ref([])
const loading = ref(false)

const filters = ref({ id:"", name:"" })
const creating = ref(false)
const createForm = ref({ name:"" })

const editModalRef = ref(null)
let editModal = null
const saving = ref(false)
const editForm = ref({ id:null, name:"" })

const filtered = computed(()=>{
  const id = filters.value.id.trim()
  const q = filters.value.name.trim().toLowerCase()
  return categories.value.filter(c=>{
    if(id && !String(c.id).includes(id)) return false
    if(q && !(c.name||"").toLowerCase().includes(q)) return false
    return true
  })
})

const stats = computed(()=>{
  const ids = categories.value.map(x=>x.id)
  const total = categories.value.length
  return {
    total,
    avgId: total ? (ids.reduce((a,b)=>a+b,0)/total).toFixed(2) : "—",
    maxId: ids.length? Math.max(...ids) : "—",
    minId: ids.length? Math.min(...ids) : "—",
  }
})

function resetFilters(){ filters.value = { id:"", name:"" } }

async function load(){
  loading.value = true
  try{
    const {data} = await axios.get("/api/categories/")
    categories.value = data.sort((a,b)=>a.id-b.id) // порядок ID ↑
  } finally { loading.value = false }
}

async function createCategory(){
  if(!createForm.value.name) return
  creating.value = true
  try{
    const {data} = await axios.post("/api/categories/", { name:createForm.value.name })
    categories.value.push({ id:data.id, name:data.name || createForm.value.name }) // новый — внизу
    categories.value.sort((a,b)=>a.id-b.id)
    createForm.value = { name:"" }
  } finally { creating.value = false }
}

function startEdit(c){
  if(!editModal && editModalRef.value) editModal = window.bootstrap.Modal.getOrCreateInstance(editModalRef.value)
  editForm.value = { id:c.id, name:c.name }
  editModal?.show()
}
async function saveEdit(){
  saving.value = true
  try{
    const {data} = await axios.put(`/api/categories/${editForm.value.id}/`, { name:editForm.value.name })
    const i = categories.value.findIndex(x=>x.id===editForm.value.id)
    if(i>-1){ categories.value[i] = { id:data.id, name:data.name || editForm.value.name } }
    categories.value.sort((a,b)=>a.id-b.id)
    editModal?.hide()
  } finally { saving.value = false }
}
async function removeCategory(id){
  if(!confirm("Удалить категорию?")) return
  await axios.delete(`/api/categories/${id}/`)
  categories.value = categories.value.filter(x=>x.id!==id)
}

onMounted(load)
</script>
