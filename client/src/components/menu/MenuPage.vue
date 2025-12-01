<template>
  <div class="container my-4">
    <h1 class="mb-3">Позиции меню</h1>

    <!-- Добавить позицию (только админ) -->
    <div class="card mb-3" v-if="canAdmin">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить позицию</h5>
        <form @submit.prevent="onCreate">
          <div class="row g-3 align-items-end">
            <div class="col-md-4">
              <label class="form-label">Название</label>
              <input v-model="createForm.name" class="form-control" required />
            </div>
            <div class="col-md-3">
              <label class="form-label">Категория</label>
              <select v-model="createForm.group_id" class="form-select">
                <option :value="null">— не выбрано —</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="col-md-2">
              <label class="form-label">Цена</label>
              <input v-model.number="createForm.price" type="number" min="0" step="0.01" class="form-control" />
            </div>
            <div class="col-md-3">
              <label class="form-label">Фото</label>
              <input type="file" class="form-control" accept="image/*" @change="onPickCreate" />
            </div>
          </div>
          <div class="mt-3">
            <button class="btn btn-primary" :disabled="creating">Добавить</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Статистика -->
    <div class="alert alert-light border d-flex flex-wrap gap-4 mb-3">
      <div>Всего позиций: <strong>{{ stats.total }}</strong></div>
      <div>Средняя цена: <strong>{{ money(stats.avg) }}</strong></div>
      <div>Макс. цена: <strong>{{ money(stats.max) }}</strong></div>
      <div>Мин. цена: <strong>{{ money(stats.min) }}</strong></div>
    </div>

    <!-- Фильтры -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2">
          <div class="col-md-6"><input v-model="filters.search" class="form-control" placeholder="Фильтр по названию" /></div>
          <div class="col-md-6">
            <select v-model="filters.category" class="form-select">
              <option value="">Все категории</option>
              <option v-for="c in categories" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Таблица -->
    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th style="width:80px;">ID</th>
              <th style="width:100px;">Фото</th>
              <th>Название</th>
              <th style="width:200px;">Категория</th>
              <th style="width:120px;">Цена</th>
              <th style="width:210px;" v-if="canAdmin">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="6" class="text-center text-muted">Загрузка…</td></tr>
            <tr v-for="m in filteredMenu" :key="m.id">
              <td>{{ m.id }}</td>
              <td>
                <div class="thumb-64">
                  <img v-if="m.pictureUrl" :src="m.pictureUrl" alt="">
                  <div v-else class="thumb-empty">нет</div>
                </div>
              </td>
              <td class="fw-semibold">{{ m.name }}</td>
              <td>{{ categoryName(m.group_id) || "—" }}</td>
              <td>{{ money(m.price) }}</td>
              <td v-if="canAdmin">
                <div class="btn-group">
                  <button class="btn btn-outline-primary btn-sm" @click="startEdit(m)">Редактировать</button>
                  <button class="btn btn-outline-danger btn-sm" @click="onDelete(m.id)">Удалить</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filteredMenu.length">
              <td colspan="6" class="text-center text-muted">Ничего не найдено</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модалка редактирования -->
    <div class="modal fade" tabindex="-1" ref="editModalRef">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <form @submit.prevent="saveEdit">
            <div class="modal-header">
              <h5 class="modal-title">Редактировать позицию #{{ editForm.id }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label">Название</label>
                  <input v-model="editForm.name" class="form-control" required />
                </div>
                <div class="col-md-6">
                  <label class="form-label">Категория</label>
                  <select v-model="editForm.group_id" class="form-select">
                    <option :value="null">— не выбрано —</option>
                    <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Цена</label>
                  <input v-model.number="editForm.price" type="number" min="0" step="0.01" class="form-control" />
                </div>
                <div class="col-md-8">
                  <label class="form-label">Фото</label>
                  <input type="file" accept="image/*" class="form-control" @change="onPickEdit" />
                  <div class="d-flex align-items-center gap-3 mt-2">
                    <div class="thumb-64 border">
                      <img v-if="editForm.preview" :src="editForm.preview" alt="">
                      <img v-else-if="editForm.pictureUrl" :src="editForm.pictureUrl" alt="">
                      <div v-else class="thumb-empty">нет</div>
                    </div>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="delPic" v-model="editForm.delete_picture" />
                      <label class="form-check-label" for="delPic">Удалить фото</label>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="editError" class="alert alert-danger mt-3">{{ editError }}</div>
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

const canAdmin = ref(true)

const categories = ref([])
const menu = ref([])
const loading = ref(false)

const filters = ref({ search:"", category:"" })

const createForm = ref({ name:"", group_id:null, price:0, file:null })
const creating = ref(false)

const editModalRef = ref(null)
let editModal = null
const saving = ref(false)
const editError = ref("")
const editForm = ref({
  id:null, name:"", group_id:null, price:0, pictureUrl:null, file:null, preview:null, delete_picture:false
})

function money(v){ return Number(v||0).toFixed(2) }
function categoryName(id){ return categories.value.find(c=>c.id===id)?.name || "" }

const filteredMenu = computed(()=>{
  const q = filters.value.search.trim().toLowerCase()
  const cat = filters.value.category
  return menu.value.filter(m=>{
    if(q && !(m.name||"").toLowerCase().includes(q)) return false
    if(cat && String(m.group_id)!==cat) return false
    return true
  })
})

