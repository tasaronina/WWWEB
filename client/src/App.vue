<template>
  <div>
    <!-- шапка скрыта на /login -->
    <header v-if="route.path !== '/login'" class="border-bottom bg-white">
      <div class="container d-flex align-items-center justify-content-between py-2">
        <!-- Бренд -->
        <RouterLink :to="{name:'menu'}" class="text-decoration-none fw-semibold text-dark">
          Кофейня
        </RouterLink>

        <!-- Навигация -->
        <nav class="d-flex align-items-center gap-3">
          <RouterLink
            :to="{name:'menu'}"
            class="btn btn-link px-2 py-1"
            :class="{ 'fw-semibold': route.name === 'menu' }"
          >
            Меню
          </RouterLink>

          <!-- пользователь -->
          <RouterLink
            v-if="store.isAuthed && !isAdmin"
            :to="{name:'my-orders'}"
            class="btn btn-link px-2 py-1"
            :class="{ 'fw-semibold': route.name === 'my-orders' }"
          >
            Мои заказы
          </RouterLink>

          <!-- админ -->
          <RouterLink
            v-if="store.isAuthed && isAdmin"
            :to="{name:'orders'}"
            class="btn btn-link px-2 py-1"
            :class="{ 'fw-semibold': route.name === 'orders' }"
          >
            Заказы (админ)
          </RouterLink>
          <RouterLink
            v-if="store.isAuthed && isAdmin"
            :to="{name:'categories'}"
            class="btn btn-link px-2 py-1"
            :class="{ 'fw-semibold': route.name === 'categories' }"
          >
            Категории
          </RouterLink>
          <RouterLink
            v-if="store.isAuthed && isAdmin"
            :to="{name:'customers'}"
            class="btn btn-link px-2 py-1"
            :class="{ 'fw-semibold': route.name === 'customers' }"
          >
            Клиенты
          </RouterLink>
          <RouterLink
            v-if="store.isAuthed && isAdmin"
            :to="{name:'order-items'}"
            class="btn btn-link px-2 py-1"
            :class="{ 'fw-semibold': route.name === 'order-items' }"
          >
            Позиции заказов
          </RouterLink>
        </nav>

        <!-- Имя + вход/выход -->
        <div class="d-flex align-items-center gap-3">
          <span v-if="store.isAuthed" class="text-muted">{{ store.username }}</span>

          <button
            v-if="store.isAuthed"
            type="button"
            class="btn btn-outline-primary btn-sm"
            @click="onLogout"
          >
            Выйти
          </button>

          <RouterLink v-else :to="{name:'login'}" class="btn btn-outline-primary btn-sm">
            Войти
          </RouterLink>
        </div>
      </div>
    </header>

    <RouterView :key="route.fullPath" />
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";

const store = useUserStore();
const route = useRoute();

onMounted(() => {
  if (!store.ready) store.restore().catch(() => {});
});

const isAdmin = computed(() => Boolean(store.user?.is_staff || store.user?.is_superuser));

function onLogout() {
  store.logout();
}
</script>

<style scoped>
.fw-semibold { font-weight: 600; }
</style>
