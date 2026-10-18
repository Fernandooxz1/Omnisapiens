import { defineConfig, devices } from '@playwright/test';

/**
 * Las e2e corren contra el backend real (`make up && make migrate && make seed`
 * y la API en `:8000`): la partida y los puntajes los decide el servidor.
 * El frontend lo levanta Playwright en `:5173`, el mismo origen que permite CORS.
 */
export default defineConfig({
	testDir: './e2e',
	fullyParallel: false,
	workers: 1,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 1 : 0,
	reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
	use: {
		baseURL: 'http://localhost:5173',
		trace: 'on-first-retry'
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	webServer: {
		command: 'npm run dev -- --host localhost --port 5173 --strictPort',
		url: 'http://localhost:5173',
		reuseExistingServer: !process.env.CI,
		timeout: 60_000
	}
});