const stats = computed(()=>{
  const arr = menu.value.map(m=>Number(m.price||0))
  const total = menu.value.length
  return {
    total,
    avg: total ? arr.reduce((a,b)=>a+b,0)/total : 0,
    max: arr.length ? Math.max(...arr) : 0,
    min: arr.length ? Math.min(...arr) : 0
  }
})

async function loadCategories(){
  const {data} = await axios.get("/api/categories/")
  categories.value = data
}
async function loadMenu(){
  loading.value = true
  try{
    const {data} = await axios.get("/api/menu/")
    menu.value = data.map(x=>{
      // корректно вытаскиваем идентификатор категории
      const groupId =
        x.group_id ??
        (x.group && typeof x.group === "object" ? x.group.id : x.group) ??
        (x.category && typeof x.category === "object" ? x.category.id : x.category) ??
        null
      return {
        id:x.id,
        name:x.name ?? x.title ?? "",
        group_id: Number.isFinite(Number(groupId)) ? Number(groupId) : null,
        price:Number(x.price ?? 0),
        pictureUrl:x.picture || x.image || null
      }
    })
  } finally { loading.value = false }
}

function onPickCreate(e){ createForm.value.file = e.target.files?.[0] || null }
async function onCreate(){
  creating.value = true
  try{
    const fd = new FormData()
    fd.append("name", createForm.value.name)
    if(Number.isFinite(Number(createForm.value.group_id))){
      fd.append("group_id", String(createForm.value.group_id))
      fd.append("group", String(createForm.value.group_id))
      fd.append("category", String(createForm.value.group_id))
    }
    fd.append("price", String(Number(createForm.value.price||0)))
    if(createForm.value.file){
      fd.append("picture", createForm.value.file)
      fd.append("image", createForm.value.file)
    }
    const {data} = await axios.post("/api/menu/", fd, { headers:{ "Content-Type":"multipart/form-data" } })
    // добавляем и поддерживаем порядок по ID ↑
    menu.value.push({
      id:data.id,
      name:data.name ?? createForm.value.name,
      group_id: data.group_id ?? (data.group?.id) ?? data.category ?? createForm.value.group_id ?? null,
      price:data.price ?? createForm.value.price,
      pictureUrl: data.picture || data.image || null
    })
    menu.value.sort((a,b)=>a.id-b.id)
    createForm.value = { name:"", group_id:null, price:0, file:null }
  } finally { creating.value = false }
}

function startEdit(m){
  if(!editModal && editModalRef.value) editModal = window.bootstrap.Modal.getOrCreateInstance(editModalRef.value)
  editError.value = ""
  editForm.value = {
    id:m.id,
    name:m.name,
    group_id:m.group_id,
    price:Number(m.price||0),
    pictureUrl:m.pictureUrl,
    file:null,
    preview:null,
    delete_picture:false
  }
  editModal?.show()
}
function onPickEdit(e){
  const f = e.target.files?.[0] || null
  editForm.value.file = f
  editForm.value.preview = f ? URL.createObjectURL(f) : null
  if(f) editForm.value.delete_picture = false
}
async function saveEdit(){
  saving.value = true
  editError.value = ""
  try{
    const fd = new FormData()
    fd.append("name", editForm.value.name)
    if(Number.isFinite(Number(editForm.value.group_id))){
      fd.append("group_id", String(editForm.value.group_id))
      fd.append("group", String(editForm.value.group_id))
      fd.append("category", String(editForm.value.group_id))
    }
    fd.append("price", String(Number(editForm.value.price || 0)))
    if(editForm.value.file){
      fd.append("picture", editForm.value.file)
      fd.append("image", editForm.value.file)
    }
    if(editForm.value.delete_picture){
      fd.append("delete_picture","1")
      fd.append("remove_picture","1")
    }
    const {data} = await axios.patch(`/api/menu/${editForm.value.id}/`, fd, { headers:{ "Content-Type":"multipart/form-data" } })
    const i = menu.value.findIndex(x=>x.id===editForm.value.id)
    if(i>-1){
      menu.value[i] = {
        id:data.id,
        name:data.name ?? editForm.value.name,
        group_id: data.group_id ?? (data.group?.id) ?? data.category ?? editForm.value.group_id ?? null,
        price:data.price ?? editForm.value.price,
        pictureUrl: data.picture || data.image || (editForm.value.delete_picture ? null : menu.value[i].pictureUrl)
      }
      menu.value.sort((a,b)=>a.id-b.id)
    }
    editModal?.hide()
  } catch(e){ editError.value = "Не удалось сохранить. Проверь поля и файл изображения." }
  finally { saving.value = false }
}
async function onDelete(id){
  if(!confirm("Удалить позицию меню?")) return
  await axios.delete(`/api/menu/${id}/`)
  menu.value = menu.value.filter(x=>x.id!==id)
}

onMounted(async ()=>{ await Promise.all([loadCategories(), loadMenu()]) })
</script>

<style scoped>
.thumb-64{ width:64px;height:64px;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:.5rem;background:#f8f9fa }
.thumb-64 img{ width:100%;height:100%;object-fit:cover }
.thumb-empty{ font-size:.85rem;color:#6c757d }
</style>
