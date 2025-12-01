<!-- client/src/components/auth/LoginPage.vue -->
<template>
  <div class="container-fluid min-vh-100 d-flex align-items-center">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12 col-sm-10 col-md-7 col-lg-5 col-xl-4">
          <div class="card shadow-sm">
            <div class="card-body p-4">
              <h1 class="h2 text-center mb-2">Вход</h1>
              <p class="text-muted text-center mb-4">Введите логин и пароль</p>

              <div class="mx-auto" style="max-width: 260px;">
                <div v-if="error" class="alert alert-danger">{{ error }}</div>

                <form @submit.prevent="onSubmit" autocomplete="on">
                  <div class="mb-3">
                    <label class="form-label">Логин</label>
                    <input
                      v-model.trim="username"
                      type="text"
                      class="form-control w-100"
                      required
                      autofocus
                    />
                  </div>

                  <div class="mb-4">
                    <label class="form-label">Пароль</label>
                    <input
                      v-model="password"
                      type="password"
                      class="form-control w-100"
                      required
                    />
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
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const store = useUserStore();

const username = ref("");
const password = ref("");
const loading  = ref(false);
const error    = ref("");

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await store.login(username.value, password.value);
    // После входа — просто на /menu (и у админа, и у пользователя)
    await router.replace("/menu");
  } catch {
    error.value = "Не удалось войти. Проверьте логин и пароль.";
  } finally {
    loading.value = false;
  }
}
</script>
