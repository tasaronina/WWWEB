<script setup>
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { computed, onBeforeMount } from "vue";
import { useUserStore } from "@/stores/user";
import "@/styles/admin.css";

const route = useRoute();
const router = useRouter();
const user = useUserStore();

onBeforeMount(() => user.init());

const showLogin = computed(() => user.ready && !user.isAuthenticated && route.path !== "/login");
const showLogout = computed(() => user.ready && user.isAuthenticated && route.path !== "/login");
const showUsername = computed(() => user.ready && user.isAuthenticated);

async function doLogout() {
  await user.logout();
  if (route.path !== "/login") router.replace("/login");
}
</script>

<template>
  <nav class="navbar bg-white border-bottom sticky-top">
    <div class="container-fluid px-4 py-2">
      <div class="d-flex gap-4">
        <RouterLink class="nav-link" to="/categories">Категории</RouterLink>
        <RouterLink class="nav-link" to="/menu">Меню</RouterLink>
        <RouterLink class="nav-link" to="/customers">Клиенты</RouterLink>
        <RouterLink class="nav-link" to="/orders">Заказы</RouterLink>
        <RouterLink class="nav-link" to="/order-items">Позиции заказа</RouterLink>
      </div>

      <div class="d-flex align-items-center gap-3">
        <span v-if="showUsername" class="badge rounded-pill text-bg-secondary">
          {{ user.username }}
        </span>
        <button v-if="showLogout" class="btn btn-outline-danger btn-sm" @click="doLogout">Выйти</button>
        <RouterLink v-if="showLogin" to="/login" class="btn btn-outline-primary btn-sm">Войти</RouterLink>
      </div>
    </div>
  </nav>

  <main class="container my-4">
    <RouterView />
  </main>
</template>
