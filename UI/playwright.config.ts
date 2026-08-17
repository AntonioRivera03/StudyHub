import { defineConfig } from '@playwright/test';

const backendPort = process.env.STUDYHUB_E2E_BACKEND_PORT ?? '8011';
const frontendPort = process.env.STUDYHUB_E2E_FRONTEND_PORT ?? '4174';
const databaseUrl = process.env.STUDYHUB_E2E_DATABASE_URL
  ?? 'sqlite:////tmp/opencode/studyhub-e2e.db';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        launchOptions: { executablePath: '/usr/bin/chromium' },
      },
    },
  ],
  webServer: [
    {
      command:
        `STUDYHUB_DATABASE_URL=${databaseUrl} STUDYHUB_ENVIRONMENT=test ../Server/.venv/bin/uvicorn app.main:app --app-dir ../Server --host 127.0.0.1 --port ${backendPort}`,
      url: `http://127.0.0.1:${backendPort}/api/v1/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: `VITE_API_PROXY_TARGET=http://127.0.0.1:${backendPort} npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
