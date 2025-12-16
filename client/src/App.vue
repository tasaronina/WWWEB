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
  <v-app>
    <v-app-bar flat>
      <v-container class="d-flex align-center">
        <v-toolbar-title class="me-6">
          <RouterLink to="/menu" style="text-decoration: none; color: inherit;">
            Кофейня
          </RouterLink>
        </v-toolbar-title>

        <div class="d-flex align-center ga-2 flex-wrap">
          <v-btn variant="text" to="/menu">Меню</v-btn>

          <v-btn v-if="isAdmin" variant="text" to="/categories">Категории</v-btn>
          <v-btn v-if="isAdmin" variant="text" to="/customers">Клиенты</v-btn>
          <v-btn v-if="isAdmin" variant="text" to="/orders">Заказы</v-btn>
          <v-btn v-if="isAdmin" variant="text" to="/order-items">Позиции заказов</v-btn>
        </div>

        <v-spacer />

        <div class="d-flex align-center">
          <v-menu v-if="isAuth" location="bottom end">
            <template #activator="{ props }">
              <v-btn v-bind="props" variant="text">
                Пользователь ({{ userInfo.username }})
              </v-btn>
            </template>

            <v-list>
              <v-list-item>
                <v-list-item-title>
                  <a href="/admin" style="text-decoration:none; color:inherit;">Админка</a>
                </v-list-item-title>
              </v-list-item>

              <v-list-item @click="handleLogout">
                <v-list-item-title>Выйти</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>

          <v-btn v-else-if="showLoginButton" variant="outlined" to="/login">
            Войти
          </v-btn>
        </div>
      </v-container>
    </v-app-bar>

    <v-main>
      <v-container class="py-6">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<style scoped></style>
