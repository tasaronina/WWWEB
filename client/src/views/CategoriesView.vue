<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { categories } = storeToRefs(dataStore);

const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const name = ref("");
const editForm = ref({ id: null, name: "" });
const errorText = ref("");

onBeforeMount(async () => {
  await userStore.checkLogin();
  if (isAdmin.value) {
    await dataStore.fetchCategories();
  }
});

async function createCategory() {
  errorText.value = "";
  try {
    await axios.post("/api/categories/", { name: name.value });
    name.value = "";
    await dataStore.fetchCategories();
  } catch (e) {
    errorText.value = "Не удалось добавить категорию.";
  }
}

function openEdit(c) {
  editForm.value = { id: c.id, name: c.name || "" };
}

async function saveEdit() {
  errorText.value = "";
  const id = editForm.value.id;
  if (!id) return;

  try {
    await axios.put(`/api/categories/${id}/`, { name: editForm.value.name });
    await dataStore.fetchCategories();
  } catch (e) {
    errorText.value = "Не удалось сохранить изменения.";
  }
}

async function deleteCategory(id) {
  errorText.value = "";
  try {
    await axios.delete(`/api/categories/${id}/`);
    await dataStore.fetchCategories();
  } catch (e) {
    errorText.value = "Не удалось удалить категорию. Возможно, она используется в меню.";
  }
}
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Категории</h2>

    <div v-if="!isAdmin" class="alert alert-danger">
      Доступно только администратору.
    </div>

    <div v-else>
      <div v-if="errorText" class="alert alert-warning">{{ errorText }}</div>

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">Добавить категорию</div>
        <div class="card-body">
          <form class="d-flex gap-2" @submit.prevent="createCategory">
            <input v-model="name" class="form-control" placeholder="Название категории" required />
            <button class="btn btn-primary" type="submit">Добавить</button>
          </form>
        </div>
      </div>

      <div class="card">
        <div class="card-header bg-body-tertiary d-flex justify-content-between">
          <span>Список</span>
          <span class="text-muted">Всего: {{ categories.length }}</span>
        </div>

        <div class="card-body table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th style="width: 80px;">ID</th>
                <th>Название</th>
                <th style="width: 240px;">Действия</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="c in categories" :key="c.id">
                <td>{{ c.id }}</td>
                <td class="fw-semibold">{{ c.name }}</td>
                <td class="d-flex gap-2">
                  <button
                    class="btn btn-sm btn-outline-primary"
                    data-bs-toggle="modal"
                    data-bs-target="#editCategoryModal"
                    @click="openEdit(c)"
                  >
                    Редактировать
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteCategory(c.id)">
                    Удалить
                  </button>
                </td>
              </tr>

              <tr v-if="categories.length === 0">
                <td colspan="3" class="text-center text-muted">Пока категорий нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="modal fade" id="editCategoryModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Редактировать категорию</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>

            <div class="modal-body">
              <form class="d-flex gap-2" @submit.prevent.stop="saveEdit">
                <input v-model="editForm.name" class="form-control" required />
                <button class="btn btn-primary" type="submit" data-bs-dismiss="modal">
                  Сохранить
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
