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
  <div class="container">
    <div class="d-flex justify-content-center align-items-center" style="min-height: calc(100vh - 80px);">
      <div style="width: 100%; max-width: 520px;">
        <h2 class="mb-3">Пожалуйста, авторизуйтесь</h2>

        <form @submit.stop.prevent="onLoginFormSubmit" class="d-flex flex-column" style="gap: 12px;">
          <input placeholder="логин" class="form-control" type="text" v-model="username" />
          <input placeholder="пароль" class="form-control" type="password" v-model="password" />
          <button class="btn btn-info">Войти</button>

          <div class="text-muted" style="font-size: 14px;">
            Админ увидит управление, пользователь — только меню и свои заказы.
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style></style>
