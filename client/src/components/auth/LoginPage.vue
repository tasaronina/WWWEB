<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-12 col-sm-10 col-md-8 col-lg-6 col-xl-5">
        <div class="card shadow-sm">
          <div class="card-body p-4">
            <h1 class="h2 text-center mb-2">Вход</h1>
            <p class="text-muted text-center mb-4">Введите логин и пароль</p>

            <div v-if="error" class="alert alert-danger">{{ error }}</div>

            <form @submit.prevent="onSubmit" autocomplete="on">
              <div class="mb-3">
                <label class="form-label">Логин</label>
                <input v-model.trim="username" type="text" class="form-control" required autofocus />
              </div>

              <div class="mb-4">
                <label class="form-label">Пароль</label>
                <input v-model="password" type="password" class="form-control" required />
              </div>

              <button class="btn btn-primary w-100" type="submit" :disabled="loading">
                {{ loading ? "Входим..." : "Войти" }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const route  = useRoute();
const store  = useUserStore();

const username = ref("");
const password = ref("");
const loading  = ref(false);
const error    = ref("");

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    // 1) пытаемся войти
    await store.login(username.value, password.value).catch(() => {});
    // 2) ОБЯЗАТЕЛЬНО сверяемся с сервером — действительно ли авторизованы
    await store.restore(true);

    if (store.isAuth) {
      const redirect = (route.query.redirect && String(route.query.redirect)) || "/menu";
      return router.replace(redirect);
    }
    error.value = "Не удалось войти. Проверьте логин и пароль.";
  } finally {
    loading.value = false;
  }
}
</script>
