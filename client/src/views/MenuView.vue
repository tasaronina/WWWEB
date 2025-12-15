<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import axios from "axios";

import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { menu, categories } = storeToRefs(dataStore);

const createForm = ref({
  title: "",
  group: null,
  price: 0,
  description: "",
});

const editForm = ref({
  id: null,
  title: "",
  group: null,
  price: 0,
  description: "",
});

const cartQty = ref({});
const currentOrderId = ref(null);

const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

onBeforeMount(async () => {
  await userStore.checkLogin();
  await dataStore.fetchCategories();
  await dataStore.fetchMenu();
});

function groupNameById(id) {
  return (categories.value || []).find((c) => c.id === id)?.name || "—";
}

function openEdit(m) {
  editForm.value = {
    id: m.id,
    title: m.title || "",
    group: m.group ?? null,
    price: Number(m.price ?? 0),
    description: m.description || "",
  };
}

async function createItem() {
  const payload = {
    title: createForm.value.title,
    group: createForm.value.group,
    price: createForm.value.price,
    description: createForm.value.description,
  };
  await axios.post("/api/menu/", payload);
  createForm.value = { title: "", group: null, price: 0, description: "" };
  await dataStore.fetchMenu();
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  const payload = {
    title: editForm.value.title,
    group: editForm.value.group,
    price: editForm.value.price,
    description: editForm.value.description,
  };

  await axios.put(`/api/menu/${id}/`, payload);
  await dataStore.fetchMenu();
}

async function deleteItem(id) {
  if (!id) return;
  await axios.delete(`/api/menu/${id}/`);
  await dataStore.fetchMenu();
}

async function addToCart(menuId) {
  if (!userInfo.value?.is_authenticated) return;

  const qty = Math.max(1, Number(cartQty.value[menuId] || 1));
  const payload = {
    menu_id: menuId,
    qty,
    order_id: currentOrderId.value || undefined,
  };

  const r = await axios.post("/api/orders/add-to-cart/", payload);
  if (r?.data?.order_id) {
    currentOrderId.value = r.data.order_id;
  }
  cartQty.value[menuId] = 1;
}
</script>

<template>
  <div class="container mt-4">
    <div class="d-flex align-items-center justify-content-between mb-3">
      <h2 class="mb-0">Меню</h2>
      <div class="text-muted" v-if="userInfo?.is_authenticated">
        Роль: <strong>{{ userInfo.is_staff ? "Админ" : "Пользователь" }}</strong>
      </div>
    </div>


    <div class="card mb-4" v-if="isAdmin">
      <div class="card-header bg-primary text-white">
        Добавить позицию меню
      </div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="createItem">
          <div class="col-md-4">
            <input v-model="createForm.title" class="form-control" placeholder="Название" required />
          </div>

          <div class="col-md-3">
            <select v-model="createForm.group" class="form-select">
              <option :value="null">Без категории</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>

          <div class="col-md-2">
            <input v-model.number="createForm.price" class="form-control" type="number" step="0.01" placeholder="Цена" />
          </div>

          <div class="col-md-3">
            <input v-model="createForm.description" class="form-control" placeholder="Описание" />
          </div>

          <div class="col-12 text-end">
            <button class="btn btn-primary" type="submit">Добавить</button>
          </div>
        </form>
      </div>
    </div>


    <div class="card">
      <div class="card-header bg-body-tertiary d-flex justify-content-between align-items-center">
        <span>Список позиций</span>
        <span class="text-muted">Всего: {{ menu.length }}</span>
      </div>

      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-striped align-middle">
            <thead>
              <tr>
                <th style="width: 70px;">ID</th>
                <th>Название</th>
                <th style="width: 220px;">Категория</th>
                <th style="width: 140px;">Цена</th>
                <th style="width: 260px;">Действия</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="m in menu" :key="m.id">
                <td>{{ m.id }}</td>
                <td>
                  <div class="fw-semibold">{{ m.title }}</div>
                  <div class="text-muted small">{{ m.description }}</div>
                </td>
                <td>{{ groupNameById(m.group) }}</td>
                <td>{{ m.price }}</td>

                <td>
                  
                  <div v-if="userInfo?.is_authenticated && !isAdmin" class="d-flex gap-2">
                    <input
                      class="form-control form-control-sm"
                      type="number"
                      min="1"
                      style="width: 90px;"
                      v-model.number="cartQty[m.id]"
                      placeholder="qty"
                    />
                    <button class="btn btn-sm btn-success" @click="addToCart(m.id)">
                      Добавить
                    </button>
                  </div>

               
                  <div v-if="isAdmin" class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editMenuModal" @click="openEdit(m)">
                      Редактировать
                    </button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteItem(m.id)">
                      Удалить
                    </button>
                  </div>

                  <div v-if="!userInfo?.is_authenticated" class="text-muted small">
                    Войдите, чтобы добавлять в заказы
                  </div>
                </td>
              </tr>

              <tr v-if="menu.length === 0">
                <td colspan="5" class="text-center text-muted">Пока нет позиций меню</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="alert alert-info mt-3" v-if="userInfo?.is_authenticated && !isAdmin">
          <div>Если ты добавляешь позиции — они попадут в один “текущий заказ”.</div>
          <div class="small text-muted">order_id: {{ currentOrderId || "ещё не создан" }}</div>
        </div>
      </div>
    </div>


    <div class="modal fade" id="editMenuModal" tabindex="-1" aria-hidden="true" v-if="isAdmin">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Редактировать позицию меню</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"></button>
          </div>

          <div class="modal-body">
            <form class="row g-2" @submit.prevent.stop="saveEdit">
              <div class="col-md-6">
                <label class="form-label">Название</label>
                <input v-model="editForm.title" class="form-control" required />
              </div>

              <div class="col-md-6">
                <label class="form-label">Категория</label>
                <select v-model="editForm.group" class="form-select">
                  <option :value="null">Без категории</option>
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>

              <div class="col-md-4">
                <label class="form-label">Цена</label>
                <input v-model.number="editForm.price" type="number" step="0.01" class="form-control" />
              </div>

              <div class="col-md-8">
                <label class="form-label">Описание</label>
                <input v-model="editForm.description" class="form-control" />
              </div>

              <div class="col-12 text-end mt-2">
                <button class="btn btn-primary" type="submit" data-bs-dismiss="modal">
                  Сохранить
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>
