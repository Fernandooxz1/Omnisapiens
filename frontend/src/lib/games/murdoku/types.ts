import type { Cell, CaseMeta } from '../types.ts';

/** Nombres de los SVG propios: el tablero los dibuja en la fase 3. */
export type PropIcon =
	| 'shelf'
	| 'piano'
	| 'plant'
	| 'clock'
	| 'chest'
	| 'statue'
	| 'painting'
	| 'lamp';

export type SuspectColor = 'green' | 'blue' | 'yellow' | 'orange' | 'pink' | 'purple' | 'red';

/**
 * Pistas como AST: el solver las evalúa y la UI las traduce.
 * `direction` fija un solo eje (`N`/`S` la fila, `E`/`W` la columna) porque ya
 * hay exactamente una persona por fila y por columna.
 */
export type Clue =
	| { type: 'region'; who: string; region: number }
	| { type: 'notRegion'; who: string; region: number }
	| { type: 'direction'; who: string; dir: 'N' | 'S' | 'E' | 'W'; steps: number; than: string }
	| { type: 'adjacent'; a: string; b: string; diagonal: boolean }
	| { type: 'sameRegion'; a: string; b: string }
	| { type: 'notSameRegion'; a: string; b: string }
	| { type: 'nearProp'; who: string; prop: string }
	| { type: 'rowEdge'; who: string; edge: 'top' | 'bottom' }
	| { type: 'colEdge'; who: string; edge: 'left' | 'right' };

export interface MurdokuRegion {
	id: number;
	name: string;
	/** 0..5: elige un tinte neutro del tablero. */
	tone: number;
}

export interface MurdokuProp {
	id: string;
	name: string;
	icon: PropIcon;
	row: number;
	col: number;
}

export interface MurdokuSuspect {
	id: string;
	name: string;
	/** Única en el caso. */
	initial: string;
	color: SuspectColor;
	clues: Clue[];
}

export interface MurdokuCase extends CaseMeta {
	game: 'murdoku';
	grid: {
		size: number;
		/** Región por celda, `[row][col]`. */
		regions: number[][];
		regionList: MurdokuRegion[];
		props: MurdokuProp[];
	};
	suspects: MurdokuSuspect[];
	victim: {
		name: string;
		row: number;
		col: number;
	};
	/** Sospechoso → celda de la solución única. */
	solution: Record<string, Cell>;
	/** Sospechoso que queda a solas con la víctima. */
	killer: string;
	meta: {
		seed: number;
		clueCount: number;
		negatives: number;
		complexity: number;
		generatedBy: string;
	};
}
