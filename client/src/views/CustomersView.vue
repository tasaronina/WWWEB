<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { customers } = storeToRefs(dataStore);

const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const createForm = ref({
  name: "",
  phone: "",
  email: "",
});

const editForm = ref({
  id: null,
  name: "",
  phone: "",
  email: "",
});

onBeforeMount(async () => {
  await userStore.checkLogin();
  if (isAdmin.value) {
    await dataStore.fetchCustomers();
  }
});

async function createCustomer() {
  await axios.post("/api/customers/", createForm.value);
  createForm.value = { name: "", phone: "", email: "" };
  await dataStore.fetchCustomers();
}

function openEdit(c) {
  editForm.value = {
    id: c.id,
    name: c.name || "",
    phone: c.phone || "",
    email: c.email || "",
  };
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/customers/${id}/`, {
    name: editForm.value.name,
    phone: editForm.value.phone,
    email: editForm.value.email,
  });
  await dataStore.fetchCustomers();
}

async function deleteCustomer(id) {
  await axios.delete(`/api/customers/${id}/`);
  await dataStore.fetchCustomers();
}
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Клиенты</h2>

    <div v-if="!isAdmin" class="alert alert-danger">
      Доступно только администратору.
    </div>

    <div v-else>
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">Добавить клиента</div>
        <div class="card-body">
          <form class="row g-2" @submit.prevent="createCustomer">
            <div class="col-md-4">
              <input v-model="createForm.name" class="form-control" placeholder="ФИО" required />
            </div>
            <div class="col-md-4">
              <input v-model="createForm.phone" class="form-control" placeholder="Телефон" />
            </div>
            <div class="col-md-4">
              <input v-model="createForm.email" class="form-control" placeholder="Email" />
            </div>
            <div class="col-12 text-end">
              <button class="btn btn-primary" type="submit">Добавить</button>
            </div>
          </form>
        </div>
      </div>

      <div class="card">
        <div class="card-header bg-body-tertiary d-flex justify-content-between">
          <span>Список клиентов</span>
          <span class="text-muted">Всего: {{ customers.length }}</span>
        </div>

        <div class="card-body table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th style="width: 80px;">ID</th>
                <th>ФИО</th>
                <th style="width: 180px;">Телефон</th>
                <th style="width: 240px;">Email</th>
                <th style="width: 220px;">Действия</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="c in customers" :key="c.id">
                <td>{{ c.id }}</td>
                <td class="fw-semibold">{{ c.name }}</td>
                <td>{{ c.phone || "—" }}</td>
                <td>{{ c.email || "—" }}</td>
                <td class="d-flex gap-2">
                  <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editCustomerModal" @click="openEdit(c)">
                    Редактировать
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteCustomer(c.id)">
                    Удалить
                  </button>
                </td>
              </tr>

              <tr v-if="customers.length === 0">
                <td colspan="5" class="text-center text-muted">Пока клиентов нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="modal fade" id="editCustomerModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Редактировать клиента</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>

            <div class="modal-body">
              <form class="row g-2" @submit.prevent.stop="saveEdit">
                <div class="col-12">
                  <label class="form-label">ФИО</label>
                  <input v-model="editForm.name" class="form-control" required />
                </div>
                <div class="col-12">
                  <label class="form-label">Телефон</label>
                  <input v-model="editForm.phone" class="form-control" />
                </div>
                <div class="col-12">
                  <label class="form-label">Email</label>
                  <input v-model="editForm.email" class="form-control" />
                </div>
                <div class="col-12 text-end">
                  <button class="btn btn-primary" type="submit" data-bs-dismiss="modal">Сохранить</button>
                </div>
              </form>
            </div>

          </div>
        </div>
      </div>

    </div>
  </div>
</template>
