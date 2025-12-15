<script setup>
import axios from "axios";
import Cookies from "js-cookie";
import { onBeforeMount } from "vue";
import { useUserStore } from "@/stores/user_store";
import { storeToRefs } from "pinia";

const userStore = useUserStore();
const { userInfo } = storeToRefs(userStore);

async function handleLogout() {
  await userStore.logout();
}


onBeforeMount(() => {
  axios.defaults.headers.common['X-CSRFToken'] = Cookies.get("csrftoken");
})

</script>

<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
    <div class="container">
      <router-link class="navbar-brand" to="/">Кофейня</router-link>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/">Главная</router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/menu">Меню</router-link>
          </li>

          <li v-if="userInfo && userInfo.is_authenticated && userInfo.is_staff" class="nav-item">
            <router-link class="nav-link" to="/categories">Категории</router-link>
          </li>

          <li v-if="userInfo && userInfo.is_authenticated && userInfo.is_staff" class="nav-item">
            <router-link class="nav-link" to="/customers">Клиенты</router-link>
          </li>

          <li v-if="userInfo && userInfo.is_authenticated" class="nav-item">
            <router-link class="nav-link" to="/orders">Заказы</router-link>
          </li>

          <li v-if="userInfo && userInfo.is_authenticated && userInfo.is_staff" class="nav-item">
            <router-link class="nav-link" to="/order-items">Позиции заказов</router-link>
          </li>
        </ul>

        <ul class="navbar-nav">
          <li v-if="userInfo && userInfo.is_authenticated" class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Пользователь
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li>
                <a class="dropdown-item" href="/admin">Админка</a>
              </li>
              <li>
                <a class="dropdown-item" href="#" @click.prevent="handleLogout">Выйти</a>
              </li>
            </ul>
          </li>

          <li v-else class="nav-item">
            <span class="nav-link text-muted">Не авторизован</span>
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
