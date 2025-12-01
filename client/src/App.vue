<!-- client/src/App.vue -->
<template>
  <!-- Скрываем шапку на странице логина -->
  <header v-if="!isLogin" class="navbar navbar-light bg-white border-bottom mb-3">
    <div class="container d-flex align-items-center justify-content-between">
      <router-link class="navbar-brand fw-semibold text-decoration-none" to="/menu">
        Кофейня
      </router-link>

      <nav class="d-flex gap-4 align-items-center">
        <router-link class="nav-link" to="/menu">Меню</router-link>

        <!-- У админа — админ-пункты; у обычного — 'Мои заказы' -->
        <template v-if="isAdmin">
          <router-link class="nav-link" to="/categories">Категории</router-link>
          <router-link class="nav-link" to="/customers">Клиенты</router-link>
          <router-link class="nav-link" to="/orders">Заказы (админ)</router-link>
          <router-link class="nav-link" to="/order-items">Позиции заказов</router-link>
        </template>
        <router-link v-else class="nav-link" to="/my-orders">Мои заказы</router-link>

        <!-- Правый угол: ник и кнопка -->
        <div class="d-flex align-items-center gap-3">
          <span v-if="isAuth" class="text-muted">{{ username }}</span>
          <button
            v-if="isAuth"
            class="btn btn-outline-primary btn-sm"
            @click="onLogout"
          >
            Выйти
          </button>
          <router-link v-else class="btn btn-outline-primary btn-sm" to="/login">
            Войти
          </router-link>
        </div>
      </nav>
    </div>
  </header>

  <router-view />
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";

const route = useRoute();
const store = useUserStore();

const isLogin = computed(() => route.path === "/login");
const isAuth = computed(() => store.isAuth);
const isAdmin = computed(() => store.isAdmin);
const username = computed(() => store.username);

async function onLogout() {
  await store.logout(); // внутри стор сразу делает router.replace("/login")
}
</script>

<style scoped>
.nav-link.router-link-active {
  padding: .35rem .8rem;
  border-radius: .6rem;
  background: #eef4ff;
}
</style>
