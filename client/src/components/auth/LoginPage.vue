<template>
  <v-container class="py-10" style="max-width: 820px;">
    <div class="text-center mb-2">
      <div class="text-h4 font-weight-bold">Вход</div>
      <div class="text-medium-emphasis">Введите логин и пароль</div>
    </div>

    <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>

    <v-card>
      <v-card-text>
        <v-form @submit.prevent="onSubmit">
          <v-row class="mt-2" justify="center">
            <v-col cols="12" md="6">
              <v-text-field v-model="form.username" label="Логин" autocomplete="username" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.password"
                :type="showPass? 'text':'password'"
                label="Пароль"
                autocomplete="current-password"
                :append-inner-icon="showPass? 'mdi-eye-off':'mdi-eye'"
                @click:append-inner="showPass=!showPass"
              />
            </v-col>
            <v-col cols="12" md="6" class="mt-2">
              <v-btn type="submit" color="primary" block :loading="loading">Войти</v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-dialog v-model="otpOpen" persistent max-width="480">
      <v-card>
        <v-card-title class="text-h6">{{ otpMode==='verify' ? 'Подтверждение входа (2FA)' : 'Привязка 2FA' }}</v-card-title>
        <v-card-text>
          <template v-if="otpMode==='setup'">
            <div class="mb-2">Секрет для приложения-аутентификатора:</div>
            <v-sheet class="pa-2 rounded" color="grey-lighten-4">{{ otpSecretData?.secret }}</v-sheet>
            <div class="mt-3 mb-1">URI:</div>
            <div class="text-body-2 text-break">{{ otpSecretData?.otpauth_url }}</div>
            <v-divider class="my-4" />
            <div class="mb-2">Введите 6-значный код:</div>
            <v-text-field v-model="otpCode" maxlength="6" placeholder="Например, 123456" />
            <div v-if="otpError" class="text-error text-body-2 mt-2">{{ otpError }}</div>
          </template>
          <template v-else>
            <div class="mb-2">Введите 6-значный код из приложения:</div>
            <v-text-field v-model="otpCode" maxlength="6" placeholder="Код 2FA" />
            <div v-if="otpError" class="text-error text-body-2 mt-2">{{ otpError }}</div>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="otpOpen=false">Отмена</v-btn>
          <v-btn color="primary" :loading="otpLoading" @click="submitOtp">Подтвердить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { login as apiLogin, me, otpStatus, otpSecret as apiOtpSecret, otpLogin } from '@/api'

const router = useRouter()
const route = useRoute()
const store = useUserStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPass = ref(false)

const otpOpen = ref(false)
const otpMode = ref('verify')
const otpCode = ref('')
const otpLoading = ref(false)
const otpError = ref('')
const otpSecretData = ref(null)

function openOtp(){ otpError.value=''; otpCode.value=''; otpOpen.value=true }
function goNext(){ const next = (route.query.next && String(route.query.next)) || '/menu'; router.replace(next) }

async function afterLogin2FA(){
  const st = await otpStatus()
  if (!st.confirmed){
    otpMode.value='setup'
    otpSecretData.value = await apiOtpSecret()
    openOtp()
    return
  }
  if (!st.otp_good){
    otpMode.value='verify'
    openOtp()
    return
  }
  await store.restore()
  goNext()
}

async function submitOtp(){
  otpLoading.value = true
  otpError.value = ''
  try{
    const code = String(otpCode.value||'').replace(/\s+/g,'')
    if (!/^\d{6}$/.test(code)){ otpError.value='Введите 6-значный код.'; return }
    const res = await otpLogin(code)
    if (!res || (res.success===false)){ otpError.value='Неверный код. Попробуйте ещё раз.'; return }
    await store.restore()
    otpOpen.value = false
    goNext()
  }catch{
    otpError.value='Не удалось подтвердить код.'
  }finally{
    otpLoading.value=false
  }
}

async function onSubmit(){
  loading.value = true
  error.value = ''
  try{
    const resp = await apiLogin(form.value.username.trim(), form.value.password)
    const ok = !!(resp && (resp.ok || resp.success))
    if (!ok) throw new Error('bad creds')
    await me()
    await afterLogin2FA()
  }catch{
    error.value = 'Не удалось войти. Проверьте логин и пароль.'
  }finally{
    loading.value = false
  }
}
</script>
