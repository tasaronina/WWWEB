<script setup>
import { computed } from "vue";
import { useUserStore } from "@/stores/user_store";
import { storeToRefs } from "pinia";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();

const userStore = useUserStore();
const { userInfo } = storeToRefs(userStore);

const isAuth = computed(() => !!userInfo.value?.is_authenticated);
const isAdmin = computed(() => !!userInfo.value?.is_authenticated && !!userInfo.value?.is_staff);

const showLoginButton = computed(() => !isAuth.value && route.name !== "Login");

async function handleLogout() {
  await userStore.logout();
  router.push("/login");
}
</script>

<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
    <div class="container">
      <router-link class="navbar-brand" to="/menu">Кофейня</router-link>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
      
          <li class="nav-item">
            <router-link class="nav-link" to="/menu">Меню</router-link>
          </li>

          <li v-if="isAdmin" class="nav-item">
            <router-link class="nav-link" to="/categories">Категории</router-link>
          </li>
          <li v-if="isAdmin" class="nav-item">
            <router-link class="nav-link" to="/customers">Клиенты</router-link>
          </li>
          <li v-if="isAdmin" class="nav-item">
            <router-link class="nav-link" to="/orders">Заказы</router-link>
          </li>
          <li v-if="isAdmin" class="nav-item">
            <router-link class="nav-link" to="/order-items">Позиции заказов</router-link>
          </li>

          
        </ul>

        <ul class="navbar-nav">
          <li v-if="isAuth" class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
              Пользователь ({{ userInfo.username }})
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><a class="dropdown-item" href="/admin">Админка</a></li>
              <li><a class="dropdown-item" href="#" @click.prevent="handleLogout">Выйти</a></li>
            </ul>
          </li>

          <li v-else-if="showLoginButton" class="nav-item">
            <router-link class="btn btn-outline-primary" to="/login">Войти</router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>

  <div class="container">
    <router-view />
  </div>
</template>

<style scoped></style>
