<script setup lang="ts">
import { ref } from 'vue'

const navOpen = ref(false)

const navLinks = [
  { to: '/', label: '首页' },
  { to: '/stages', label: '权利指引' },
  { to: '/documents', label: '文书核对' },
  { to: '/official-channels', label: '官方渠道' },
  { to: '/about', label: '关于项目' },
]

function closeNav() {
  navOpen.value = false
}
</script>

<template>
  <header class="header">
    <div class="container header__inner">
      <RouterLink to="/" class="header__logo" @click="closeNav">
        法护 <span class="header__logo-en">LawGuard</span>
      </RouterLink>

      <button
        class="header__toggle"
        type="button"
        :aria-expanded="navOpen"
        aria-label="展开或收起导航菜单"
        @click="navOpen = !navOpen"
      >
        <span class="header__toggle-bar" />
        <span class="header__toggle-bar" />
        <span class="header__toggle-bar" />
      </button>

      <nav class="header__nav" :class="{ 'header__nav--open': navOpen }">
        <RouterLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="header__link"
          @click="closeNav"
        >
          {{ link.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  position: relative;
}

.header__logo {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary-dark);
  text-decoration: none;
  letter-spacing: 1px;
}

.header__logo-en {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  letter-spacing: 0.5px;
}

.header__toggle {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 36px;
  height: 36px;
  padding: 8px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
}

.header__toggle-bar {
  display: block;
  height: 2px;
  width: 100%;
  background: var(--color-primary-dark);
}

.header__nav {
  display: none;
  flex-direction: column;
  position: absolute;
  top: 60px;
  left: 0;
  right: 0;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  padding: 8px 20px 16px;
}

.header__nav--open {
  display: flex;
}

.header__link {
  padding: 10px 4px;
  color: var(--color-text);
  text-decoration: none;
  font-size: 15px;
  border-bottom: 1px solid var(--color-surface);
}

.header__link:last-child {
  border-bottom: none;
}

.header__link.router-link-active {
  color: var(--color-primary);
  font-weight: 700;
}

@media (min-width: 800px) {
  .header__toggle {
    display: none;
  }

  .header__nav {
    display: flex;
    flex-direction: row;
    position: static;
    border: none;
    padding: 0;
    gap: 28px;
  }

  .header__link {
    padding: 0;
    border-bottom: none;
  }
}
</style>
