<script setup lang="ts">
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import AppLoading from './components/AppLoading.vue'
</script>

<template>
  <AppHeader />
  <main class="main">
    <RouterView v-slot="{ Component }">
      <Suspense>
        <component :is="Component" />
        <template #fallback>
          <!-- 页面级路由为按需加载的异步组件（见 router/index.ts 的 import()）：
               加载 chunk 期间用统一 Loading 状态占位，避免内容区短暂为空、
               Footer 瞬间贴到 Header 下方又被推下去，造成刷新时"一闪而过"的
               视觉跳动（对应 P3.4 页面须覆盖 loading 状态）。 -->
          <AppLoading label="页面加载中…" />
        </template>
      </Suspense>
    </RouterView>
  </main>
  <AppFooter />
</template>

<style scoped>
/* 有意不使用 flex:1 撑满视口高度：这会把 Footer 强行推到视口底部，
   内容较短的页面（如占位页、清单类页面）会在正文和 Footer 之间出现
   一大块突兀空白。改为让 Footer 紧跟内容之后，内容较短时页面本身
   短于视口高度也没有关系。 */
</style>
