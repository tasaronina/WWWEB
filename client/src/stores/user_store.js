import { defineStore } from "pinia";
import { onBeforeMount, ref } from "vue";
import axios from "axios";

export const useUserStore = defineStore("userStore", () => {
  const userInfo = ref({
    is_authenticated: false,
    is_staff: false,
    second: false,
    username: "",
  });

  const second = ref(false);

  async function checkLogin() {
    try {
      const r = await axios.get("/api/user/info/");
      userInfo.value = r.data;
      second.value = r.data.second;
    } catch (error) {
      userInfo.value = {
        is_authenticated: false,
        is_staff: false,
        second: false,
        username: "",
      };
      second.value = false;
    }
  }

  async function login(username, password) {
    await axios.post("/api/user/login/", {
      username,
      password,
    });
    await checkLogin();
  }

  async function logout() {
    try {
      await axios.post("/api/user/logout/");
    } finally {
      userInfo.value = {
        is_authenticated: false,
        is_staff: false,
        second: false,
        username: "",
      };
      second.value = false;
    }
  }

  onBeforeMount(async () => {
    await checkLogin();
  });

  return {
    userInfo,
    second,
    checkLogin,
    login,
    logout,
  };
});
