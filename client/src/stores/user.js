import { defineStore } from "pinia";
import api, { ensureCsrf } from "@/api";

export const useUserStore = defineStore("user", {
  state: () => ({
    // базовое состояние
    ready: false,          // для совместимости с твоим App.vue
    initialized: false,    // внутренний флаг
    authenticated: false,
    user: null,
    otp_ttl: 0,
  }),
  getters: {
    isAuthed(state) {
      return !!state.authenticated;
    },
    isAdmin(state) {
      return !!state.user?.is_staff || !!state.user?.is_superuser;
    },
    username(state) {
      return state.user?.username || state.user?.email || "";
    },
  },
  actions: {
    async fetchMe() {
      const { data } = await api.get("/api/auth/me/");
      this.authenticated = !!data?.authenticated;
      this.user = data?.user || null;
      this.otp_ttl = Number(data?.otp_ttl || 0);
      this.initialized = true;
      this.ready = true;    // совместимость с твоим кодом
      return data;
    },

    // алиас для твоего App.vue
    async restore() {
      return await this.fetchMe();
    },

    async login(username, password) {
      await ensureCsrf();
      await api.post("/api/auth/login/", { username, password });
      return await this.fetchMe(); // здесь authenticated уже true
    },

    async logout() {
      await ensureCsrf();
      await api.post("/api/auth/logout/");
      this.authenticated = false;
      this.user = null;
      this.otp_ttl = 0;
      this.ready = true;
      this.initialized = true;
    },
  },
});
