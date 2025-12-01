import { defineStore } from "pinia";
import { apiMe, apiLogin, apiLogout } from "@/api";

export const useUserStore = defineStore("user", {
  state: () => ({
    me: null,
    initialized: false,
    loading: false,
  }),

  getters: {
    isAuth: (s) => !!(s.me && s.me.id),
    isAdmin: (s) => !!(s.me && (s.me.is_staff || s.me.is_superuser)),
    username: (s) => s.me?.username ?? "",
  },

  actions: {
    // Восстановление сессии при старте приложения/перезагрузке
    async restore(force = false) {
      if (this.initialized && !force) return;
      this.loading = true;
      try {
        const data = await apiMe();
        this.me = data?.is_authenticated
          ? {
              id: data.id,
              username: data.username,
              is_staff: !!data.is_staff,
              is_superuser: !!data.is_superuser,
            }
          : null;
      } finally {
        this.initialized = true;
        this.loading = false;
      }
    },

    // Логин
    async login(username, password) {
      await apiLogin(username, password);
      await this.restore(true);
    },

    // Логаут + мгновенный редирект на /login
    async logout() {
      try { await apiLogout(); } catch { /* игнор сетевых ошибок */ }
      this.me = null;
      this.initialized = false;

      // ВАЖНО: убираем защищённую страницу из истории и переходим на логин
      window.location.replace("/login");
    },
  },
});
