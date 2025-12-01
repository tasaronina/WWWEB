<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const user = useUserStore();

const username = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref("");

async function onSubmit(e) {
  e.preventDefault();
  submitting.value = true;
  error.value = "";
  const ok = await user.login({
    username: username.value.trim(),
    password: password.value,
  });
  submitting.value = false;
  if (ok) router.replace("/menu");
  else error.value = user.error || "Ошибка входа";
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <div class="auth-card-body">
        
        <div class="form-wrap">
          <h1 class="h2 fw-bold text-center mb-2">Вход</h1>
          <p class="text-center text-muted mb-4">Введите логин и пароль</p>

          <form @submit="onSubmit" class="vstack gap-3">
            <div>
              <label class="form-label">Логин</label>
              <input
                v-model="username"
                type="text"
                class="form-control form-control-lg"
                autocomplete="username"
              />
            </div>

            <div>
              <label class="form-label">Пароль</label>
              <input
                v-model="password"
                type="password"
                class="form-control form-control-lg"
                autocomplete="current-password"
              />
            </div>

            <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

            <button class="btn btn-primary btn-lg w-100" :disabled="submitting">
              {{ submitting ? "Входим..." : "Войти" }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Экран */
.auth-screen {
  min-height: calc(100dvh - 80px);
  display: grid;
  place-items: center;
  padding: clamp(16px, 4vw, 40px);
}

/* Карточка */
.auth-card {
  width: min(32vw, 980px);
  border-radius: 20px;
  background: #fff;
  box-shadow:
    0 30px 60px rgba(0,0,0,.1),
    0 1px 0 rgba(0,0,0,.04) inset;
}

.auth-card-body {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: clamp(24px, 4vw, 48px);
}


.form-wrap {
  max-width: 220px;    
  width: 100%;
  margin: 0 auto;     
  text-align: left;
}

/* Сглаживание */
:deep(.form-control-lg) {
  min-height: 48px;
  border-radius: 12px;
}
:deep(.btn-lg) {
  border-radius: 12px;
}
</style>
