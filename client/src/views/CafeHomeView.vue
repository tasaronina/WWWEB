<script setup>
import { computed, onBeforeMount, ref } from "vue";
import { storeToRefs } from "pinia";
import { useUserStore } from "@/stores/user_store";
import { useDataStore } from "@/stores/data_store";

const userStore = useUserStore();
const dataStore = useDataStore();

const { userInfo } = storeToRefs(userStore);
const { menu } = storeToRefs(dataStore);

const isAuthed = computed(() => !!userInfo.value?.is_authenticated);
const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const loginUsername = ref("");
const loginPassword = ref("");
const loginError = ref("");

const showAllMenu = ref(false);
const topMenu = computed(() => (menu.value || []).slice(0, 10));
const menuForShow = computed(() => (showAllMenu.value ? (menu.value || []) : topMenu.value));

onBeforeMount(async () => {
  await userStore.checkLogin();
  await dataStore.fetchMenu();
});

async function doLogin() {
  loginError.value = "";
  try {
    await userStore.login(loginUsername.value, loginPassword.value);
    // после логина обновляем инфу
    await userStore.checkLogin();
  } catch (e) {
    loginError.value = "Неверный логин или пароль (или не прошёл CSRF).";
  }
}

async function doLogout() {
  await userStore.logout();
  loginUsername.value = "";
  loginPassword.value = "";
}
</script>

<template>
  <div>
    <!-- Если не авторизован — модалка -->
    <div v-if="!isAuthed" class="position-fixed top-0 start-0 w-100 h-100" style="background: rgba(0,0,0,.55); z-index: 1050;">
      <div class="d-flex align-items-start justify-content-center" style="padding-top: 90px;">
        <div class="bg-white rounded-3 shadow p-4" style="width: 900px; max-width: calc(100% - 24px);">
          <h4 class="mb-3">Пожалуйста, авторизуйтесь</h4>

          <div v-if="loginError" class="alert alert-warning">{{ loginError }}</div>

          <form class="row g-2 align-items-center" @submit.prevent="doLogin">
            <div class="col-md-5">
              <input v-model="loginUsername" class="form-control" placeholder="Логин" autocomplete="username" required />
            </div>
            <div class="col-md-5">
              <input v-model="loginPassword" type="password" class="form-control" placeholder="Пароль" autocomplete="current-password" required />
            </div>
            <div class="col-md-2 d-grid">
              <button class="btn btn-primary" type="submit">Войти</button>
            </div>
          </form>

          <div class="text-muted mt-2">
            Админ увидит управление, пользователь — только меню и свои заказы.
          </div>
        </div>
      </div>
    </div>

    <!-- Контент страницы -->
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 class="mb-0">Кофейня</h2>
          <div class="text-muted">
            Статус:
            <span v-if="isAuthed">вошли как <b>{{ userInfo.username }}</b> ({{ isAdmin ? "админ" : "пользователь" }})</span>
            <span v-else>не авторизован</span>
          </div>
        </div>
        <button v-if="isAuthed" class="btn btn-outline-secondary" @click="doLogout">Выйти</button>
      </div>

      <div class="card">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
          <span>Меню (топ-10)</span>
          <button class="btn btn-sm btn-light" @click="showAllMenu = !showAllMenu">
            {{ showAllMenu ? "Скрыть лишнее" : "Открыть всё меню" }}
          </button>
        </div>

        <div class="card-body">
          <div v-if="menuForShow.length === 0" class="text-muted">Пока меню пустое</div>

          <div class="list-group" v-else>
            <div class="list-group-item d-flex justify-content-between align-items-center" v-for="m in menuForShow" :key="m.id">
              <div>
                <div class="fw-semibold">{{ m.title }}</div>
                <div class="text-muted small">{{ m.description }}</div>
              </div>
              <div class="text-end" style="min-width: 120px;">
                <div class="fw-semibold">{{ m.price }}</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>
