/** Respuestas del backend tal cual, según `docs/api.md`. El cliente no las reescribe. */

export interface User {
	id: string;
	nick: string;
	is_guest: boolean;
	created_at: string;
	last_seen_at: string;
}

/** Alta o cambio de nick: siempre trae token nuevo para guardar. */
export interface AuthOut {
	user: User;
	token: string;
}

export type MatchResult = 'win' | 'loss' | 'draw';

/** Configuración de una sala 1v1 (`POST /rooms`). */
export interface RoomConfig {
	rounds: number;
	seconds: number;
}

export interface RoomCreated {
	code: string;
	config: RoomConfig;
}

/** Vista previa pública de una sala (`GET /rooms/{code}`). */
export interface RoomPreview {
	code: string;
	config: RoomConfig;
	status: 'waiting' | 'playing' | 'finished' | 'expired';
	host_nick: string;
	expires_at: string;
	/** Sillas ocupadas, no conexiones. */
	players: number;
}

export interface ArcadeRun {
	id: string;
	score: number;
	correct_count: number;
	longest_streak: number;
	max_difficulty: number;
	ended_at: string;
}

export interface MatchSummary {
	id: string;
	ended_at: string;
	opponent_nick: string;
	my_score: number;
	opponent_score: number;
	result: MatchResult;
}

export interface Me extends User {
	best: { all_time: number | null; week: number | null } | null;
	arcade_runs: ArcadeRun[];
	matches: MatchSummary[];
}
