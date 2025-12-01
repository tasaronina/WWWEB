<script setup>
import axios from "axios"
import { ref, computed, onBeforeMount } from "vue"
import "bootstrap/dist/js/bootstrap.bundle.min.js"
import "@/styles/admin.css"

axios.defaults.withCredentials = true

const canAdmin = ref(false)
async function detectAdmin(){
  if (typeof window !== "undefined" && (window.IS_ADMIN === true || window.__CAN_ADMIN__ === true || window.vCanAdmin === true)) return true
  try { if (localStorage.getItem("is_admin")==="1") return true } catch {}
  const eps=["/api/me/","/api/auth/me/","/api/users/me/","/api/user/","/api/whoami/"]
  for (const ep of eps){
    try{
      const {data}=await axios.get(ep)
      if (!data) continue
      const role=(data.role||"").toString().toLowerCase()
      if (data.is_superuser||data.is_staff||data.is_admin||["admin","staff","manager","superuser"].includes(role)) return true
    }catch{}
  }
  return false
}

const categories = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

const categoryToAdd = ref({ name: "" })
const categoryToEdit = ref({ id: null, name: "" })

const filters = ref({ id: "", name: "" })
function resetFilters(){ filters.value = { id: "", name: "" } }

function formatNumber(value){ const n=Number(value); return Number.isNaN(n) ? String(value) : n.toFixed(2) }

const filteredCategories = computed(() =>
  categories.value.filter((cat) => {
    const f = filters.value
    if (f.id && String(cat.id) !== f.id.trim()) return false
    if (f.name && !cat.name.toLowerCase().includes(f.name.toLowerCase().trim())) return false
    return true
  }),
)

async function fetchCategories(){ const { data } = await axios.get("/api/categories/"); categories.value = data }
async function fetchStats(){ const { data } = await axios.get("/api/categories/stats/"); stats.value = data }

function showModal(id){
  const el = document.getElementById(id)
  if (el && window.bootstrap) window.bootstrap.Modal.getOrCreateInstance(el).show()
}

async function onCategoryAdd(){
  if (!canAdmin.value) return
  if (!categoryToAdd.value.name.trim()) return
  await axios.post("/api/categories/", { name: categoryToAdd.value.name.trim() })
  categoryToAdd.value.name = ""
  await Promise.all([fetchCategories(), fetchStats()])
}
function onCategoryEditClick(cat){
  if (!canAdmin.value) return
  categoryToEdit.value = { id: cat.id, name: cat.name }
  showModal("editCategoryModal")
}
async function onUpdateCategory(){
  if (!canAdmin.value) return
  if (!categoryToEdit.value.name.trim()) return
  await axios.put(`/api/categories/${categoryToEdit.value.id}/`, { name: categoryToEdit.value.name.trim() })
  await Promise.all([fetchCategories(), fetchStats()])
}
async function onRemoveCategory(cat){
  if (!canAdmin.value) return
  if(!confirm(`Удалить категорию "${cat.name}"?`)) return
  await axios.delete(`/api/categories/${cat.id}/`)
  await Promise.all([fetchCategories(), fetchStats()])
}

onBeforeMount(async () => {
  canAdmin.value = await detectAdmin()
  loading.value = true; error.value = ""
  try { await Promise.all([fetchCategories(), fetchStats()]) }
  catch (e) { error.value = String(e) }
  finally { loading.value = false }
})
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Категории</h1>

    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="card mb-4" v-if="canAdmin">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить категорию</h5>
        <div class="row g-2 align-items-end">
          <div class="col-md-6">
            <label class="form-label">Название</label>
            <input v-model="categoryToAdd.name" type="text" class="form-control" placeholder="Например, Супы" />
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" type="button" @click="onCategoryAdd">Добавить</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего категорий: <strong>{{ stats.count }}</strong></span>
        <span>Средний ID: <strong>{{ formatNumber(stats.avg) }}</strong></span>
        <span>Максимальный ID: <strong>{{ stats.max }}</strong></span>
        <span>Минимальный ID: <strong>{{ stats.min }}</strong></span>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <div class="row filter-bar g-2 align-items-center">
          <div class="col-md-2">
            <input v-model="filters.id" type="text" class="form-control form-control-sm" placeholder="Фильтр по ID" />
          </div>
          <div class="col-md-4">
            <input v-model="filters.name" type="text" class="form-control form-control-sm" placeholder="Фильтр по названию" />
          </div>
          <div class="col-md-1 d-flex">
            <button type="button" class="btn btn-outline-secondary w-100" @click="resetFilters">Сброс</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th style="width: 90px">ID</th>
              <th>Название</th>
              <th style="width: 160px" v-if="canAdmin">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td :colspan="canAdmin ? 3 : 2" class="text-center text-muted">Загрузка...</td></tr>
            <tr v-for="cat in filteredCategories" :key="cat.id">
              <td>{{ cat.id }}</td>
              <td>{{ cat.name }}</td>
              <td v-if="canAdmin">
                <button class="btn btn-sm btn-outline-primary me-2" type="button" @click="onCategoryEditClick(cat)">Редактировать</button>
                <button class="btn btn-sm btn-outline-danger" type="button" @click="onRemoveCategory(cat)">Удалить</button>
              </td>
            </tr>
            <tr v-if="!loading && !filteredCategories.length"><td :colspan="canAdmin ? 3 : 2" class="text-center text-muted">Ничего не найдено</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div id="editCategoryModal" class="modal fade" tabindex="-1" aria-hidden="true" v-if="canAdmin">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Редактировать категорию #{{ categoryToEdit.id }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <label class="form-label">Название</label>
            <input v-model="categoryToEdit.name" type="text" class="form-control" />
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateCategory">Сохранить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
