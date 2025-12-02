
<template>
  <div class="container my-5" style="max-width: 820px;">
    <h1 class="display-5 fw-bold text-center mb-2">Вход</h1>
    <p class="text-center text-muted mb-4">Введите логин и пароль</p>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="card shadow-sm">
      <div class="card-body p-4">
        <form @submit.prevent="onSubmit">
          <div class="row g-3">
            <div class="col-md-6 offset-md-3">
              <label class="form-label">Логин</label>
              <input v-model="form.username" class="form-control" autocomplete="username" />
            </div>
            <div class="col-md-6 offset-md-3">
              <label class="form-label">Пароль</label>
              <input v-model="form.password" type="password" class="form-control" autocomplete="current-password" />
            </div>
            <div class="col-md-6 offset-md-3 d-grid mt-3">
              <button class="btn btn-primary btn-lg" :disabled="loading">
                {{ loading ? "Входим..." : "Войти" }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

   
    <div class="modal fade" tabindex="-1" ref="otpModalRef">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 v-if="otpMode==='verify'" class="modal-title">Подтверждение входа (2FA)</h5>
            <h5 v-else class="modal-title">Привязка 2FA</h5>
            <button type="button" class="btn-close" @click="closeOtp"></button>
          </div>

          <div class="modal-body">
            
            <template v-if="otpMode==='setup'">
              <p class="mb-2">Секрет для приложения-аутентификатора:</p>
              <div class="p-2 bg-light border rounded fw-semibold text-monospace user-select-all">
                {{ otpSecretData?.secret }}
              </div>
              <p class="mt-3 mb-1">Отсканируйте QR/URI в приложении (Google Authenticator, Aegis и т.д.):</p>
              <div class="small text-break">{{ otpSecretData?.otpauth_url }}</div>
              <hr />
              <p class="mb-2">После добавления введите 6-значный код:</p>
              <input v-model="otpCode" maxlength="6" class="form-control" placeholder="Например, 123456" />
              <div v-if="otpError" class="text-danger small mt-2">{{ otpError }}</div>
            </template>

            
            <template v-else>
              <p class="mb-2">Введите 6-значный код из приложения-аутентификатора:</p>
              <input v-model="otpCode" maxlength="6" class="form-control" placeholder="Код 2FA" />
              <div v-if="otpError" class="text-danger small mt-2">{{ otpError }}</div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" @click="closeOtp">Отмена</button>
            <button class="btn btn-primary" type="button" :disabled="otpLoading" @click="submitOtp">
              {{ otpLoading ? "Проверяем..." : "Подтвердить" }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "@/styles/admin.css";

import { login as apiLogin, me, otpStatus, otpSecret as apiOtpSecret, otpLogin } from "@/api";

const router = useRouter();
const route = useRoute();

const form = ref({ username: "", password: "" });
const loading = ref(false);
const error = ref("");


const otpModalRef = ref(null);
let otpModal = null;
const otpMode = ref("verify");        
const otpCode = ref("");
const otpLoading = ref(false);
const otpError = ref("");
const otpSecretData = ref(null);

function openOtp() {
  if (!otpModal && otpModalRef.value) {
    otpModal = window.bootstrap.Modal.getOrCreateInstance(otpModalRef.value, { backdrop: "static" });
  }
  otpError.value = "";
  otpCode.value = "";
  otpModal?.show();
}
function closeOtp() {
  otpModal?.hide();
}

async function afterLogin2FA() {
  
  const st = await otpStatus();

  if (!st.confirmed) {
    otpMode.value = "setup";
    otpSecretData.value = await apiOtpSecret(); 
    openOtp();
    return;
  }
 
  if (!st.otp_good) {
    otpMode.value = "verify";
    openOtp();
    return;
  }
 
  goNext();
}

function goNext() {
  const next = (route.query.next && String(route.query.next)) || "/menu";
  router.replace(next);
}

async function submitOtp() {
  otpLoading.value = true;
  otpError.value = "";
  try {
    const code = otpCode.value.replace(/\s+/g, "");
    if (!/^\d{6}$/.test(code)) {
      otpError.value = "Введите 6-значный код.";
      return;
    }
    const res = await otpLogin(code); 
    if (!res || (res.success === false)) {
      otpError.value = "Неверный код. Попробуйте ещё раз.";
      return;
    }
    closeOtp();
    goNext();
  } catch (e) {
    otpError.value = "Не удалось подтвердить код.";
  } finally {
    otpLoading.value = false;
  }
}

async function onSubmit() {
  loading.value = true;
  error.value = "";
  try {
    const resp = await apiLogin(form.value.username.trim(), form.value.password);
    const ok = !!(resp && (resp.ok || resp.success));
    if (!ok) throw new Error("bad creds");

  
    await me();

 
    await afterLogin2FA();
  } catch (_) {
    error.value = "Не удалось войти. Проверьте логин и пароль.";
  } finally {
    loading.value = false;
  }
}
</script>
