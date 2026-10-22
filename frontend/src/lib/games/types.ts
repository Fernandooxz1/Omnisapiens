import type { IconName } from '#lib/components/Icon.svelte';
import type { MessageKey } from '#lib/i18n';

/** El hub no conoce juegos concretos: cada entrada del registro aporta estos datos. */
export type GameId = 'murdoku';

export type GameAccent = 'green' | 'blue' | 'yellow' | 'orange' | 'red' | 'purple';

export interface GameMeta {
	id: GameId;
	/** Ruta del catálogo del juego, hermana de `/juegos`. */
	route: string;
	titleKey: MessageKey;
	blurbKey: MessageKey;
	icon: IconName;
	accent: GameAccent;
	order: number;
	caseCount: number;
}

/** Los seis niveles de la escala; el orden vive en `difficulty.ts`. */
export type DifficultyKey =
	| 'very_easy'
	| 'easy'
	| 'medium'
	| 'hard'
	| 'very_hard'
	| 'hardcore';

export interface Cell {
	row: number;
	col: number;
}

export interface CaseMeta {
	/** "murdoku-001" */
	id: string;
	game: GameId;
	/** 1..62 */
	number: number;
	title: string;
	setting: string;
	difficulty: DifficultyKey;
	/** Lado de la grilla: 5..15. */
	size: number;
	estimatedMinutes: number;
	/** Solo el primer 5×5. */
	tutorial?: boolean;
}

/** Datos mínimos para dibujar un sobre antes de cargar el caso completo. */
export interface CasePreview {
	meta: CaseMeta;
	/** Región por celda, `[row][col]`. */
	regions: number[][];
	/** La víctima es pública; los sospechosos no. */
	victim: Cell;
}
