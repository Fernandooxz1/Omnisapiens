import { expect, test } from '@playwright/test';
import { enter, uniqueNick } from './helpers';

test('an arcade run until the three lives are gone', async ({ page }) => {
	// Sin responder, cada pregunta vence y descuenta una vida: 20 s por pregunta.
	test.setTimeout(150_000);

	await enter(page, uniqueNick('Arc'), 'arcade');

	await expect(page.locator('.match__tiles button')).toHaveCount(4, { timeout: 15_000 });

	const over = page.getByRole('heading', { name: 'Fin de la corrida' });
	await expect(over).toBeVisible({ timeout: 110_000 });

	// El puntaje y los aciertos los decide el servidor; sin responder son cero.
	await expect(page.locator('.end-score__value')).toHaveText(/^\d+$/);
	await expect(page.locator('.end-stats dd').first()).toHaveText('0');
	await expect(page.locator('.end-ranks')).toContainText('Global');
	await expect(page.locator('.end-ranks')).toContainText('Semanal');
	await expect(page.getByRole('button', { name: 'Otra corrida' })).toBeVisible();
});
