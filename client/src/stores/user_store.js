import { defineStore } from "pinia";
import { onBeforeMount, ref } from "vue";
import axios from "axios";
import Cookies from "js-cookie";

export const useUserStore = defineStore("userStore", () => {
  const username = ref("");
  const is_authenticated = ref(null);
  const is_staff = ref(false);
  const second = ref(false);

  const userInfo = ref({
    is_authenticated: false,
    is_staff: false,
    second: false,
    username: "",
  });

  function applyCsrfFromCookies() {
    axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken");
  }

  async function fetchUserInfo() {
    try {
      const r = await axios.get("/api/user/info/");

      userInfo.value = r.data;

      username.value = r.data.username || "";
      is_authenticated.value = r.data.is_authenticated;
      is_staff.value = r.data.is_staff || false;
      second.value = r.data.second || false;

      applyCsrfFromCookies();
    } catch (e) {
      userInfo.value = {
        is_authenticated: false,
        is_staff: false,
        second: false,
        username: "",
      };

      username.value = "";
      is_authenticated.value = false;
      is_staff.value = false;
      second.value = false;

      applyCsrfFromCookies();
    }
  }

  async function checkLogin() {
    await fetchUserInfo();
  }

  async function login(loginUsername, loginPassword) {
    await axios.post("/api/user/login/", {
      username: loginUsername,
      password: loginPassword,
    });

    await fetchUserInfo();
  }

  async function logout() {
    await axios.post("/api/user/logout/");
    await fetchUserInfo();
  }

  async function getTotp() {
    const r = await axios.get("/api/user/get-totp/");

    if (r.data && r.data.url) {
      return r.data.url;
    }

    return "";
  }

  async function verifyTotp(code) {
    const key = String(code || "").trim();

    const r = await axios.post("/api/user/second-login/", {
      key: key,
    });

    await fetchUserInfo();

    if (r.data && r.data.success) {
      return true;
    }

    return false;
  }

  onBeforeMount(async () => {
    await fetchUserInfo();
  });

  return {
    username,
    is_authenticated,
    is_staff,
    second,

    userInfo,

    fetchUserInfo,
    checkLogin,
    login,
    logout,

    getTotp,
    verifyTotp,
  };
});
