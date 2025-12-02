import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";

// важно: импортируем конфиг axios как сайд-эффект,
// чтобы он применился даже если страницы импортируют "axios" напрямую
import "@/api";

import "@/styles/admin.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
