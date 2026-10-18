/** Las dos pieles de la app. El markup es el mismo; cambia `data-skin` en <html>. */
export type Skin = 'papel' | 'colorido';

/** La clave la lee el bootstrap inline de app.html para no parpadear al cargar. */
export const SKIN_KEY = 'omni-skin';

export const SKINS: readonly Skin[] = ['papel', 'colorido'];

export const DEFAULT_SKIN: Skin = 'papel';

export function isSkin(value: unknown): value is Skin {
	return value === 'papel' || value === 'colorido';
}

export function getSkin(): Skin {
	if (typeof document === 'undefined') return DEFAULT_SKIN;
	const value = document.documentElement.dataset.skin;
	return isSkin(value) ? value : DEFAULT_SKIN;
}

/** Color de la barra del navegador por piel; se aplica junto con `data-skin`. */
export const THEME_COLORS: Record<Skin, string> = {
	papel: '#FCF8F0',
	colorido: '#222831'
};

export function setSkin(skin: Skin): void {
	document.documentElement.dataset.skin = skin;
	document
		.querySelector('meta[name="theme-color"]')
		?.setAttribute('content', THEME_COLORS[skin]);
	try {
		localStorage.setItem(SKIN_KEY, skin);
	} catch {
		/* sin persistencia: la piel igual vale para esta sesión */
	}
}
