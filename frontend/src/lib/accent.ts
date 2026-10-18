/** El tono del acento del jugador: pinta su avatar. Se recuerda en `localStorage`. */
export type Accent = 'blue' | 'green' | 'orange' | 'pink' | 'purple';

/** La clave la lee el bootstrap inline de app.html para no parpadear al cargar. */
export const ACCENT_KEY = 'omni-accent';

export const ACCENTS: readonly Accent[] = ['blue', 'green', 'orange', 'pink', 'purple'];

export const DEFAULT_ACCENT: Accent = 'blue';

/** Muestra de cada swatch: el cuerpo de la familia, igual que `--accent-bot`. */
export const ACCENT_SWATCH: Record<Accent, string> = {
	blue: '#0098E6',
	green: '#1EC765',
	orange: '#FF7800',
	pink: '#EC388B',
	purple: '#9338C6'
};

export function isAccent(value: unknown): value is Accent {
	return ACCENTS.includes(value as Accent);
}

export function getAccent(): Accent {
	if (typeof document === 'undefined') return DEFAULT_ACCENT;
	const value = document.documentElement.dataset.accent;
	return isAccent(value) ? value : DEFAULT_ACCENT;
}

export function setAccent(accent: Accent): void {
	document.documentElement.dataset.accent = accent;
	try {
		localStorage.setItem(ACCENT_KEY, accent);
	} catch {
		/* sin persistencia: el acento igual vale para esta sesión */
	}
}
