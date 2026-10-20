import { ApiError } from '#lib/api/client';
import { session } from '#lib/api/session.svelte';
import { connectRoom, type Envelope, type SocketStatus } from '#lib/api/ws';
import { isCategory, type Category } from '#lib/categories';

/** Un turno tal como lo sirve el servidor; el cliente solo lo dibuja. */
export interface LiveQuestion {
	/** Índice que hay que devolver en `answer`; es 0-based en el protocolo. */
	round: number;
	prompt: string;
	options: string[];
	category: Category;
	endsAt: number;
	/** Puede no ser el de la config: los desempates duran la mitad. */
	totalSeconds: number;
}

export interface RoundScore {
	/** `null` si no llegó a responder. */
	choice: number | null;
	ms: number;
	points: number;
	correct: boolean;
}

export interface LiveRoundResult {
	round: number;
	correctIndex: number;
	you: RoundScore;
	opponent: RoundScore;
	scores: { you: number; opponent: number };
	explanation: string | null;
}

/** Una ronda cerrada, para repasar cuando la partida ya terminó. */
export interface LiveReviewItem {
	round: number;
	prompt: string;
	options: string[];
	correctIndex: number;
	choice: number | null;
	explanation: string | null;
}

export interface LiveEnd {
	winner: 'you' | 'opponent' | 'tie';
	scores: { you: number; opponent: number };
	reason: 'completed' | 'abandoned';
}

export interface LivePlayer {
	id: string;
	nick: string;
}

export interface LiveConfig {
	rounds: number;
	seconds: number;
}

export type LivePhase =
	| 'connecting'
	| 'waiting'
	| 'starting'
	| 'question'
	| 'answered'
	| 'reveal'
	| 'over';

interface RoomState {
	status: 'waiting' | 'playing' | 'finished' | 'expired';
	config: { rounds: number; seconds: number };
	you: { id: string; nick: string };
	players: { id: string; nick: string }[];
}

interface RoundStart {
	round: number;
	prompt: string;
	options: string[];
	category: string;
	ends_at: number;
	total_seconds: number;
}

interface MatchStart {
	config: { rounds: number; seconds: number };
	rounds_total: number;
}

interface MatchEnd extends LiveEnd {
	rounds: LiveRoundResult[];
}

function category(value: string): Category {
	return isCategory(value) ? value : 'science';
}

function asScore(value: unknown): RoundScore {
	const raw = (value ?? {}) as Partial<RoundScore>;
	return {
		choice: raw.choice ?? null,
		ms: raw.ms ?? 0,
		points: raw.points ?? 0,
		correct: raw.correct ?? false
	};
}

interface RoundResultWire {
	round?: number;
	correct_index?: number;
	explanation?: string | null;
	you?: Partial<RoundScore>;
	opponent?: Partial<RoundScore>;
	scores?: { you: number; opponent: number };
}

function asResult(value: unknown): LiveRoundResult {
	const raw = (value ?? {}) as RoundResultWire;
	return {
		round: raw.round ?? 0,
		correctIndex: raw.correct_index ?? -1,
		you: asScore(raw.you),
		opponent: asScore(raw.opponent),
		scores: raw.scores ?? { you: 0, opponent: 0 },
		explanation: raw.explanation ?? null
	};
}

/**
 * La partida vista desde un asiento: traduce el socket a estado de pantalla.
 * El servidor es el único que decide ronda, tiempos y resultado (`docs/api.md`).
 */
