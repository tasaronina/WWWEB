<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"

import "@/styles/admin.css"



const categories = ref([])
const loading = ref(false)
const error = ref("")

const categoryToAdd = ref({ name: "" })
const categoryToEdit = ref({ id: null, name: "" })

async function fetchCategories() {
  loading.value = true; error.value = ""
  try {
    const { data } = await axios.get("/api/categories/")
    categories.value = data
  } catch (e) { error.value = String(e) }
  finally { loading.value = false }
}

async function onCategoryAdd() {
  if (!categoryToAdd.value.name.trim()) return
  await axios.post("/api/categories/", { name: categoryToAdd.value.name.trim() })
  categoryToAdd.value.name = ""
  await fetchCategories()
}

function onCategoryEditClick(cat) {
  categoryToEdit.value = { ...cat }
  new bootstrap.Modal(document.getElementById("editCategoryModal")).show()
}

async function onUpdateCategory() {
  if (!categoryToEdit.value.name.trim()) return
  await axios.put(`/api/categories/${categoryToEdit.value.id}/`, { name: categoryToEdit.value.name.trim() })
  await fetchCategories()
}

async function onRemoveClick(cat) {
  if (!confirm(`Удалить категорию "${cat.name}"?`)) return
  await axios.delete(`/api/categories/${cat.id}/`)
  await fetchCategories()
}

onBeforeMount(fetchCategories)
</script>

<template>
  <div class="page">
    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="section">
      <h3>Категории</h3>

      <form class="inline-form" @submit.prevent="onCategoryAdd">
        <div class="form-floating">
          <input class="form-control" v-model="categoryToAdd.name" placeholder="Название" required />
          <label>Название категории</label>
        </div>
        <button class="btn btn-primary">Добавить</button>
      </form>
    </div>

    <div class="section">
      <div class="table-wrap">
        <table class="table table-bordered align-middle">
          <thead><tr><th style="width:90px">ID</th><th>Название</th><th style="width:160px">Действия</th></tr></thead>
          <tbody>
            <tr v-for="cat in categories" :key="cat.id">
              <td>{{ cat.id }}</td>
              <td>{{ cat.name ?? cat.title }}</td>
              <td>
                <button class="btn btn-sm btn-outline-warning me-2" @click="onCategoryEditClick(cat)">✏️</button>
                <button class="btn btn-sm btn-outline-danger" @click="onRemoveClick(cat)">🗑️</button>
              </td>
            </tr>
            <tr v-if="!loading && !categories.length"><td colspan="3" class="text-center text-muted">Пусто</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="editCategoryModal" tabindex="-1">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Редактировать категорию</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="form-floating">
            <input class="form-control" v-model="categoryToEdit.name" placeholder="Название категории" />
            <label>Название категории</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
          <button class="btn btn-primary" @click="onUpdateCategory" data-bs-dismiss="modal">Сохранить</button>
        </div>
      </div></div>
    </div>
  </div>
</template>
