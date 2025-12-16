<script setup>
import { ref, onBeforeMount } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user_store";
import { storeToRefs } from "pinia";

const router = useRouter();

const username = ref("");
const password = ref("");

const userStore = useUserStore();
const { userInfo } = storeToRefs(userStore);

async function onLoginFormSubmit() {
  await axios.post("/api/user/login/", {
    username: username.value,
    password: password.value,
  });

  password.value = "";
  username.value = "";

  await userStore.fetchUserInfo();

  if (userInfo.value?.is_authenticated) {
    router.push("/menu");
  }
}

onBeforeMount(async () => {
  await userStore.fetchUserInfo();

  if (userInfo.value?.is_authenticated) {
    router.push("/menu");
  }
});
</script>

<template>
  <div class="d-flex justify-center align-center" style="min-height: calc(100vh - 120px);">
    <v-card style="width: 100%; max-width: 520px;" variant="flat" border>
      <v-card-title class="text-h6">Пожалуйста, авторизуйтесь</v-card-title>

      <v-card-text>
        <v-form @submit.prevent="onLoginFormSubmit">
          <v-text-field
            v-model="username"
            label="Логин"
            variant="outlined"
            density="comfortable"
          />
          <v-text-field
            v-model="password"
            label="Пароль"
            type="password"
            variant="outlined"
            density="comfortable"
          />

          <v-btn type="submit" color="primary" block>
            Войти
          </v-btn>

          <div class="text-medium-emphasis mt-3" style="font-size: 14px;">
            Админ увидит управление, пользователь — только меню и свои заказы.
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<style></style>
