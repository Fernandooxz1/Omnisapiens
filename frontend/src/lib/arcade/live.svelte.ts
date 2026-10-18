import { ApiError } from '#lib/api/client';
import { connectArcade, type Envelope, type Socket, type SocketStatus } from '#lib/api/ws';
import { isCategory, type Category } from '#lib/categories';

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
	category: Category;
	difficulty: number;
	/** Duración total de esta pregunta (baja con los aciertos). */
	seconds: number;
	endsAt: number;
	score: number;
	lives: number;
	streak: number;
	correctCount: number;
}

export interface ArcadeScore {
	/** `null` si no llegó a responder. */
	choice: number | null;
	ms: number;
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

interface QuestionWire {
	round: number;
	prompt: string;
	options: string[];
	category: string;
	difficulty: number;
	seconds: number;
	ends_at: number;
	score: number;
	lives: number;
	streak: number;
	correct_count: number;
}

interface ResultWire {
	round: number;
	correct_index: number;
	you?: Partial<ArcadeScore>;
	score: number;
	lives: number;
	streak: number;
	correct_count: number;
}

interface EndWire {
	run_id: string;
	score: number;
	correct_count: number;
	max_difficulty: number;
	longest_streak: number;
	rank_global: number | null;
	rank_weekly: number | null;
	personal_best: number | null;
	is_new_best: boolean;
}

function category(value: string): Category {
	return isCategory(value) ? value : 'science';
}

function asScore(value: unknown): ArcadeScore {
	const raw = (value ?? {}) as Partial<ArcadeScore>;
	return {
		choice: raw.choice ?? null,
		ms: raw.ms ?? 0,
		points: raw.points ?? 0,
		correct: raw.correct ?? false
	};
}

/**
 * Una corrida arcade vista desde el socket. `start` vale una vez por conexión:
 * para otra corrida se cierra y se abre otra (`again`).
 */
export function createArcadeRun(token: string) {
	let phase = $state<ArcadePhase>('connecting');
	let status = $state<SocketStatus>('connecting');
	let failure = $state<ApiError | null>(null);
	/** Error suelto del servidor (`NO_QUESTIONS`, `RUN_NOT_STARTED`…). */
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
	/** El socket viejo no puede pisar el estado del nuevo al reconectar o reintentar. */
	let generation = 0;

	function onMessage(message: Envelope) {
		switch (message.t) {
			case 'arcade_start': {
				const start = message.d as StartWire;
				score = 0;
				lives = start.lives;
				streak = 0;
				correctCount = 0;
				phase = 'starting';
				break;
			}
			case 'arcade_question': {
				const next = message.d as QuestionWire;
				question = {
					round: next.round,
					prompt: next.prompt,
					options: next.options,
					category: category(next.category),
					difficulty: next.difficulty,
					seconds: next.seconds,
					endsAt: next.ends_at,
					score: next.score,
					lives: next.lives,
					streak: next.streak,
					correctCount: next.correct_count
				};
				score = next.score;
				lives = next.lives;
				streak = next.streak;
				correctCount = next.correct_count;
				picked = null;
				result = null;
				notice = null;
				phase = 'question';
				break;
			}
			case 'arcade_result': {
				const resolved = message.d as ResultWire;
				result = {
					round: resolved.round,
					correctIndex: resolved.correct_index,
					you: asScore(resolved.you),
					score: resolved.score,
					lives: resolved.lives,
					streak: resolved.streak,
					correctCount: resolved.correct_count
				};
				score = resolved.score;
				lives = resolved.lives;
				streak = resolved.streak;
				correctCount = resolved.correct_count;
				picked = result.you.choice;
				phase = 'reveal';
				break;
			}
			case 'arcade_end': {
				const final = message.d as EndWire;
				end = {
					runId: final.run_id,
					score: final.score,
					correctCount: final.correct_count,
					maxDifficulty: final.max_difficulty,
					longestStreak: final.longest_streak,
					rankGlobal: final.rank_global,
					rankWeekly: final.rank_weekly,
					personalBest: final.personal_best,
					isNewBest: final.is_new_best
				};
				score = final.score;
				correctCount = final.correct_count;
				phase = 'over';
				// La corrida terminó: el socket ya no tiene nada que hacer (y `start`
				// vale una vez por conexión). `again` abre uno nuevo.
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

	function connect() {
		const mine = ++generation;

		socket = connectArcade(token, {
			onMessage: (message) => {
				if (mine === generation) onMessage(message);
			},
			onStatus: (next) => {
				if (mine === generation) status = next;
			},
			// `start` vale una vez por conexión: al abrir (o reabrir) arranca la corrida.
			onOpen: () => {
				if (mine === generation) socket?.send('start');
			},
			onRejected: (error) => {
				if (mine !== generation) return;
				failure = error;
				phase = 'over';
			}
		});
	}

	connect();

	function answer(choice: number) {
		if (phase !== 'question' || !question) return;
		// Sin canal no se manda: la corrida no se puede reanudar (es de una conexión).
		if (!socket?.send('answer', { round: question.round, choice })) return;

		picked = choice;
		phase = 'answered';
	}

	/** Otra corrida: la anterior ya terminó, así que se abre una conexión nueva. */
	function again() {
		socket?.close();
		reset();
		connect();
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
		close: () => socket?.close()
	};
}

export type ArcadeRun = ReturnType<typeof createArcadeRun>;
