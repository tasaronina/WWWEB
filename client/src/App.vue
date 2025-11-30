<script setup>
</script>

<template>
  <div style="padding:16px">
    <nav class="navbar navbar-expand-lg navbar-light bg-light" style="padding:8px 16px;">
      <div class="container-fluid">
        <div class="navbar-nav" style="display:flex; gap:12px;">
          <router-link class="nav-link" active-class="active" to="/categories">Категории</router-link>
          <router-link class="nav-link" active-class="active" to="/menu">Меню</router-link>
          <router-link class="nav-link" active-class="active" to="/customers">Клиенты</router-link>
          <router-link class="nav-link" active-class="active" to="/orders">Заказы</router-link>
          <router-link class="nav-link" active-class="active" to="/order-items">Позиции заказа</router-link>
        </div>

        <ul class="navbar-nav ms-auto">
          <li class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Пользователь
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><a class="dropdown-item" href="/admin/">Админка</a></li>
            </ul>
          </li>
        </ul>
      </div>
    </nav>

    <router-view />
  </div>
</template>

<style>
.navbar-nav .nav-link.active {
  font-weight: bold;
  color: #0d6efd !important;
}
</style>
