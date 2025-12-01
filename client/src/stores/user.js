// client/src/stores/user.js
import { defineStore } from "pinia";
import { getMe, doLogin, doLogout } from "@/api";
import router from "@/router";

export const useUserStore = defineStore("user", {
  state: () => ({
    user: null,           // {id, username, is_staff, is_superuser}
    ready: false,         // инициализация завершена
  }),
  getters: {
    isAuth: (s) => !!s.user,
    username: (s) => (s.user ? s.user.username : ""),
    isAdmin: (s) => !!(s.user && (s.user.is_staff || s.user.is_superuser)),
  },
  actions: {
    async restore() {
      try {
        const me = await getMe();
        // Когда не залогинен — сервер отдаёт {} или is_authenticated=false
        this.user = me && me.username ? me : null;
      } catch {
        this.user = null;
      } finally {
        this.ready = true;
      }
    },

    async login(username, password) {
      const me = await doLogin(username, password);
      // сервер возвращает id/username/is_staff/is_superuser
      this.user = me && me.username ? me : null;
      if (!this.user) throw new Error("bad credentials");
    },

    async logout() {
      try { await doLogout(); } finally {
        this.user = null;
        // жёстко отправляем на логин, чтобы не оставаться на /menu
        if (router.currentRoute.value.path !== "/login") {
          await router.replace("/login");
        }
      }
    },
  },
});
