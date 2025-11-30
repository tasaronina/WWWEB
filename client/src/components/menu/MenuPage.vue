<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import "@/styles/admin.css"

const items = ref([])
const categories = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref("")

const newItem = ref({
  name: "",
  group_id: null,
  price: 0,
  pictureFile: null,
  picturePreview: null,
})

const itemToEdit = ref({
  id: null,
  name: "",
  price: 0,
  _editGroupId: null,
  pictureUrl: null,
})

const editPictureFile = ref(null)

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

async function fetchItems() {
  const { data } = await axios.get("/api/menu/")
  items.value = data
}

async function fetchStats() {
  const { data } = await axios.get("/api/menu/stats/")
  stats.value = data
}

function onAddPictureChange(event) {
  const file = event.target.files?.[0]
  newItem.value.pictureFile = file || null
  newItem.value.picturePreview = file ? URL.createObjectURL(file) : null
}

function onEditPictureChange(event) {
  const file = event.target.files?.[0]
  editPictureFile.value = file || null
  if (file) {
    itemToEdit.value.pictureUrl = URL.createObjectURL(file)
  }
}

async function onItemAdd() {
  if (!newItem.value.name.trim() || !newItem.value.group_id) return

  const formData = new FormData()
  formData.append("name", newItem.value.name.trim())
  formData.append("group_id", String(newItem.value.group_id))
  formData.append("price", String(newItem.value.price || 0))
  if (newItem.value.pictureFile) {
    formData.append("picture", newItem.value.pictureFile)
  }

  await axios.post("/api/menu/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })

  newItem.value = {
    name: "",
    group_id: null,
    price: 0,
    pictureFile: null,
    picturePreview: null,
  }

  await Promise.all([fetchItems(), fetchStats()])
}

function onItemEditClick(it) {
  itemToEdit.value = {
    id: it.id,
    name: it.name,
    price: it.price ?? 0,
    _editGroupId: it.group?.id ?? it.group_id ?? null,
    pictureUrl: it.picture ?? null,
  }
  editPictureFile.value = null
  new bootstrap.Modal(document.getElementById("editMenuModal")).show()
}

async function onItemUpdate() {
  if (!itemToEdit.value.id || !itemToEdit.value.name.trim()) return

  const formData = new FormData()
  formData.append("name", itemToEdit.value.name.trim())
  if (itemToEdit.value._editGroupId) {
    formData.append("group_id", String(itemToEdit.value._editGroupId))
  }
  formData.append("price", String(itemToEdit.value.price || 0))
  if (editPictureFile.value) {
    formData.append("picture", editPictureFile.value)
  }

  await axios.put(`/api/menu/${itemToEdit.value.id}/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })

  await Promise.all([fetchItems(), fetchStats()])
}

async function onRemoveClick(it) {
  if (!confirm(`Удалить позицию "${it.name}"?`)) return
  await axios.delete(`/api/menu/${it.id}/`)
  await Promise.all([fetchItems(), fetchStats()])
}

onBeforeMount(async () => {
  loading.value = true
  error.value = ""
  try {
    await Promise.all([fetchCategories(), fetchItems(), fetchStats()])
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container my-4">
    <h1 class="mb-3">Позиции меню</h1>

    <div v-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title mb-3">Добавить позицию меню</h5>

        <div class="row g-3 align-items-end">
          <div class="col-md-4">
            <label class="form-label">Название</label>
            <input
              v-model="newItem.name"
              type="text"
              class="form-control"
              placeholder="Название блюда"
            />
          </div>

          <div class="col-md-3">
            <label class="form-label">Категория</label>
            <select v-model="newItem.group_id" class="form-select">
              <option value="">Категория...</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">
                {{ c.name }}
              </option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label">Цена</label>
            <input
              v-model.number="newItem.price"
              type="number"
              min="0"
              step="0.01"
              class="form-control"
            />
          </div>

          <div class="col-md-3">
            <label class="form-label">Изображение</label>
            <input
              type="file"
              accept="image/*"
              class="form-control"
              @change="onAddPictureChange"
            />
          </div>
        </div>

        <div v-if="newItem.picturePreview" class="mt-3">
          <img
            :src="newItem.picturePreview"
            alt="Превью"
            class="img-thumbnail"
            style="max-height: 160px"
          />
        </div>

        <div class="mt-3">
          <button class="btn btn-primary" type="button" @click="onItemAdd">
            Добавить
          </button>
        </div>
      </div>
    </div>

    <div v-if="stats" class="alert alert-secondary small mb-3">
      <div class="d-flex flex-wrap gap-3">
        <span>Всего позиций: <strong>{{ stats.count }}</strong></span>
        <span>Средняя цена: <strong>{{ formatNumber(stats.avg) }}</strong></span>
        <span>Максимальная цена: <strong>{{ formatNumber(stats.max) }}</strong></span>
        <span>Минимальная цена: <strong>{{ formatNumber(stats.min) }}</strong></span>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <h5 class="card-title mb-3">Список позиций</h5>

        <div v-if="loading" class="text-muted">
          Загрузка...
        </div>

        <div v-else-if="!items.length" class="text-muted">
          Позиции ещё не добавлены
        </div>

        <div v-else class="list-group">
          <div
            v-for="it in items"
            :key="it.id"
            class="list-group-item d-flex align-items-center justify-content-between"
          >
            <div class="d-flex align-items-center gap-3">
              <div v-if="it.picture">
                <img
                  :src="it.picture"
                  alt=""
                  class="rounded"
                  style="width: 64px; height: 64px; object-fit: cover"
                />
              </div>
              <div>
                <div class="fw-semibold">{{ it.name }}</div>
                <div class="text-muted small">
                  ID: {{ it.id }}
                  <span v-if="it.group">
                    • Категория: {{ it.group.name }}
                  </span>
                  <span v-if="it.price !== undefined">
                    • Цена: {{ formatNumber(it.price) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="btn-group">
              <button
                class="btn btn-sm btn-outline-primary"
                type="button"
                @click="onItemEditClick(it)"
              >
                Редактировать
              </button>
              <button
                class="btn btn-sm btn-outline-danger"
                type="button"
                @click="onRemoveClick(it)"
              >
                Удалить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка редактирования позиции меню -->
    <div
      id="editMenuModal"
      class="modal fade"
      tabindex="-1"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              Редактировать позицию #{{ itemToEdit.id }}
            </h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="row g-3">
              <div class="col-md-5">
                <label class="form-label">Название</label>
                <input
                  v-model="itemToEdit.name"
                  type="text"
                  class="form-control"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">Категория</label>
                <select
                  v-model="itemToEdit._editGroupId"
                  class="form-select"
                >
                  <option
                    v-for="c in categories"
                    :key="c.id"
                    :value="c.id"
                  >
                    {{ c.name }}
                  </option>
                </select>
              </div>
              <div class="col-md-2">
                <label class="form-label">Цена</label>
                <input
                  v-model.number="itemToEdit.price"
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-control"
                />
              </div>
              <div class="col-md-4">
                <label class="form-label">Изображение</label>
                <input
                  type="file"
                  accept="image/*"
                  class="form-control"
                  @change="onEditPictureChange"
                />
                <div v-if="itemToEdit.pictureUrl" class="mt-2">
                  <img
                    :src="itemToEdit.pictureUrl"
                    alt=""
                    class="img-thumbnail"
                    style="max-height: 140px"
                  />
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              Закрыть
            </button>
            <button
              type="button"
              class="btn btn-primary"
              @click="onItemUpdate"
            >
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
