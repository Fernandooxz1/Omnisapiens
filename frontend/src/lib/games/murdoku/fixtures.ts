import type { CasePreview } from '../types.ts';
import type { MurdokuCase } from './types.ts';

/**
 * Dos casos reales escritos a mano: previews del catálogo y base de los tests.
 * El catálogo publicado vive en `cases/`.
 */

const study: MurdokuCase = {
	id: 'murdoku-001',
	game: 'murdoku',
	number: 1,
	title: 'El estudio',
	setting: 'Una mansión a medianoche',
	difficulty: 'very_easy',
	size: 5,
	estimatedMinutes: 3,
	tutorial: true,
	grid: {
		size: 5,
		regions: [
			[0, 0, 0, 1, 1],
			[0, 0, 1, 1, 1],
			[2, 2, 2, 3, 3],
			[2, 2, 3, 3, 3],
			[2, 2, 3, 3, 3]
		],
		regionList: [
			{ id: 0, name: 'Estudio', tone: 0 },
			{ id: 1, name: 'Biblioteca', tone: 1 },
			{ id: 2, name: 'Cocina', tone: 2 },
			{ id: 3, name: 'Jardín', tone: 3 }
		],
		props: [
			{ id: 'piano', name: 'piano', icon: 'piano', row: 1, col: 0 },
			{ id: 'planta', name: 'planta', icon: 'plant', row: 3, col: 1 },
			{ id: 'reloj', name: 'reloj', icon: 'clock', row: 3, col: 4 }
		]
	},
	suspects: [
		{
			id: 's1',
			name: 'Blake',
			initial: 'B',
			color: 'green',
			clues: [
				{ type: 'rowEdge', who: 's1', edge: 'top' },
				{ type: 'nearProp', who: 's1', prop: 'piano' }
			]
		},
		{
			id: 's2',
			name: 'Cruz',
			initial: 'C',
			color: 'blue',
			clues: [
				{ type: 'region', who: 's2', region: 1 },
				{ type: 'colEdge', who: 's2', edge: 'right' }
			]
		},
		{
			id: 's3',
			name: 'Duarte',
			initial: 'D',
			color: 'orange',
			clues: [
				{ type: 'rowEdge', who: 's3', edge: 'bottom' },
				{ type: 'nearProp', who: 's3', prop: 'planta' }
			]
		},
		{
			id: 's4',
			name: 'Evans',
			initial: 'E',
			color: 'purple',
			clues: [
				{ type: 'region', who: 's4', region: 3 },
				{ type: 'nearProp', who: 's4', prop: 'reloj' }
			]
		}
	],
	victim: { name: 'Marta', row: 2, col: 2 },
	solution: {
		s1: { row: 0, col: 0 },
		s2: { row: 1, col: 4 },
		s3: { row: 4, col: 1 },
		s4: { row: 3, col: 3 }
	},
	killer: 's3',
	meta: { seed: 1, clueCount: 8, negatives: 0, complexity: 1, generatedBy: 'fixtures' }
};

