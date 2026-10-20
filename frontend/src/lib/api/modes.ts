import { request } from './client';

/** Modo publicado por `GET /modes`: el catálogo manda, el cliente no hardcodea. */
export interface GameMode {
	code: string;
	name: string;
	content_kind: string;
	play_format: string;
	players: 'solo' | 'versus';
	input: 'choice';
	media: string[];
	/** Si publica tabla propia en `/leaderboard/{code}`. */
	ranking: boolean;
	/** JSON Schema que valida el `config` de la sesión o de la sala. */
	config_schema: Record<string, unknown>;
}

export function fetchModes(): Promise<GameMode[]> {
	return request<GameMode[]>('/modes');
}
