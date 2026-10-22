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