const library: MurdokuCase = {
	id: 'murdoku-021',
	game: 'murdoku',
	number: 21,
	title: 'La biblioteca',
	setting: 'Una biblioteca cerrada al público',
	difficulty: 'medium',
	size: 9,
	estimatedMinutes: 10,
	grid: {
		size: 9,
		regions: [
			[0, 0, 0, 0, 0, 1, 1, 1, 1],
			[0, 0, 0, 0, 0, 1, 1, 1, 1],
			[0, 0, 0, 0, 0, 1, 1, 1, 1],
			[2, 2, 2, 2, 2, 3, 3, 3, 3],
			[2, 2, 2, 2, 2, 3, 3, 3, 3],
			[2, 2, 2, 2, 2, 3, 3, 3, 3],
			[4, 4, 4, 4, 4, 5, 5, 5, 5],
			[4, 4, 4, 4, 4, 5, 5, 5, 5],
			[4, 4, 4, 4, 4, 5, 5, 5, 5]
		],
		regionList: [
			{ id: 0, name: 'Vestíbulo', tone: 0 },
			{ id: 1, name: 'Galería', tone: 1 },
			{ id: 2, name: 'Sala de lectura', tone: 2 },
			{ id: 3, name: 'Depósito', tone: 3 },
			{ id: 4, name: 'Patio', tone: 4 },
			{ id: 5, name: 'Torre', tone: 5 }
		],
		props: [
			{ id: 'piano', name: 'piano', icon: 'piano', row: 0, col: 7 },
			{ id: 'planta', name: 'planta', icon: 'plant', row: 5, col: 0 },
			{ id: 'estanteria', name: 'estantería', icon: 'shelf', row: 5, col: 3 },
			{ id: 'reloj', name: 'reloj', icon: 'clock', row: 1, col: 2 },
			{ id: 'baul', name: 'baúl', icon: 'chest', row: 8, col: 4 },
			{ id: 'estatua', name: 'estatua', icon: 'statue', row: 1, col: 8 },
			{ id: 'cuadro', name: 'cuadro', icon: 'painting', row: 4, col: 8 },
			{ id: 'lampara', name: 'lámpara', icon: 'lamp', row: 7, col: 7 }
		]
	},
	suspects: [
		{
			id: 's1',
			name: 'Ari',
			initial: 'A',
			color: 'green',
			clues: [
				{ type: 'rowEdge', who: 's1', edge: 'top' },
				{ type: 'nearProp', who: 's1', prop: 'reloj' }
			]
		},
		{
			id: 's2',
			name: 'Beltrán',
			initial: 'B',
			color: 'blue',
			clues: [{ type: 'region', who: 's2', region: 0 }]
		},
		{
			id: 's3',
			name: 'Cora',
			initial: 'C',
			color: 'yellow',
			clues: [
				{ type: 'region', who: 's3', region: 1 },
				{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's4' }
			]
		},
		{
			id: 's4',
			name: 'Damián',
			initial: 'D',
			color: 'orange',
			clues: [
				{ type: 'region', who: 's4', region: 3 },
				{ type: 'direction', who: 's4', dir: 'S', steps: 1, than: 's3' }
			]
		},
		{
			id: 's5',
			name: 'Elena',
			initial: 'E',
			color: 'pink',
			clues: [
				{ type: 'region', who: 's5', region: 2 },
				{ type: 'nearProp', who: 's5', prop: 'planta' }
			]
		},
		{
			id: 's6',
			name: 'Fabio',
			initial: 'F',
			color: 'purple',
			clues: [
				{ type: 'colEdge', who: 's6', edge: 'right' },
				{ type: 'region', who: 's6', region: 5 }
			]
		},
		{
			id: 's7',
			name: 'Greta',
			initial: 'G',
			color: 'red',
			clues: [
				{ type: 'colEdge', who: 's7', edge: 'left' },
				{ type: 'direction', who: 's7', dir: 'S', steps: 1, than: 's6' }
			]
		},
		{
			id: 's8',
			name: 'Hugo',
			initial: 'H',
			color: 'blue',
			clues: [
				{ type: 'rowEdge', who: 's8', edge: 'bottom' },
				{ type: 'nearProp', who: 's8', prop: 'lampara' }
			]
		}
	],
	victim: { name: 'Vera', row: 4, col: 4 },
	solution: {
		s1: { row: 0, col: 2 },
		s2: { row: 1, col: 3 },
		s3: { row: 2, col: 5 },
		s4: { row: 3, col: 6 },
		s5: { row: 5, col: 1 },
		s6: { row: 6, col: 8 },
		s7: { row: 7, col: 0 },
		s8: { row: 8, col: 7 }
	},
	killer: 's5',
	meta: { seed: 21, clueCount: 15, negatives: 0, complexity: 1, generatedBy: 'fixtures' }
};

export const fixtureCases: MurdokuCase[] = [study, library];

/** El catálogo dibuja sobres antes de cargar el caso completo. */
export function toPreview(entry: MurdokuCase): CasePreview {
	return {
		meta: {
			id: entry.id,
			game: entry.game,
			number: entry.number,
			title: entry.title,
			setting: entry.setting,
			difficulty: entry.difficulty,
			size: entry.size,
			estimatedMinutes: entry.estimatedMinutes,
			tutorial: entry.tutorial
		},
		regions: entry.grid.regions,
		victim: { row: entry.victim.row, col: entry.victim.col }
	};
}

export const fixturePreviews: CasePreview[] = fixtureCases.map(toPreview);
