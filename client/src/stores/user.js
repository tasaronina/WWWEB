
import { defineStore } from "pinia";
import axios from "axios";
import router from "@/router";

axios.defaults.withCredentials = true;

async function ensureCsrf() {
  try { await axios.get("/api/csrf/"); } catch {  }
}

export const useUserStore = defineStore("user", {
  state: () => ({
    ready: false,
    user: null,
  }),
  getters: {
    isAuthed: (s) => !!s.user,
    username: (s) => s.user?.username || "",
    isAdmin:  (s) => !!(s.user?.is_staff || s.user?.is_superuser),
  },
  actions: {
    async restore() {
      await this.refresh();
      this.ready = true;
    },
    async refresh() {
      try {
        const { data } = await axios.get("/api/auth/me/");
        this.user = data?.is_authenticated ? data : null;
      } catch {
        this.user = null;
      }
      return this.user;
    },
    async login(username, password) {
      await ensureCsrf();
      const { data } = await axios.post("/api/auth/login/", { username, password });
      const ok = !!(data && (data.ok === true || data.success === true));
      if (!ok) throw new Error("bad_credentials");
      await this.refresh();
      return true;
    },
    async logout() {
      try { await axios.post("/api/auth/logout/"); } catch { /* ignore */ }
      this.user = null;
      
      await router.replace({ name: "login" });
    },
  },
});
