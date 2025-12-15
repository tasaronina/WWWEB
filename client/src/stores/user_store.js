import { defineStore } from "pinia";
import { onBeforeMount, ref } from "vue";
import axios from "axios";
import Cookies from "js-cookie";

export const useUserStore = defineStore("userStore", () => {
  const userInfo = ref({
    is_authenticated: false,
    is_staff: false,
    second: false,
    username: "",
  });

  const second = ref(false);

  function applyCsrfFromCookies() {
    const token = Cookies.get("csrftoken");
    if (token) {
      axios.defaults.headers.common["X-CSRFToken"] = token;
    }
  }

  async function fetchUserInfo() {
   
    try {
      const r = await axios.get("/api/user/info/");
      userInfo.value = r.data;
      second.value = r.data.second || false;
    } catch (e) {
      userInfo.value = {
        is_authenticated: false,
        is_staff: false,
        second: false,
        username: "",
      };
      second.value = false;
    } finally {
      applyCsrfFromCookies();
    }
  }

  async function login(username, password) {
    await axios.post("/api/user/login/", { username, password });
    await fetchUserInfo();
  }

  async function logout() {
    await axios.post("/api/user/logout/");
    await fetchUserInfo(); // ✅ заново подтягиваем состояние + обновляем csrf
  }

  onBeforeMount(async () => {
    await fetchUserInfo();
  });

  return {
    userInfo,
    second,
    fetchUserInfo,
    login,
    logout,
  };
});
