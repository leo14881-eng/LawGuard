<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import AppLoading from './components/AppLoading.vue'

/**
 * 路由组件为按需加载的异步组件（见 router/index.ts 的 import()），刷新页面时
 * （不同于站内路由跳转——目标 chunk 通常已在内存/HTTP 缓存中，切换近乎瞬时）
 * 整个模块图需要重新从网络加载，Suspense 进入 pending 状态的时间明显更长。
 * 这段时间里 <main> 内容区曾经是空的或只有一个几十像素高的小 spinner，
 * Header 和 Footer（深蓝色通栏）却已经渲染，Footer 会紧贴 Header 下方短暂
 * 出现在视口顶部，加载完成后又被真实内容推到页面底部——这才是用户反馈
 * "刷新时蓝色一闪而过"的真实来源（已用 Playwright + CDP 逐帧采样定位，
 * 证实 html/body/#app 自身背景从未变蓝，是 Footer 位置随加载状态跳动）。
 *
 * 用 Suspense 的 pending/resolve 事件（而不是 setTimeout 或额外遮罩）驱动
 * `loading`，仅在真正处于加载状态时给 <main> 一个占满剩余视口高度的
 * min-height，把 Footer 保持在首屏之外；一旦内容 resolve，min-height 立即
 * 撤销，短页面不会被撑高，不影响正常页面的留白表现。
 *
 * 初始值必须是 true。另外经 CDP 逐帧采样发现：刷新页面后的最初约 300～900ms，
 * <RouterView v-slot="{ Component }"> 拿到的 Component 本身还是 undefined
 * （路由尚未解析完成），此时 <Suspense> 的默认插槽等于没有子节点，不会触发
 * pending/resolve，`loading` 这个 ref 完全不起作用——这正是第一版修复
 * （只监听 Suspense 事件）没有生效的原因。因此 min-height 不能只依赖
 * `loading`，还必须在 `Component` 为空时同样生效，见下方模板中的
 * `!Component || loading`。
 */
const loading = ref(true)
</script>

<template>
  <AppHeader />
  <RouterView v-slot="{ Component }">
    <main class="main" :class="{ 'main--loading': !Component || loading }">
      <Suspense @pending="loading = true" @fallback="loading = true" @resolve="loading = false">
        <component :is="Component" />
        <template #fallback>
          <AppLoading label="页面加载中…" />
        </template>
      </Suspense>
    </main>
  </RouterView>
  <AppFooter />
</template>

<style scoped>
/* 有意不对 .main 默认使用 flex:1 撑满视口高度：这会把 Footer 强行推到视口
   底部，内容较短的页面（如占位页、清单类页面）会在正文和 Footer 之间出现
   一大块突兀空白。改为让 Footer 紧跟内容之后，内容较短时页面本身短于视口
   高度也没有关系；仅在 main--loading（异步组件加载中）时临时撑满剩余视口，
   避免 Footer 在加载期间跳到顶部又被推下去。 */
.main--loading {
  min-height: calc(100svh - var(--header-height));
}
</style>
