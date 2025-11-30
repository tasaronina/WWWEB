// client/src/main.js
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./styles/admin.css";
import { initCsrf } from "./api";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

// сначала получаем csrftoken, потом монтируем приложение
initCsrf().finally(() => {
  createApp(App).use(router).mount("#app");
});