export function createLiveMatch(code: string, token: string) {
	let phase = $state<LivePhase>('connecting');
	let status = $state<SocketStatus>('connecting');
	/** Falla que corta la partida: no hay reconexión que la arregle. */
	let failure = $state<ApiError | null>(null);
	/** Error suelto del servidor (`ROUND_MISMATCH`, `NO_QUESTIONS`…). */
	let notice = $state<string | null>(null);

	let you = $state(session.user?.nick ?? '');
	let youId = $state('');
	let rival = $state('');
	let rounds = $state(0);
	let config = $state<LiveConfig>({ rounds: 0, seconds: 0 });
	/** Sillas de la sala, en el orden del servidor (incluye desconectadas). */
	let players = $state<LivePlayer[]>([]);
	let question = $state<LiveQuestion | null>(null);
	let picked = $state<number | null>(null);
	let result = $state<LiveRoundResult | null>(null);
	let review = $state<LiveReviewItem[]>([]);
	/** El enunciado solo viaja en `round_start`; el repaso lo cruza con el resultado. */
	const seen = new Map<number, { prompt: string; options: string[] }>();
	let scores = $state({ you: 0, opponent: 0 });
	let history = $state<('won' | 'lost')[]>([]);
	let rivalAnswered = $state(false);
	/** Segundos de gracia que le quedan al rival desconectado. */
	let rivalGone = $state<number | null>(null);
	let ended = $state<MatchEnd | null>(null);
	let rematchWaiting = $state(false);

	function onMessage(message: Envelope) {
		switch (message.t) {
			case 'room_state': {
				const state = message.d as RoomState;
				you = state.you.nick;
				youId = state.you.id;
				players = state.players;
				config = state.config;
				rival = state.players.find((player) => player.id !== state.you.id)?.nick ?? '';
				rounds = state.config.rounds;
				notice = null;
				if (state.status === 'waiting') phase = 'waiting';
				break;
			}
			case 'match_start': {
				const start = message.d as MatchStart;
				rounds = start.rounds_total;
				config = start.config;
				// Partida nueva: lo anterior era de la revancha pasada.
				history = [];
				review = [];
				seen.clear();
				scores = { you: 0, opponent: 0 };
				result = null;
				picked = null;
				rivalAnswered = false;
				rivalGone = null;
				ended = null;
				rematchWaiting = false;
				phase = 'starting';
				break;
			}
			case 'round_start': {
				const round = message.d as RoundStart;
				question = {
					round: round.round,
					prompt: round.prompt,
					options: round.options,
					category: category(round.category),
					endsAt: round.ends_at,
					totalSeconds: round.total_seconds
				};
				seen.set(round.round, { prompt: round.prompt, options: round.options });
				picked = null;
				result = null;
				rivalAnswered = false;
				notice = null;
				phase = 'question';
				break;
			}
			case 'opponent_answered':
				rivalAnswered = true;
				break;
			case 'round_result': {
				const round = asResult(message.d);
				result = round;
				picked = round.you.choice;
				scores = round.scores;
				history[round.round] = round.you.correct ? 'won' : 'lost';
				phase = 'reveal';
				break;
			}
			case 'match_end': {
				const end = message.d as MatchEnd;
				ended = end;
				scores = end.scores;
				// `rounds` trae todas las rondas resueltas: cápsulas y repaso final.
				const resolved = end.rounds.map(asResult);
				history = resolved.map((round) => (round.you.correct ? 'won' : 'lost'));
				review = resolved.flatMap((round) => {
					const question = seen.get(round.round);
					if (!question) return [];
					return [
						{
							round: round.round,
							prompt: question.prompt,
							options: question.options,
							correctIndex: round.correctIndex,
							choice: round.you.choice,
							explanation: round.explanation
						}
					];
				});
				phase = 'over';
				break;
			}
			case 'reconnect_pending':
				rivalGone = (message.d as { seconds_left: number }).seconds_left;
				break;
			case 'opponent_returned':
				rivalGone = null;
				break;
			case 'rematch_waiting':
				rematchWaiting = true;
				break;
			case 'error':
				notice = (message.d as { code?: string })?.code ?? 'UNKNOWN';
				break;
		}
	}

	const socket = connectRoom(code, token, {
		onMessage,
		onStatus: (next) => (status = next),
		onRejected: (error) => {
			failure = error;
			phase = 'over';
		}
	});

	function answer(choice: number) {
		if (phase !== 'question' || !question) return;
		// Sin canal no se manda: el server repone la ronda al reconectar.
		if (!socket.send('answer', { round: question.round, choice })) return;

		picked = choice;
		phase = 'answered';
	}

	/** Solo el host puede; el servidor igual rechaza con `NOT_HOST`/`NOT_READY`. */
	function start() {
		return socket.send('start');
	}

	function rematch() {
		if (socket.send('rematch')) rematchWaiting = true;
	}

	return {
		get phase() {
			return phase;
		},
		get status() {
			return status;
		},
		get failure() {
			return failure;
		},
		get notice() {
			return notice;
		},
		get you() {
			return you;
		},
		get youId() {
			return youId;
		},
		get rival() {
			return rival;
		},
		get config() {
			return config;
		},
		get players() {
			return players;
		},
		get question() {
			return question;
		},
		get picked() {
			return picked;
		},
		get result() {
			return result;
		},
		get review() {
			return review;
		},
		get scores() {
			return scores;
		},
		get history() {
			return history;
		},
		get rivalAnswered() {
			return rivalAnswered;
		},
		get rivalGone() {
			return rivalGone;
		},
		get ended() {
			return ended;
		},
		get rematchWaiting() {
			return rematchWaiting;
		},
		/** Las cápsulas crecen si hay desempate: el servidor puede servir rondas de más. */
		get total() {
			return Math.max(rounds, history.length, (question?.round ?? 0) + 1);
		},
		answer,
		start,
		rematch,
		close: () => socket.close()
	};
}

export type LiveMatch = ReturnType<typeof createLiveMatch>;
