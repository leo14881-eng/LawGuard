import { defineConfig } from '@playwright/test'

/**
 * 仅用于"首屏闪烁"类问题的回归测试（e2e/first-paint-flash.spec.ts），
 * 不是完整的 E2E 测试体系；不影响 `npm run test`（Vitest 单元/组件测试）。
 * 通过 `npm run test:e2e` 单独运行，自动拉起生产构建的预览服务器。
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  fullyParallel: false,
  reporter: 'list',
  webServer: {
    command: 'npm run preview -- --port 5199 --strictPort',
    port: 5199,
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
  use: {
    baseURL: 'http://localhost:5199',
  },
})
