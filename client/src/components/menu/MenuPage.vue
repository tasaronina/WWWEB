<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import Cookies from "js-cookie"
import "@/styles/admin.css"

axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")

const items = ref([])
const categories = ref([])
const loading = ref(false)
const error = ref("")

const newItem = ref({ name: "", group_id: null, pictureFile: null, picturePreview: null })
const itemToEdit = ref({ id: null, name: "", _editGroupId: null, pictureUrl: null })
const editPictureFile = ref(null)

async function fetchCategories(){ const {data}=await axios.get("/api/categories/"); categories.value=data }
async function fetchItems(){
  const { data } = await axios.get("/api/menu/")
  items.value = data.map(it => ({
    ...it,
    pictureUrl: it.picture && !String(it.picture).startsWith("http")
      ? `${window.location.origin}${it.picture}`
      : it.picture
  }))
}

function itemAddPictureChange(e){
  if(!e.target.files.length) return
  if(newItem.value.picturePreview) URL.revokeObjectURL(newItem.value.picturePreview)
  newItem.value.pictureFile = e.target.files[0]
  newItem.value.picturePreview = URL.createObjectURL(newItem.value.pictureFile)
}

function onEditPictureChange(e){
  if(!e.target.files.length) return
  editPictureFile.value = e.target.files[0]
  if(itemToEdit.value.pictureUrl) URL.revokeObjectURL(itemToEdit.value.pictureUrl)
  itemToEdit.value.pictureUrl = URL.createObjectURL(editPictureFile.value)
}

async function onItemAdd(){
  if(!newItem.value.name.trim() || !newItem.value.group_id) return
  const fd = new FormData()
  fd.append("name", newItem.value.name.trim())
  fd.append("group_id", newItem.value.group_id)
  if(newItem.value.pictureFile) fd.append("picture", newItem.value.pictureFile)
  await axios.post("/api/menu/", fd, { headers:{ "Content-Type":"multipart/form-data" } })
  if(newItem.value.picturePreview) URL.revokeObjectURL(newItem.value.picturePreview)
  newItem.value = { name:"", group_id:null, pictureFile:null, picturePreview:null }
  await fetchItems()
}

function onItemEditClick(it){
  itemToEdit.value = {
    id: it.id, name: it.name,
    _editGroupId: it.group?.id || it.group || null,
    pictureUrl: it.pictureUrl || null
  }
  editPictureFile.value = null
  new bootstrap.Modal(document.getElementById("editItemModal")).show()
}

async function onItemUpdate(){
  if(!itemToEdit.value.name.trim()) return
  const fd = new FormData()
  fd.append("name", itemToEdit.value.name.trim())
  if(itemToEdit.value._editGroupId) fd.append("group_id", itemToEdit.value._editGroupId)
  if(editPictureFile.value) fd.append("picture", editPictureFile.value)
  await axios.patch(`/api/menu/${itemToEdit.value.id}/`, fd, { headers:{ "Content-Type":"multipart/form-data" } })
  if(itemToEdit.value.pictureUrl) URL.revokeObjectURL(itemToEdit.value.pictureUrl)
  editPictureFile.value = null
  await fetchItems()
}

async function onRemoveClick(it){
  if(!confirm(`Удалить позицию "${it.name}"?`)) return
  await axios.delete(`/api/menu/${it.id}/`)
  await fetchItems()
}

onBeforeMount(async ()=>{
  loading.value = true
  try{ await Promise.all([fetchCategories(), fetchItems()]) } 
  catch(e){ error.value = String(e) } 
  finally{ loading.value = false }
})
</script>

<template>
  <div class="page">
    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="section">
      <h3>Добавить блюдо</h3>
      <form class="inline-form" @submit.prevent="onItemAdd">
        <div class="form-floating">
          <input class="form-control" v-model="newItem.name" placeholder="Название блюда" required />
          <label>Название</label>
        </div>

        <div class="form-floating">
          <select class="form-select" v-model="newItem.group_id" required>
            <option value="" disabled>Категория…</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name ?? c.title }}</option>
          </select>
          <label>Категория</label>
        </div>

        <input type="file" class="form-control" accept="image/*" @change="itemAddPictureChange" />
        <img v-if="newItem.picturePreview" :src="newItem.picturePreview" class="preview-img" alt="Превью" />

        <button class="btn btn-primary">Добавить</button>
      </form>
    </div>

    <div class="section">
      <div class="table-wrap">
        <table class="table table-bordered align-middle">
          <thead>
            <tr>
              <th style="width:80px">ID</th><th style="width:100px">Изобр.</th>
              <th>Название</th><th>Категория</th><th style="width:220px">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td>{{ it.id }}</td>
              <td>
                <img v-if="it.pictureUrl" :src="it.pictureUrl" class="preview-img" style="max-width:80px" />
                <span v-else class="badge badge-muted">Нет</span>
              </td>
              <td><input class="form-control form-control-sm" v-model="it.name" /></td>
              <td>{{ it.group?.name ?? it.group?.title ?? ('#' + (typeof it.group === 'number' ? it.group : it.group?.id ?? '')) }}</td>
              <td>
                <button class="btn btn-sm btn-outline-success me-2" @click="onItemEditClick(it)">Редактировать</button>
                <button class="btn btn-sm btn-outline-danger" @click="onRemoveClick(it)">Удалить</button>
              </td>
            </tr>
            <tr v-if="!loading && !items.length"><td colspan="5" class="text-center text-muted">Пусто</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="editItemModal" tabindex="-1">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Редактировать позицию</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="form-floating mb-3">
            <input class="form-control" v-model="itemToEdit.name" placeholder="Название" />
            <label>Название</label>
          </div>
          <div class="form-floating mb-3">
            <select class="form-select" v-model="itemToEdit._editGroupId">
              <option value="">—</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name ?? c.title }}</option>
            </select>
            <label>Категория</label>
          </div>
          <div class="mb-3">
            <label class="form-label">Изображение</label>
            <input type="file" class="form-control" accept="image/*" @change="onEditPictureChange" />
            <div class="form-text">Оставьте пустым, чтобы не менять текущую картинку</div>
          </div>
          <img v-if="itemToEdit.pictureUrl" :src="itemToEdit.pictureUrl" class="preview-img" style="max-height:100px;max-width:150px" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
          <button class="btn btn-primary" @click="onItemUpdate" data-bs-dismiss="modal">Сохранить</button>
        </div>
      </div></div>
    </div>
  </div>
</template>
