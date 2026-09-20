import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '.', testMatch: '*.spec.ts', fullyParallel: false, workers: 1, timeout: 30000,
  reporter: [['list']], outputDir: '../../target/ui-browser',
  use: { baseURL: 'http://127.0.0.1:1428', viewport: { width: 1100, height: 720 }, headless: true, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: { command: 'node server.mjs', url: 'http://127.0.0.1:1428', reuseExistingServer: false },
});
