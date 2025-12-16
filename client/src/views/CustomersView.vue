<script setup>
import { onBeforeMount, ref } from "vue";
import axios from "axios";
import { useUserStore } from "@/stores/user_store";
import QRCode from "qrcode";

const userStore = useUserStore();

const items = ref([]);
const stats = ref(null);

const userInfo = ref({
  is_authenticated: false,
  is_staff: false,
  second: false,
});

const filters = ref({
  name: "",
  phone: "",
});

const createForm = ref({
  name: "",
  phone: "",
});

const editForm = ref({
  id: null,
  name: "",
  phone: "",
});

const totpDialogVisible = ref(false);
const totpUrl = ref("");
const qrDataUrl = ref("");
const totpCode = ref("");
const totpError = ref(false);
const pendingDeleteId = ref(null);

async function buildQr(u) {
  if (!u) {
    qrDataUrl.value = "";
    return;
  }

  qrDataUrl.value = await QRCode.toDataURL(u, {
    width: 220,
    margin: 1,
  });
}

async function fetchUserInfo() {
  const r = await axios.get("/api/user/info/");
  userInfo.value = r.data || userInfo.value;
}

async function fetchItems() {
  const r = await axios.get("/api/customers/", { params: filters.value });
  items.value = r.data || [];
}

async function fetchStats() {
  const r = await axios.get("/api/customers/stats/", { params: filters.value });
  stats.value = r.data;
}

async function applyFilters() {
  await fetchItems();
  await fetchStats();
}

async function createItem() {
  if (!createForm.value.name) return;

  await axios.post("/api/customers/", {
    name: createForm.value.name,
    phone: createForm.value.phone || "",
  });

  createForm.value = { name: "", phone: "" };
  await applyFilters();
}

function openEdit(c) {
  editForm.value = {
    id: c.id,
    name: c.name,
    phone: c.phone || "",
  };
}

async function saveEdit() {
  const id = editForm.value.id;
  if (!id) return;

  await axios.put(`/api/customers/${id}/`, {
    name: editForm.value.name,
    phone: editForm.value.phone || "",
  });

  await applyFilters();
}

async function openTotpDialog(deleteId) {
  pendingDeleteId.value = deleteId;
  totpDialogVisible.value = true;
  totpError.value = false;
  totpCode.value = "";
  totpUrl.value = "";
  qrDataUrl.value = "";

  const u = await userStore.getTotp();
  totpUrl.value = u || "";
  await buildQr(totpUrl.value);
}

function closeTotpDialog() {
  totpDialogVisible.value = false;
  totpError.value = false;
  totpCode.value = "";
  totpUrl.value = "";
  qrDataUrl.value = "";
  pendingDeleteId.value = null;
}

async function confirmTotpAndDelete() {
  totpError.value = false;

  const ok = await userStore.verifyTotp(totpCode.value);
  await fetchUserInfo();

  if (!ok) {
    totpError.value = true;
    totpCode.value = "";
    return;
  }

  const id = pendingDeleteId.value;

  closeTotpDialog();

  if (id) {
    await axios.delete(`/api/customers/${id}/`);
    await applyFilters();
  }
}

async function deleteItem(id) {
  if (userInfo.value.is_staff && !userInfo.value.second) {
    await openTotpDialog(id);
    return;
  }

  await axios.delete(`/api/customers/${id}/`);
  await applyFilters();
}

onBeforeMount(async () => {
  await fetchUserInfo();
  await applyFilters();
});
</script>

<template>
  <div class="container mt-4">
    <h2 class="mb-3">Клиенты</h2>

    <div class="d-flex justify-content-between align-items-center mb-2">
      <div class="text-muted" v-if="stats">
        Всего клиентов: <b>{{ stats.total }}</b>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Добавить клиента</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="createItem">
          <div class="col-md-6">
            <label class="form-label">ФИО</label>
            <input class="form-control" v-model="createForm.name" />
          </div>

          <div class="col-md-4">
            <label class="form-label">Телефон</label>
            <input class="form-control" v-model="createForm.phone" />
          </div>

          <div class="col-md-2 d-flex align-items-end justify-content-end">
            <button class="btn btn-primary">Добавить</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-header">Фильтры</div>
      <div class="card-body">
        <form class="row g-2" @submit.prevent="applyFilters">
          <div class="col-md-5">
            <label class="form-label">ФИО</label>
            <input class="form-control" v-model="filters.name" />
          </div>
          <div class="col-md-5">
            <label class="form-label">Телефон</label>
            <input class="form-control" v-model="filters.phone" />
          </div>
          <div class="col-md-2 d-flex align-items-end justify-content-end">
            <button class="btn btn-primary">Применить</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card">
      <div class="card-header">Таблица</div>
      <div class="card-body table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th style="width: 90px;">ID</th>
              <th>ФИО</th>
              <th style="width: 240px;">Телефон</th>
              <th style="width: 220px;">Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="c in items" :key="c.id">
              <td>#{{ c.id }}</td>
              <td>{{ c.name }}</td>
              <td>{{ c.phone }}</td>
              <td class="d-flex gap-2">
                <button
                  class="btn btn-sm btn-outline-secondary"
                  data-bs-toggle="modal"
                  data-bs-target="#editCustomerModal"
                  @click="openEdit(c)"
                >
                  Редактировать
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteItem(c.id)">
                  Удалить
                </button>
              </td>
            </tr>

            <tr v-if="items.length === 0">
              <td colspan="4" class="text-muted text-center">Нет данных</td>
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
            <form class="d-flex flex-column" style="gap: 10px;" @submit.prevent.stop="saveEdit">
              <div>
                <label class="form-label">ФИО</label>
                <input class="form-control" v-model="editForm.name" />
              </div>

              <div>
                <label class="form-label">Телефон</label>
                <input class="form-control" v-model="editForm.phone" />
              </div>

              <div class="text-end">
                <button class="btn btn-primary" type="submit" data-bs-dismiss="modal">
                  Сохранить
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>

    <div
      v-if="totpDialogVisible"
      class="modal fade show"
      style="display: block;"
      tabindex="-1"
      aria-modal="true"
      role="dialog"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">2FA подтверждение</h5>
            <button type="button" class="btn-close" @click="closeTotpDialog"></button>
          </div>

          <div class="modal-body d-flex flex-column" style="gap: 12px;">
            <div class="text-muted" style="font-size: 14px;">
              Отсканируйте QR-код и введите код.
            </div>

            <div class="d-flex justify-content-center" v-if="qrDataUrl">
              <img :src="qrDataUrl" alt="QR" style="width: 220px; height: 220px;" />
            </div>

            <div v-if="!qrDataUrl" class="text-muted" style="font-size: 14px;">
              Не удалось получить QR. Обновите страницу и попробуйте снова.
            </div>

            <input class="form-control" placeholder="код из приложения" v-model="totpCode" />

            <div v-if="totpError" class="text-danger" style="font-size: 14px;">
              Неверный код
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" @click="closeTotpDialog">Отмена</button>
            <button class="btn btn-danger" type="button" @click="confirmTotpAndDelete">Удалить</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="totpDialogVisible" class="modal-backdrop fade show"></div>
  </div>
</template>

<style></style>
