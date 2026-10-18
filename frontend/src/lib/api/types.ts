/** Respuestas del backend tal cual, según `docs/api.md`. El cliente no las reescribe. */

import type { Category } from '#lib/categories';

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

export type LeaderboardPeriod = 'all' | 'week';

export interface LeaderboardEntry {
	position: number;
	nick: string;
	score: number;
	/** ISO-8601. */
	achieved_at: string;
}

export interface Leaderboard {
	period: LeaderboardPeriod;
	entries: LeaderboardEntry[];
}

/** Los tres campos van juntos: sin corridas en el período, los tres son `null`. */
export interface ArcadeRank {
	rank: number | null;
	score: number | null;
	achieved_at: string | null;
}

export interface MyRanks {
	global: ArcadeRank;
	week: ArcadeRank;
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

export type QuestionStatus = 'draft' | 'published' | 'archived';

/** Vista del panel: es la única que trae `correct_index`. */
export interface AdminQuestion {
	id: string;
	category: Category;
	difficulty: number;
	prompt: string;
	options: string[];
	correct_index: number;
	explanation: string | null;
	source: string | null;
	status: QuestionStatus;
	media_type: string;
	media_url: string | null;
	tags: string[];
	created_at: string;
	updated_at: string;
}

export interface AdminQuestionPage {
	items: AdminQuestion[];
	page: number;
	page_size: number;
	total: number;
	pages: number;
}

export interface AdminFilters {
	status?: QuestionStatus;
	category?: Category;
	difficulty?: number;
	q?: string;
	page?: number;
	page_size?: number;
}

export interface RejectedRow {
	row: number;
	reason: string;
}

export interface ImportReport {
	total: number;
	imported: number;
	duplicated: number;
	rejected: RejectedRow[];
}
