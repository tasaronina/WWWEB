<template>
  <div class="modal fade" tabindex="-1" ref="modalEl">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <!-- novalidate: отключаем нативную блокировку сабмита, валидируем сами -->
        <form @submit.prevent="submit" novalidate>
          <div class="modal-header">
            <h5 class="modal-title">Двойная авторизация</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">
            <p class="text-muted mb-3">Введите 6-значный код из приложения.</p>

            <!-- Подсказка для первичной привязки -->
            <div v-if="secretInfo" class="alert alert-info py-2">
              <div class="small">
                Секрет для привязки: <code>{{ secretInfo.secret }}</code>
                <button class="btn btn-link btn-sm p-0 ms-1" type="button" @click="copySecret">копировать</button>
              </div>
              <div class="small">
                Можно добавить по ссылке:
                <a :href="secretInfo.otpauth_url" target="_blank" rel="noopener">otpauth_url</a>
              </div>
            </div>

            <input
              v-model="code"
              @input="onCodeInput"
              type="text"
              inputmode="numeric"
              autocomplete="one-time-code"
              name="otp"
              pattern="[0-9]{6}"
              maxlength="6"
              class="form-control text-center"
              placeholder="••••••"
              required
            />

            <div v-if="error" class="alert alert-danger py-2 px-3 mt-3">{{ error }}</div>

            <div class="d-flex gap-2 mt-2">
              <button type="button" class="btn btn-outline-secondary btn-sm" @click="otpReset" :disabled="loading">
                Перепривязать приложение
              </button>
              <small class="text-muted ms-auto" v-if="ttlLeft > 0">
                Доверено ещё: {{ ttlLeft }}&nbsp;с
              </small>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Отмена</button>
            <button class="btn btn-primary" type="submit" :disabled="loading || code.length !== 6">
              {{ loading ? "Проверяем..." : "Подтвердить" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import api, { ensureCsrf } from "@/api";

const emit = defineEmits(["success"]);

const modalEl = ref(null);
let modal = null;

const code = ref("");
const loading = ref(false);
const error = ref("");
const ttlLeft = ref(0);
const secretInfo = ref(null); // {secret, otpauth_url}

let timer = null;

onMounted(() => {
  if (modalEl.value && window.bootstrap) {
    modal = window.bootstrap.Modal.getOrCreateInstance(modalEl.value, {
      backdrop: "static",
      keyboard: false,
    });
  }
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});

function onCodeInput(e) {
  // оставляем только цифры и режем до 6 символов
  const onlyDigits = String(e.target.value || "").replace(/\D/g, "").slice(0, 6);
  code.value = onlyDigits;
}

function show() {
  code.value = "";
  error.value = "";
  loading.value = false;
  ttlLeft.value = 0;
  secretInfo.value = null;
  preloadSecretIfNeeded(); // получим секрет только если НЕ подтверждено
  modal?.show();
}

async function preloadSecretIfNeeded() {
  try {
    const st = await api.get("/api/2fa/otp-status/");
    const confirmed = !!st?.data?.confirmed;
    const ttl = Number(st?.data?.ttl_seconds || 0);
    ttlLeft.value = Math.max(0, ttl);
    // секрет показываем ТОЛЬКО если ещё не подтверждено
    if (!confirmed) {
      const { data } = await api.get("/api/2fa/otp-secret/");
      if (data?.secret) secretInfo.value = data;
    }
  } catch {
    /* игнорируем */
  }
}

async function submit() {
  if (code.value.length !== 6) return; // простая защита
  error.value = "";
  loading.value = true;
  try {
    await ensureCsrf();
    const { data } = await api.post("/api/2fa/otp-login/", {
      key: code.value,
    });
    if (!data?.success) throw new Error("bad otp");

    ttlLeft.value = Number(data.ttl_seconds || 0);
    if (timer) clearInterval(timer);
    if (ttlLeft.value > 0) {
      timer = setInterval(() => {
        ttlLeft.value = Math.max(0, ttlLeft.value - 1);
        if (ttlLeft.value === 0) { clearInterval(timer); timer = null; }
      }, 1000);
    }
    modal?.hide();
    emit("success");
  } catch {
    error.value = "Неверный код. Попробуйте ещё раз.";
    code.value = "";
  } finally {
    loading.value = false;
  }
}

async function otpReset() {
  error.value = "";
  loading.value = true;
  try {
    await ensureCsrf();
    const { data } = await api.post("/api/2fa/otp-reset/");
    secretInfo.value = data;
    if (navigator.clipboard && data?.secret) {
      navigator.clipboard.writeText(data.secret).catch(()=>{});
    }
  } catch {
    error.value = "Не удалось перепривязать. Попробуйте позже.";
  } finally {
    loading.value = false;
  }
}

function copySecret() {
  if (!secretInfo.value?.secret) return;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(secretInfo.value.secret).catch(()=>{});
  }
}

defineExpose({ show });
</script>
