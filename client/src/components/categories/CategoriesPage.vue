<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import "@/styles/admin.css"

const categories = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

const categoryToAdd = ref({ name: "" })
const categoryToEdit = ref({ id: null, name: "" })

function formatNumber(value) {
  if (value === null || value === undefined) return "-"
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toFixed(2)
}

async function fetchCategories() {
  const { data } = await axios.get("/api/categories/")
  categories.value = data
}

async function fetchStats() {
  const { data } = await axios.get("/api/categories/stats/")
  stats.value = data
}

async function onCategoryAdd() {
  if (!categoryToAdd.value.name.trim()) return
  await axios.post("/api/categories/", {
    name: categoryToAdd.value.name.trim(),
  })
  categoryToAdd.value.name = ""
  await Promise.all([fetchCategories(), fetchStats()])
}

function onCategoryEditClick(cat) {
  categoryToEdit.value = { id: cat.id, name: cat.name }
  new bootstrap.Modal(
    document.getElementById("editCategoryModal"),
  ).show()
}

async function onUpdateCategory() {
  if (!categoryToEdit.value.name.trim()) return
  await axios.put(`/api/categories/${categoryToEdit.value.id}/`, {
    name: categoryToEdit.value.name.trim(),
  })
  await Promise.all([fetchCategories(), fetchStats()])
}

async function onRemoveCategory(cat) {
  if (!confirm(`Удалить категорию "${cat.name}"?`)) return
  await axios.delete(`/api/categories/${cat.id}/`)
  await Promise.all([fetchCategories(), fetchStats()])
}

onBeforeMount(async () => {
  loading.value = true
  error.value = ""
  try {
    await Promise.all([fetchCategories(), fetchStats()])
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Категории</h1>

    <div v-if="error" class="alert alert-danger alert-inline">
      Ошибка: {{ error }}
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить категорию</h5>
        <div class="row g-2 align-items-end">
          <div class="col-md-6">
            <label class="form-label">Название</label>
            <input
              v-model="categoryToAdd.name"
              type="text"
              class="form-control"
              placeholder="Например, Супы"
            />
          </div>
          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" type="button" @click="onCategoryAdd">
              Добавить
            </button>
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

    <div class="card">
      <div class="card-body table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th style="width: 90px">ID</th>
              <th>Название</th>
              <th style="width: 160px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="3" class="text-center text-muted">Загрузка...</td>
            </tr>
            <tr v-for="cat in categories" :key="cat.id">
              <td>{{ cat.id }}</td>
              <td>{{ cat.name }}</td>
              <td>
                <button
                  class="btn btn-sm btn-outline-primary me-2"
                  type="button"
                  @click="onCategoryEditClick(cat)"
                >
                  Редактировать
                </button>
                <button
                  class="btn btn-sm btn-outline-danger"
                  type="button"
                  @click="onRemoveCategory(cat)"
                >
                  Удалить
                </button>
              </td>
            </tr>
            <tr v-if="!loading && !categories.length">
              <td colspan="3" class="text-center text-muted">
                Категорий пока нет
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      id="editCategoryModal"
      class="modal fade"
      tabindex="-1"
      aria-hidden="true"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              Редактировать категорию #{{ categoryToEdit.id }}
            </h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <label class="form-label">Название</label>
            <input
              v-model="categoryToEdit.name"
              type="text"
              class="form-control"
            />
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              Отмена
            </button>
            <button
              type="button"
              class="btn btn-primary"
              data-bs-dismiss="modal"
              @click="onUpdateCategory"
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
