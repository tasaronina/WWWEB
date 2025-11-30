<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import Cookies from "js-cookie"
import "@/styles/admin.css"

axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")

const items = ref([])
const newItem = ref({ name:"", pictureFile:null, picturePreview:null })
const itemToEdit = ref({ id:null, name:"", pictureUrl:null })
const editPictureFile = ref(null)
const error = ref("")
const loading = ref(false)

async function fetchItems(){
  loading.value = true; error.value = ""
  try{
    const { data } = await axios.get("/api/customers/")
    items.value = data.map(it=>({
      ...it,
      pictureUrl: it.picture && !String(it.picture).startsWith("http")
        ? `${window.location.origin}${it.picture}` : it.picture
    }))
  }catch(e){ error.value = String(e) }
  finally{ loading.value = false }
}

function customerAddPictureChange(e){
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
  if(!newItem.value.name.trim()) return
  const fd = new FormData()
  fd.append("name", newItem.value.name.trim())
  if(newItem.value.pictureFile) fd.append("picture", newItem.value.pictureFile)
  await axios.post("/api/customers/", fd, { headers:{ "Content-Type":"multipart/form-data" } })
  if(newItem.value.picturePreview) URL.revokeObjectURL(newItem.value.picturePreview)
  newItem.value = { name:"", pictureFile:null, picturePreview:null }
  await fetchItems()
}

function onItemEditClick(it){
  itemToEdit.value = { id:it.id, name:it.name, pictureUrl: it.pictureUrl || null }
  editPictureFile.value = null
  new bootstrap.Modal(document.getElementById("editCustomerModal")).show()
}

async function onItemUpdate(){
  if(!itemToEdit.value.name.trim()) return
  const fd = new FormData()
  fd.append("name", itemToEdit.value.name.trim())
  if(editPictureFile.value) fd.append("picture", editPictureFile.value)
  await axios.put(`/api/customers/${itemToEdit.value.id}/`, fd, { headers:{ "Content-Type":"multipart/form-data" } })
  if(itemToEdit.value.pictureUrl) URL.revokeObjectURL(itemToEdit.value.pictureUrl)
  editPictureFile.value = null
  await fetchItems()
}

async function onRemoveClick(it){
  if(!confirm(`Удалить "${it.name}"?`)) return
  await axios.delete(`/api/customers/${it.id}/`)
  await fetchItems()
}

onBeforeMount(fetchItems)
</script>

<template>
  <div class="page">
    <div v-if="error" class="alert alert-danger alert-inline">Ошибка: {{ error }}</div>

    <div class="section">
      <h3>Добавить клиента</h3>
      <form class="inline-form" @submit.prevent="onItemAdd">
        <div class="form-floating">
          <input class="form-control" v-model="newItem.name" placeholder="Имя клиента" required />
          <label>Имя клиента</label>
        </div>
        <input type="file" class="form-control" accept="image/*" @change="customerAddPictureChange" />
        <img v-if="newItem.picturePreview" :src="newItem.picturePreview" class="preview-img round" />
        <button class="btn btn-primary">Добавить</button>
      </form>
    </div>

    <div class="section">
      <div class="list-group">
        <div v-for="it in items" :key="it.id" class="list-group-item">
          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
              <img v-if="it.pictureUrl" :src="it.pictureUrl" class="preview-img round me-3" style="width:60px;height:60px" />
              <div v-else class="bg-secondary text-white round d-flex align-items-center justify-content-center me-3" style="width:60px;height:60px">
                <b>{{ (it.name ?? 'U').charAt(0).toUpperCase() }}</b>
              </div>
              <div>
                <strong>{{ it.name }}</strong>
                <div class="text-muted small">ID: {{ it.id }}</div>
              </div>
            </div>
            <div>
              <button class="btn btn-sm btn-outline-warning me-2" @click="onItemEditClick(it)">✏️ Редактировать</button>
              <button class="btn btn-sm btn-outline-danger" @click="onRemoveClick(it)">🗑️ Удалить</button>
            </div>
          </div>
        </div>
        <div v-if="!loading && !items.length" class="text-center text-muted py-3">Пусто</div>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="editCustomerModal" tabindex="-1">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Редактировать клиента</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="form-floating mb-3">
            <input class="form-control" v-model="itemToEdit.name" placeholder="Имя" />
            <label>Имя</label>
          </div>
          <div class="mb-3">
            <label class="form-label">Изображение</label>
            <input type="file" class="form-control" accept="image/*" @change="onEditPictureChange" />
            <div class="form-text">Оставьте пустым, чтобы не менять картинку</div>
          </div>
          <img v-if="itemToEdit.pictureUrl" :src="itemToEdit.pictureUrl" class="preview-img round" style="max-height:100px;max-width:100px" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
          <button class="btn btn-primary" @click="onItemUpdate" data-bs-dismiss="modal">Сохранить</button>
        </div>
      </div></div>
    </div>
  </div>
</template>
