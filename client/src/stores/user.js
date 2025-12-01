import { defineStore } from "pinia";
import axios from "axios";

axios.defaults.withCredentials = true;

async function ensureCsrf() {
  try { await axios.get("/api/csrf/"); } catch {}
}

export const useUserStore = defineStore("user", {
  state: () => ({
    user: null,
    ready: false,
    error: "",
  }),

  getters: {
    isAuthenticated: (s) => !!s.user,
    username: (s) =>
      s.user?.username ||
      s.user?.name ||
      s.user?.email ||
      "",
  },

  actions: {
    async init() {
      if (this.ready) return;
      this.error = "";
      try {
        await ensureCsrf();
        const { data } = await axios.get("/api/auth/me/");
        this.user = data || null;
      } catch {
        this.user = null;
      } finally {
        this.ready = true;
      }
    },

    async login({ username, password }) {
      this.error = "";
      try {
        await ensureCsrf();
        await axios.post("/api/auth/login/", { username, password });
        const { data } = await axios.get("/api/auth/me/");
        this.user = data || null;
        this.ready = true;
        return true;
      } catch (e) {
        this.user = null;
        this.ready = true;
        this.error = "Неверные логин или пароль";
        return false;
      }
    },

    async logout() {
      try {
        await ensureCsrf();
        await axios.post("/api/auth/logout/");
      } catch {}
      this.user = null;
      this.ready = true;
    },
  },
});
