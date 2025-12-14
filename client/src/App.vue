<template>
  <v-app>
    <v-app-bar density="comfortable" v-if="appReady && route.path !== '/login'">
      <v-container class="d-flex align-center justify-space-between" fluid>
        <RouterLink :to="{name:'menu'}" class="text-high-emphasis text-decoration-none">
          <span class="text-h6">Кофейня</span>
        </RouterLink>
        <div class="d-flex align-center ga-2">
          <v-btn variant="text" :to="{name:'menu'}" :class="{ 'font-weight-bold': route.name==='menu' }">Меню</v-btn>
          <v-btn v-if="store.isAuthed && !isAdmin" variant="text" :to="{name:'my-orders'}" :class="{ 'font-weight-bold': route.name==='my-orders' }">Мои заказы</v-btn>
          <v-btn v-if="store.isAuthed && isAdmin" variant="text" :to="{name:'orders'}" :class="{ 'font-weight-bold': route.name==='orders' }">Заказы (админ)</v-btn>
          <v-btn v-if="store.isAuthed && isAdmin" variant="text" :to="{name:'categories'}" :class="{ 'font-weight-bold': route.name==='categories' }">Категории</v-btn>
          <v-btn v-if="store.isAuthed && isAdmin" variant="text" :to="{name:'customers'}" :class="{ 'font-weight-bold': route.name==='customers' }">Клиенты</v-btn>
          <v-btn v-if="store.isAuthed && isAdmin" variant="text" :to="{name:'order-items'}" :class="{ 'font-weight-bold': route.name==='order-items' }">Позиции заказов</v-btn>
        </div>
        <div class="d-flex align-center ga-3">
          <span v-if="store.isAuthed" class="text-medium-emphasis">{{ store.username }}</span>
          <v-btn v-if="store.isAuthed" color="primary" variant="outlined" size="small" @click="onLogout">Выйти</v-btn>
          <v-btn v-else color="primary" variant="outlined" size="small" :to="{name:'login'}">Войти</v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main>
      <div v-if="!appReady" class="pa-6">
        <v-progress-linear indeterminate />
      </div>
      <RouterView v-else :key="route.fullPath" />
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const route = useRoute()

const appReady = ref(false)
onMounted(async () => {
  try { await store.restore() } finally { appReady.value = true }
})

const isAdmin = computed(() => Boolean(store.user?.is_staff || store.user?.is_superuser))
function onLogout(){ store.logout() }
</script>

<style scoped>
.text-decoration-none{ text-decoration: none }
.font-weight-bold{ font-weight: 600 }
</style>
