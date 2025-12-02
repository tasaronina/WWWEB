<template>
  <div class="container py-5" style="max-width: 520px;">
    <h1 class="mb-2 text-center">Вход</h1>
    <p class="text-muted text-center mb-4">Введите логин и пароль</p>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <form @submit.prevent="onSubmit" class="card p-4 shadow-sm">
      <div class="mb-3">
        <label class="form-label">Логин</label>
        <input v-model.trim="username" class="form-control" autocomplete="username" required />
      </div>

      <div class="mb-4">
        <label class="form-label">Пароль</label>
        <input v-model="password" type="password" class="form-control" autocomplete="current-password" required />
      </div>

      <button class="btn btn-primary w-100" :disabled="loading">
        {{ loading ? "Входим..." : "Войти" }}
      </button>
    </form>

    <!-- Модалка 2FA -->
    <OtpModal ref="otpRef" @success="onOtpSuccess" />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";
import api from "@/api";
import OtpModal from "@/components/auth/OtpModal.vue";

const router = useRouter();
const route = useRoute();
const store = useUserStore();

const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

const otpRef = ref(null);
let pendingNext = "/menu";

function getNextPath() {
  const qnext = route.query?.next;
  return (qnext && String(qnext)) || "/menu";
}

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    // логинимся и обновляем store
    const me = await store.login(username.value, password.value);
    if (!me?.authenticated) throw new Error("not-auth");

    // после логина проверяем статус 2FA
    const { data: st } = await api.get("/api/2fa/otp-status/");
    const confirmed = !!st?.confirmed;
    const ttl = Number(st?.ttl_seconds || 0);

    pendingNext = getNextPath();

    // если ещё не подтверждено ИЛИ доверенное окно истекло — просим код
    if (!confirmed || ttl <= 0) {
      otpRef.value?.show();
      return; // останемся на /login до успешного ввода
    }

    // 2FA ок — идём на next
    router.replace(pendingNext);
  } catch (e) {
    error.value = "Не удалось войти. Проверьте логин и пароль.";
  } finally {
    loading.value = false;
  }
}

function onOtpSuccess() {
  // после ввода верного кода — на next
  router.replace(pendingNext || "/menu");
}
</script>
