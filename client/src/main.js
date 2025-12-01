import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";

import axios from "@/api"; // чтобы в одном месте был withCredentials и CSRF
axios.defaults.withCredentials = true;

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
