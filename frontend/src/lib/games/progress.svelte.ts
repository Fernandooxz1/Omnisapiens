import type { Cell, GameId } from './types';

/**
 * Progreso local de la sección de juegos: sin cuenta, sin red y sin ranking.
 * Si el navegador limpia el storage se pierde; es aceptado en v1.
 */
export const PROGRESS_KEY = 'omnisapiens.games.v1';
export const PROGRESS_VERSION = 1;

export interface ResumeState {
	placements: Record<string, Cell>;
	/** Celdas marcadas con X, con el formato "fila,columna". */
	marks: string[];
	elapsedMs: number;
	hintsUsed: number;
	updatedAt: string;
}

export interface CaseProgress {
	solved: boolean;
	bestMs: number | null;
	lastMs: number | null;
	/** Pistas usadas en la última resolución. */
	hints: number;
	solvedAt: string | null;
	lastPlayedAt: string | null;
	resume: ResumeState | null;
}

export interface GameProgress {
	version: typeof PROGRESS_VERSION;
	cases: Record<string, CaseProgress>;
}

function emptyProgress(): GameProgress {
	return { version: PROGRESS_VERSION, cases: {} };
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function numberOrNull(value: unknown): number | null {
	return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function textOrNull(value: unknown): string | null {
	return typeof value === 'string' ? value : null;
}

function countOrZero(value: unknown): number {
	return typeof value === 'number' && Number.isFinite(value) && value > 0 ? Math.trunc(value) : 0;
}

function parseCell(value: unknown): Cell | null {
	if (!isRecord(value) || typeof value.row !== 'number' || typeof value.col !== 'number') return null;
	return { row: Math.trunc(value.row), col: Math.trunc(value.col) };
}

function parseResume(value: unknown): ResumeState | null {
	if (!isRecord(value)) return null;

	const placements: Record<string, Cell> = {};
	if (isRecord(value.placements)) {
		for (const [id, cell] of Object.entries(value.placements)) {
			const parsed = parseCell(cell);
			if (parsed) placements[id] = parsed;
		}
	}

	const marks = Array.isArray(value.marks)
		? value.marks.filter((mark): mark is string => typeof mark === 'string')
		: [];

	return {
		placements,
		marks,
		elapsedMs: countOrZero(value.elapsedMs),
		hintsUsed: countOrZero(value.hintsUsed),
		updatedAt: textOrNull(value.updatedAt) ?? new Date().toISOString()
	};
}

function parseCase(value: unknown): CaseProgress | null {
	if (!isRecord(value)) return null;

	return {
		solved: value.solved === true,
		bestMs: numberOrNull(value.bestMs),
		lastMs: numberOrNull(value.lastMs),
		hints: countOrZero(value.hints),
		solvedAt: textOrNull(value.solvedAt),
		lastPlayedAt: textOrNull(value.lastPlayedAt),
		resume: parseResume(value.resume)
	};
}

/** Un JSON roto, una versión vieja o casos desconocidos no rompen la pantalla. */
function parseProgress(raw: string | null): GameProgress {
	if (!raw) return emptyProgress();

	try {
		const data: unknown = JSON.parse(raw);
		if (!isRecord(data) || data.version !== PROGRESS_VERSION || !isRecord(data.cases)) {
			return emptyProgress();
		}

		const cases: Record<string, CaseProgress> = {};
		for (const [id, value] of Object.entries(data.cases)) {
			const parsed = parseCase(value);
			if (parsed) cases[id] = parsed;
		}

		return { version: PROGRESS_VERSION, cases };
	} catch {
		return emptyProgress();
	}
}

function canStore(): boolean {
	return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
}

function load(): GameProgress {
	if (!canStore()) return emptyProgress();

	try {
		return parseProgress(localStorage.getItem(PROGRESS_KEY));
	} catch {
		return emptyProgress();
	}
}

function persist(progress: GameProgress): void {
	if (!canStore()) return;

	try {
		localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
	} catch {
		/* sin persistencia: el progreso igual vale para esta sesión */
	}
}

function emptyCase(): CaseProgress {
	return {
		solved: false,
		bestMs: null,
		lastMs: null,
		hints: 0,
		solvedAt: null,
		lastPlayedAt: null,
		resume: null
	};
}

let store = $state<GameProgress>(load());

export function getCaseProgress(caseId: string): CaseProgress | undefined {
	return store.cases[caseId];
}

/** Fusiona el parche sobre la entrada existente y guarda; no borra campos que no vengan. */
export function saveCaseProgress(caseId: string, patch: Partial<CaseProgress>): void {
	const current = store.cases[caseId];
	const next: CaseProgress = { ...(current ?? emptyCase()), ...patch };

	store.cases = { ...store.cases, [caseId]: next };
	persist(store);
}

export function removeResume(caseId: string): void {
	const current = store.cases[caseId];
	if (!current?.resume) return;

	store.cases = { ...store.cases, [caseId]: { ...current, resume: null } };
	persist(store);
}

export function clearAll(): void {
	store = emptyProgress();
	if (!canStore()) return;

	try {
		localStorage.removeItem(PROGRESS_KEY);
	} catch {
		/* sin storage no hay nada que borrar */
	}
}

/** Cada juego numera sus casos con su id delante: `murdoku-001`. */
export function countSolved(game: GameId): number {
	return Object.entries(store.cases).filter(
		([id, entry]) => entry.solved && id.startsWith(`${game}-`)
	).length;
}
