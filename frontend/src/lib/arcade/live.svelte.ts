import { ApiError } from '#lib/api/client';
import { createSoloSession } from '#lib/api/sessions';
import { connectSession, type Envelope, type Socket, type SocketStatus } from '#lib/api/ws';

export type ArcadePhase =
	| 'connecting'
	| 'starting'
	| 'question'
	| 'answered'
	| 'reveal'
	| 'over';

/** La pregunta tal como la sirve el servidor; el cliente solo la dibuja. */
export interface ArcadeQuestion {
	round: number;
	prompt: string;
	options: string[];
	/** Duración total de esta pregunta (baja con los aciertos). */
	seconds: number;
	endsAt: number;
}

export interface ArcadeScore {
	/** `null` si no llegó a responder. */
	choice: number | null;
	points: number;
	correct: boolean;
}

export interface ArcadeResult {
	round: number;
	correctIndex: number;
	you: ArcadeScore;
	score: number;
	lives: number;
	streak: number;
	correctCount: number;
}

export interface ArcadeEnd {
	runId: string;
	score: number;
	correctCount: number;
	maxDifficulty: number;
	longestStreak: number;
	rankGlobal: number | null;
	rankWeekly: number | null;
	personalBest: number | null;
	isNewBest: boolean;
}

interface StartWire {
	lives: number;
}

interface ItemStartWire {
	item_key: string;
	position: number;
	ends_at: number;
	total_seconds: number;
	payload: {
		prompt: string;
		options: string[];
	};
}

interface SubmissionWire {
	index?: number;
}

interface ItemResultWire {
	item_key: string;
	correct: boolean;
	submission: SubmissionWire | null;
	solution: { correct_index?: number } | null;
	points: number;
	scores: {
		score?: number;
		lives?: number;
		streak?: number;
		correct_count?: number;
	};
}

interface RankingWire {
	rank_global?: number | null;
	rank_weekly?: number | null;
	personal_best?: number | null;
	is_new_best?: boolean;
}

interface EndWire {
	session_id: string;
	score: number;
	correct_count: number;
	max_difficulty: number;
	longest_streak: number;
	ranking: RankingWire | null;
}

/**
 * Una partida arcade sobre el canal canónico de una sesión solo. La sesión se
 * crea antes (`POST /sessions`) y el socket solo la juega: otra partida es otra
 * sesión, no un `restart`.
 */
export function createArcadeRun(token: string, mode = 'trivia_arcade') {
	let phase = $state<ArcadePhase>('connecting');
	let status = $state<SocketStatus>('connecting');
	let failure = $state<ApiError | null>(null);
	/** Error suelto del servidor (`NO_QUESTIONS`, `ROUND_MISMATCH`…). */
	let notice = $state<string | null>(null);

	let question = $state<ArcadeQuestion | null>(null);
	let result = $state<ArcadeResult | null>(null);
	let picked = $state<number | null>(null);
	let end = $state<ArcadeEnd | null>(null);
	let score = $state(0);
	let lives = $state(3);
	let streak = $state(0);
	let correctCount = $state(0);

	let socket: Socket | null = null;
	/** El socket (o la creación) vieja no puede pisar el estado de la nueva. */
	let generation = 0;
	let disposed = false;

	function onMessage(message: Envelope) {
		switch (message.t) {
			case 'session_start': {
				const start = message.d as StartWire;
				score = 0;
				lives = start.lives;
				streak = 0;
				correctCount = 0;
				phase = 'starting';
				break;
			}
			case 'item_start': {
				const next = message.d as ItemStartWire;
				question = {
					round: next.position,
					prompt: next.payload.prompt,
					options: next.payload.options,
					seconds: next.total_seconds,
					endsAt: next.ends_at
				};
				picked = null;
				result = null;
				notice = null;
				phase = 'question';
				break;
			}
			case 'item_result': {
				const resolved = message.d as ItemResultWire;
				result = {
					round: Number(resolved.item_key),
					correctIndex: resolved.solution?.correct_index ?? -1,
					you: {
						choice: resolved.submission?.index ?? null,
						points: resolved.points,
						correct: resolved.correct
					},
					score: resolved.scores.score ?? 0,
					lives: resolved.scores.lives ?? 0,
					streak: resolved.scores.streak ?? 0,
					correctCount: resolved.scores.correct_count ?? 0
				};
				score = result.score;
				lives = result.lives;
				streak = result.streak;
				correctCount = result.correctCount;
				picked = result.you.choice;
				phase = 'reveal';
				break;
			}
			case 'session_end': {
				const final = message.d as EndWire;
				const ranking = final.ranking;
				end = {
					runId: final.session_id,
					score: final.score,
					correctCount: final.correct_count,
					maxDifficulty: final.max_difficulty,
					longestStreak: final.longest_streak,
					rankGlobal: ranking?.rank_global ?? null,
					rankWeekly: ranking?.rank_weekly ?? null,
					personalBest: ranking?.personal_best ?? null,
					isNewBest: ranking?.is_new_best ?? false
				};
				score = final.score;
				correctCount = final.correct_count;
				phase = 'over';
				// La sesión terminó: el socket ya no tiene nada que hacer y el canal
				// es de una conexión. `again` crea otra sesión.
				socket?.close();
				break;
			}
			case 'error':
				notice = (message.d as { code?: string })?.code ?? 'UNKNOWN';
				break;
		}
	}

	function reset() {
		phase = 'connecting';
		status = 'connecting';
		failure = null;
		notice = null;
		question = null;
		result = null;
		picked = null;
		end = null;
		score = 0;
		lives = 3;
		streak = 0;
		correctCount = 0;
	}

	async function connect() {
		const mine = ++generation;

		try {
			const created = await createSoloSession(token, mode);
			if (disposed || mine !== generation) return;

			socket = connectSession(created.session_id, token, {
				onMessage: (message) => {
					if (mine === generation) onMessage(message);
				},
				onStatus: (next) => {
					if (mine === generation) status = next;
				},
				onRejected: (error) => {
					if (mine !== generation) return;
					failure = error;
					phase = 'over';
				}
			});
		} catch (error) {
			if (disposed || mine !== generation) return;
			failure =
				error instanceof ApiError
					? error
					: new ApiError(0, 'UNKNOWN', 'No se pudo crear la sesión.');
			phase = 'over';
		}
	}

	void connect();

	function answer(choice: number) {
		if (phase !== 'question' || !question) return;
		// Sin canal no se manda: la partida no se puede reanudar (es de una conexión).
		if (!socket?.send('answer', { round: question.round, choice })) return;

		picked = choice;
		phase = 'answered';
	}

	/** Otra partida: la anterior ya terminó, así que se crea otra sesión. */
	function again() {
		socket?.close();
		socket = null;
		reset();
		void connect();
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
		get question() {
			return question;
		},
		get result() {
			return result;
		},
		get picked() {
			return picked;
		},
		get end() {
			return end;
		},
		get score() {
			return score;
		},
		get lives() {
			return lives;
		},
		get streak() {
			return streak;
		},
		get correctCount() {
			return correctCount;
		},
		answer,
		again,
		close: () => {
			disposed = true;
			generation += 1;
			socket?.close();
		}
	};
}

export type ArcadeRun = ReturnType<typeof createArcadeRun>;
