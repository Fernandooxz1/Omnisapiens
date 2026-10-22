import { expect, test } from '@playwright/test';
import { answerCurrent, createRoom, enter, joinRoom, uniqueNick } from './helpers';

test('a full 1v1 from code to result', async ({ browser }) => {
	test.setTimeout(90_000);

	const host = await browser.newContext();
	const guest = await browser.newContext();
	const hostPage = await host.newPage();
	const guestPage = await guest.newPage();

	const hostNick = uniqueNick('Host');
	const guestNick = uniqueNick('Guest');

	await enter(hostPage, hostNick, 'online');
	const code = await createRoom(hostPage, 3);

	await enter(guestPage, guestNick, 'online');
	await joinRoom(guestPage, code);

	// Las dos sillas ocupadas: el host ve al rival y puede empezar.
	await expect(hostPage.getByText(guestNick)).toBeVisible();
	await hostPage.getByRole('button', { name: 'Empezar partida' }).click();

	const overHeading = hostPage.getByRole('heading', { name: /^(¡Ganaste!|Perdiste|Empate)/ });
	const guestOver = guestPage.getByRole('heading', { name: /^(¡Ganaste!|Perdiste|Empate)/ });
	const enabledTile = hostPage.locator('.match__tiles button:not([disabled])').first();

	// Hasta seis preguntas: tres de partida y hasta tres de desempate.
	for (let round = 0; round < 6; round++) {
		await expect(enabledTile.or(overHeading)).toBeVisible({ timeout: 40_000 });
		if (await overHeading.isVisible()) break;

		// Los dos clientes dibujan la misma ronda del servidor.
		const roundText = await hostPage.locator('.match__top .sr-only').textContent();
		await expect(guestPage.locator('.match__top .sr-only')).toHaveText(roundText ?? '');

		await answerCurrent(hostPage, 0);
		await answerCurrent(guestPage, 1);

		// La revelación del servidor precede a la ronda siguiente; la última
		// resuelve directo en el fin de la partida.
		await expect(hostPage.locator('.match__cta').or(overHeading)).toBeVisible();
		await expect(guestPage.locator('.match__cta').or(guestOver)).toBeVisible();
		if (await overHeading.isVisible()) break;
	}

	// Ganador y resumen ronda a ronda en los dos navegadores.
	await expect(overHeading).toBeVisible();
	await expect(guestOver).toBeVisible();

	for (const page of [hostPage, guestPage]) {
		const rows = await page.locator('.summary__row').count();
		expect(rows).toBeGreaterThanOrEqual(3);
		await expect(page.locator('.summary__title')).toHaveText('Ronda a ronda');
	}

	// La explicación no aparece durante la partida: se consulta en el repaso final.
	await hostPage.getByText('Repasar la partida').click();
	await expect(hostPage.locator('.review__row').first()).toBeVisible();
	await expect(hostPage.locator('.review__row').first()).toContainText('La correcta');

	await host.close();
	await guest.close();
});
