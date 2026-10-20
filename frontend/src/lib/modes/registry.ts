import type { GameMode } from '#lib/api/modes';
import type { MessageKey } from '#lib/i18n';

/** Pantalla que monta cada modo. La ruta `/play/[mode]` la mapea a un componente. */
export type ModeRenderer = 'arcade' | 'versus';

export interface ModeEntry {
	/** Ruta de la pantalla del modo. */
	route: string;
	renderer: ModeRenderer;
	/** Posición en el menú: menor primero. */
	order: number;
	title: MessageKey;
	hint: MessageKey;
	variant: 'green' | 'blue' | 'slate';
	/** Pastilla del botón (vidas del arcade, VS del duelo). */
	aside: 'lives' | 'versus';
}

const REGISTRY: Record<string, ModeEntry> = {
	trivia_arcade: {
		route: '/arcade',
		renderer: 'arcade',
		order: 0,
		title: 'home.play_arcade',
		hint: 'home.play_arcade_hint',
		variant: 'green',
		aside: 'lives'
	},
	trivia_versus: {
		route: '/play',
		renderer: 'versus',
		order: 1,
		title: 'home.play_online',
		hint: 'home.play_online_hint',
		variant: 'blue',
		aside: 'versus'
	}
};

/** Presentación de un modo; `null` cuando el backend publica uno sin renderer. */
export function modeEntry(code: string): ModeEntry | null {
	return REGISTRY[code] ?? null;
}

/** Los modos conocidos primero, en el orden del menú; el resto conserva el del backend. */
export function orderModes(modes: GameMode[]): GameMode[] {
	return [...modes].sort((left, right) => {
		const leftEntry = modeEntry(left.code);
		const rightEntry = modeEntry(right.code);

		if (leftEntry && rightEntry) return leftEntry.order - rightEntry.order;
		if (leftEntry) return -1;
		if (rightEntry) return 1;
		return 0;
	});
}
