/** Vibración táctil: existe en móvil y se ignora en silencio donde no está. */
function vibrate(pattern: number | number[]): void {
	if (typeof navigator === 'undefined' || !('vibrate' in navigator)) return;

	try {
		navigator.vibrate(pattern);
	} catch {
		/* algunos navegadores la rechazan sin un gesto previo del usuario */
	}
}

export const haptics = {
	tap(): void {
		vibrate(12);
	},
	success(): void {
		vibrate(40);
	},
	error(): void {
		vibrate([35, 50, 35]);
	}
};
