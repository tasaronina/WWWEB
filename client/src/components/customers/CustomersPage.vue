<template>
  <div class="container my-4">
    <h1 class="mb-3">Клиенты</h1>

    <div class="alert alert-light border d-flex flex-wrap gap-4 mb-3">
      <div>Всего: <strong>{{ stats.total }}</strong></div>
      <div>Средний ID: <strong>{{ stats.avgId }}</strong></div>
      <div>Макс ID: <strong>{{ stats.maxId }}</strong></div>
      <div>Мин ID: <strong>{{ stats.minId }}</strong></div>
    </div>

    <!-- Добавить -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-5">
            <label class="form-label">Имя клиента</label>
            <input v-model="createForm.name" class="form-control" />
          </div>
          <div class="col-md-5">
            <label class="form-label">Фото</label>
            <input type="file" accept="image/*" class="form-control" @change="onPickCreate" />
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" :disabled="creating" @click="createCustomer">Добавить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2">
          <div class="col-md-6"><input v-model="filterId" class="form-control" placeholder="Фильтр по ID" /></div>
          <div class="col-md-6"><input v-model="filterName" class="form-control" placeholder="Фильтр по имени" /></div>
        </div>
      </div>
    </div>

    <!-- Таблица -->
    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead><tr>
            <th style="width:80px;">ID</th>
            <th style="width:100px;">Фото</th>
            <th>Имя</th>
            <th style="width:210px;">Действия</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="4" class="text-center text-muted">Загрузка…</td></tr>
            <tr v-for="c in filtered" :key="c.id">
              <td>{{ c.id }}</td>
              <td>
                <div class="thumb-64">
                  <img v-if="c.photoUrl" :src="c.photoUrl" alt="">
                  <div v-else class="thumb-empty">нет</div>
                </div>
              </td>
              <td class="fw-semibold">{{ c.name }}</td>
              <td>
                <div class="btn-group">
                  <button class="btn btn-outline-primary btn-sm" @click="startEdit(c)">Редактировать</button>
                  <button class="btn btn-outline-danger btn-sm" @click="removeCustomer(c.id)">Удалить</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filtered.length"><td colspan="4" class="text-center text-muted">Ничего не найдено</td></tr>
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
              <h5 class="modal-title">Редактировать клиента #{{ editForm.id }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Имя</label>
                <input v-model="editForm.name" class="form-control" required />
              </div>
              <div class="mb-2">
                <label class="form-label">Фото</label>
                <input type="file" accept="image/*" class="form-control" @change="onPickEdit" />
              </div>
              <div class="d-flex align-items-center gap-3">
                <div class="thumb-64 border">
                  <img v-if="editForm.preview" :src="editForm.preview" alt="">
                  <img v-else-if="editForm.photoUrl" :src="editForm.photoUrl" alt="">
                  <div v-else class="thumb-empty">нет</div>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" id="delPh" v-model="editForm.delete_photo" />
                  <label class="form-check-label" for="delPh">Удалить фото</label>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Закрыть</button>
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

axios.defaults.withCredentials = true

const customers = ref([])
const loading = ref(false)

const createForm = ref({ name:"", file:null })
const creating = ref(false)

const editForm = ref({ id:null, name:"", photoUrl:null, file:null, preview:null, delete_photo:false })
const saving = ref(false)
const editModalRef = ref(null)
let editModal = null

const filterId = ref("")
const filterName = ref("")

const filtered = computed(()=>{
  const id = filterId.value.trim()
  const q = filterName.value.trim().toLowerCase()
  return customers.value.filter(c=>{
    if(id && !String(c.id).includes(id)) return false
    if(q && !(c.name||"").toLowerCase().includes(q)) return false
    return true
  })
})

const stats = computed(()=>{
  const ids = customers.value.map(x=>x.id)
  const total = customers.value.length
  return {
    total,
    avgId: total ? (ids.reduce((a,b)=>a+b,0)/total).toFixed(2) : "—",
    maxId: ids.length? Math.max(...ids) : "—",
    minId: ids.length? Math.min(...ids) : "—",
  }
})

async function load(){
  loading.value = true
  try{
    const {data} = await axios.get("/api/customers/")
    customers.value = data.map(x=>({
      id:x.id, name:x.name||x.title||"",
      photoUrl: x.photo || x.image || x.picture || null
    })).sort((a,b)=>a.id-b.id) // по ID ↑
  } finally { loading.value = false }
}

function onPickCreate(e){ createForm.value.file = e.target.files?.[0] || null }
async function createCustomer(){
  if(!createForm.value.name) return
  creating.value = true
  try{
    const fd = new FormData()
    fd.append("name", createForm.value.name)
    if(createForm.value.file){
      fd.append("photo", createForm.value.file)
      fd.append("image", createForm.value.file)
      fd.append("picture", createForm.value.file)
    }
    const {data} = await axios.post("/api/customers/", fd, { headers:{ "Content-Type":"multipart/form-data" } })
    customers.value.push({
      id:data.id, name:data.name||createForm.value.name,
      photoUrl: data.photo || data.image || data.picture || null
    })
    customers.value.sort((a,b)=>a.id-b.id) // новый — внизу
    createForm.value = { name:"", file:null }
  } finally { creating.value = false }
}

function startEdit(c){
  if(!editModal && editModalRef.value) editModal = window.bootstrap.Modal.getOrCreateInstance(editModalRef.value)
  editForm.value = { id:c.id, name:c.name, photoUrl:c.photoUrl, file:null, preview:null, delete_photo:false }
  editModal?.show()
}
function onPickEdit(e){
  const f = e.target.files?.[0] || null
  editForm.value.file = f
  editForm.value.preview = f ? URL.createObjectURL(f) : null
  if(f) editForm.value.delete_photo = false
}
async function saveEdit(){
  saving.value = true
  try{
    const fd = new FormData()
    fd.append("name", editForm.value.name)
    if(editForm.value.delete_photo){ fd.append("delete_photo","1"); fd.append("remove_photo","1") }
    if(editForm.value.file){
      fd.append("photo", editForm.value.file)
      fd.append("image", editForm.value.file)
      fd.append("picture", editForm.value.file)
    }
    const {data} = await axios.patch(`/api/customers/${editForm.value.id}/`, fd, { headers:{ "Content-Type":"multipart/form-data" } })
    const i = customers.value.findIndex(x=>x.id===editForm.value.id)
    if(i>-1){
      customers.value[i] = {
        id:data.id,
        name:data.name ?? editForm.value.name,
        photoUrl: data.photo || data.image || data.picture || (editForm.value.delete_photo ? null : customers.value[i].photoUrl)
      }
    }
    customers.value.sort((a,b)=>a.id-b.id)
    editModal?.hide()
  } finally { saving.value = false }
}
async function removeCustomer(id){
  if(!confirm("Удалить клиента?")) return
  await axios.delete(`/api/customers/${id}/`)
  customers.value = customers.value.filter(x=>x.id!==id)
}

onMounted(load)
</script>

<style scoped>
.thumb-64{ width:64px;height:64px;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:.5rem;background:#f8f9fa }
.thumb-64 img{ width:100%;height:100%;object-fit:cover }
.thumb-empty{ font-size:.85rem;color:#6c757d }
</style>
