import type { MurdokuCase } from '../types.ts';

/** Generado por `npm run games:generate -- --min-size 10` (semilla base 20261022). No editar a mano. */
export const largeCases: MurdokuCase[] = [
	{
		id: 'murdoku-049',
		game: 'murdoku',
		number: 49,
		title: 'Polvo en el piano',
		setting: 'Una mansión a medianoche',
		difficulty: 'hard',
		size: 10,
		estimatedMinutes: 14,
		grid: {
			size: 10,
			regions: [
				[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 3, 1, 3, 3, 1, 1, 1],
				[1, 3, 3, 3, 3, 3, 3, 4, 1, 1],
				[0, 0, 3, 3, 3, 3, 5, 4, 4, 4],
				[0, 0, 3, 3, 3, 3, 5, 4, 4, 4],
				[2, 2, 2, 3, 3, 3, 5, 4, 4, 4]
			],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 },
				{ id: 4, name: 'Jardín', tone: 4 },
				{ id: 5, name: 'Terraza', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'candelabro', icon: 'lamp', row: 6, col: 7 },
				{ id: 'p2', name: 'cuadro', icon: 'painting', row: 8, col: 1 },
				{ id: 'p3', name: 'retrato', icon: 'painting', row: 9, col: 6 },
				{ id: 'p4', name: 'baúl', icon: 'chest', row: 9, col: 1 },
				{ id: 'p5', name: 'estatua', icon: 'statue', row: 9, col: 3 },
				{ id: 'p6', name: 'piano', icon: 'piano', row: 8, col: 9 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Irene',
				initial: 'I',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 6, than: 's2' },
					{ type: 'region', who: 's1', region: 1 }
				]
			},
			{
				id: 's2',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 2, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Olivia',
				initial: 'O',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 2, than: 's4' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's7' }
				]
			},
			{
				id: 's4',
				name: 'Karina',
				initial: 'K',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'N', steps: 3, than: 's6' },
					{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's1' }
				]
			},
			{
				id: 's5',
				name: 'Marta',
				initial: 'M',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'W', steps: 3, than: 's2' },
					{ type: 'direction', who: 's5', dir: 'N', steps: 1, than: 's3' }
				]
			},
			{
				id: 's6',
				name: 'Fabián',
				initial: 'F',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'S', steps: 3, than: 's4' }]
			},
			{
				id: 's7',
				name: 'Elena',
				initial: 'E',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'S', steps: 6, than: 's3' }]
			},
			{
				id: 's8',
				name: 'Gabriela',
				initial: 'G',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'S', steps: 5, than: 's2' },
					{ type: 'region', who: 's8', region: 2 }
				]
			},
			{
				id: 's9',
				name: 'Lorenzo',
				initial: 'L',
				color: 'blue',
				clues: [{ type: 'direction', who: 's9', dir: 'W', steps: 2, than: 's2' }]
			}
		],
		victim: { name: 'Óscar', row: 6, col: 3 },
		solution: {
			s1: { row: 5, col: 1 },
			s2: { row: 4, col: 7 },
			s3: { row: 2, col: 9 },
			s4: { row: 0, col: 0 },
			s5: { row: 1, col: 4 },
			s6: { row: 3, col: 6 },
			s7: { row: 8, col: 8 },
			s8: { row: 9, col: 2 },
			s9: { row: 7, col: 5 }
		},
		killer: 's9',
		meta: { seed: 20649053, clueCount: 14, negatives: 0, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-050',
		game: 'murdoku',
		number: 50,
		title: 'La sala de mapas',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'hard',
		size: 10,
		estimatedMinutes: 14,
		grid: {
			size: 10,
			regions: [
				[1, 1, 1, 1, 2, 2, 4, 4, 4, 4],
				[1, 1, 1, 1, 2, 2, 4, 4, 4, 5],
				[1, 1, 1, 2, 2, 2, 2, 4, 4, 5],
				[1, 1, 2, 2, 2, 2, 4, 4, 4, 5],
				[3, 3, 2, 2, 2, 2, 4, 4, 4, 4],
				[3, 3, 2, 2, 2, 2, 4, 4, 4, 4],
				[3, 3, 2, 2, 2, 2, 4, 4, 4, 4],
				[3, 2, 2, 2, 0, 0, 0, 0, 0, 0],
				[3, 3, 2, 0, 0, 0, 0, 0, 0, 0],
				[3, 3, 3, 0, 0, 0, 0, 0, 0, 0]
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
				{ id: 'p1', name: 'reloj', icon: 'clock', row: 5, col: 0 },
				{ id: 'p2', name: 'cofre', icon: 'chest', row: 0, col: 3 },
				{ id: 'p3', name: 'estatua', icon: 'statue', row: 6, col: 5 },
				{ id: 'p4', name: 'estantería', icon: 'shelf', row: 0, col: 0 },
				{ id: 'p5', name: 'busto', icon: 'statue', row: 1, col: 0 },
				{ id: 'p6', name: 'atril', icon: 'shelf', row: 1, col: 2 },
				{ id: 'p7', name: 'cuadro', icon: 'painting', row: 7, col: 3 },
				{ id: 'p8', name: 'lámpara', icon: 'lamp', row: 2, col: 6 },
				{ id: 'p9', name: 'planta', icon: 'plant', row: 7, col: 5 },
				{ id: 'p10', name: 'candelabro', icon: 'lamp', row: 9, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 5, than: 's3' },
					{ type: 'rowEdge', who: 's1', edge: 'top' }
				]
			},
			{
				id: 's2',
				name: 'Elena',
				initial: 'E',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 2 }, { type: 'nearProp', who: 's2', prop: 'p1' }]
			},
			{
				id: 's3',
				name: 'Alicia',
				initial: 'A',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'E', steps: 9, than: 's2' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's6' }
				]
			},
			{
				id: 's4',
				name: 'Julián',
				initial: 'J',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 4, than: 's3' }]
			},
			{
				id: 's5',
				name: 'Marta',
				initial: 'M',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'W', steps: 2, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Irene',
				initial: 'I',
				color: 'purple',
				clues: [
					{ type: 'notRegion', who: 's6', region: 1 },
					{ type: 'direction', who: 's6', dir: 'N', steps: 1, than: 's7' }
				]
			},
			{
				id: 's7',
				name: 'Fabián',
				initial: 'F',
				color: 'red',
				clues: [
					{ type: 'notRegion', who: 's7', region: 3 },
					{ type: 'direction', who: 's7', dir: 'E', steps: 1, than: 's2' }
				]
			},
			{
				id: 's8',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's8', region: 2 }]
			},
			{
				id: 's9',
				name: 'Bruno',
				initial: 'B',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'N', steps: 7, than: 's4' },
					{ type: 'region', who: 's9', region: 2 }
				]
			}
		],
		victim: { name: 'Lucía', row: 3, col: 6 },
		solution: {
			s1: { row: 0, col: 4 },
			s2: { row: 4, col: 0 },
			s3: { row: 1, col: 9 },
			s4: { row: 9, col: 5 },
			s5: { row: 5, col: 2 },
			s6: { row: 6, col: 8 },
			s7: { row: 7, col: 1 },
			s8: { row: 8, col: 7 },
			s9: { row: 2, col: 3 }
		},
		killer: 's6',
		meta: { seed: 20656972, clueCount: 15, negatives: 4, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-051',
		game: 'murdoku',
		number: 51,
		title: 'La regadera olvidada',
		setting: 'Un invernadero al amanecer',
		difficulty: 'hard',
		size: 10,
		estimatedMinutes: 14,
		grid: {
			size: 10,
			regions: [
				[4, 4, 4, 4, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 3, 3, 3, 3, 3],
				[1, 1, 1, 4, 3, 3, 3, 3, 3, 3],
				[1, 1, 1, 1, 3, 3, 3, 3, 3, 3],
				[1, 1, 1, 3, 3, 3, 3, 3, 3, 3],
				[1, 1, 1, 3, 3, 3, 3, 3, 3, 3],
				[2, 2, 2, 2, 3, 3, 3, 0, 0, 3],
				[2, 2, 2, 2, 2, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 2, 0, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'candelabro', icon: 'lamp', row: 4, col: 5 },
				{ id: 'p2', name: 'piano', icon: 'piano', row: 7, col: 6 },
				{ id: 'p3', name: 'maceta', icon: 'plant', row: 3, col: 3 },
				{ id: 'p4', name: 'arcón', icon: 'chest', row: 7, col: 3 },
				{ id: 'p5', name: 'lámpara', icon: 'lamp', row: 2, col: 9 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 2, than: 's4' }]
			},
			{
				id: 's2',
				name: 'Alicia',
				initial: 'A',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'E', steps: 3, than: 's1' },
					{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's1' }
				]
			},
			{
				id: 's3',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'W', steps: 2, than: 's2' },
					{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's1' }
				]
			},
			{
				id: 's4',
				name: 'Karina',
				initial: 'K',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 0 },
					{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's9' }
				]
			},
			{
				id: 's5',
				name: 'Marta',
				initial: 'M',
				color: 'pink',
				clues: [{ type: 'notRegion', who: 's5', region: 1 }]
			},
			{
				id: 's6',
				name: 'Elena',
				initial: 'E',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'S', steps: 5, than: 's3' }]
			},
			{
				id: 's7',
				name: 'Carla',
				initial: 'C',
				color: 'red',
				clues: [{ type: 'notRegion', who: 's7', region: 1 }]
			},
			{
				id: 's8',
				name: 'Fabián',
				initial: 'F',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'W', steps: 3, than: 's1' },
					{ type: 'direction', who: 's8', dir: 'E', steps: 1, than: 's5' }
				]
			},
			{
				id: 's9',
				name: 'Bruno',
				initial: 'B',
				color: 'blue',
				clues: [{ type: 'direction', who: 's9', dir: 'N', steps: 5, than: 's2' }]
			}
		],
		victim: { name: 'Lucía', row: 8, col: 1 },
		solution: {
			s1: { row: 5, col: 6 },
			s2: { row: 6, col: 9 },
			s3: { row: 4, col: 7 },
			s4: { row: 3, col: 4 },
			s5: { row: 0, col: 2 },
			s6: { row: 9, col: 8 },
			s7: { row: 7, col: 0 },
			s8: { row: 2, col: 3 },
			s9: { row: 1, col: 5 }
		},
		killer: 's7',
		meta: { seed: 21188536, clueCount: 13, negatives: 3, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-052',
		game: 'murdoku',
		number: 52,
		title: 'La despensa abierta',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'hard',
		size: 10,
		estimatedMinutes: 14,
		grid: {
			size: 10,
			regions: [
				[0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
				[0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
				[0, 0, 0, 1, 1, 1, 1, 1, 1, 2],
				[0, 0, 0, 1, 1, 1, 1, 3, 2, 2],
				[0, 0, 0, 0, 1, 3, 3, 3, 2, 2],
				[0, 0, 0, 0, 3, 3, 3, 2, 2, 2],
				[0, 0, 0, 0, 3, 3, 2, 2, 2, 2],
				[0, 0, 0, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 2, 2, 2, 2, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'aparador', icon: 'shelf', row: 5, col: 9 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 0, col: 5 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 7, col: 6 },
				{ id: 'p4', name: 'piano', icon: 'piano', row: 9, col: 5 },
				{ id: 'p5', name: 'figura', icon: 'statue', row: 2, col: 5 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 7, col: 1 },
				{ id: 'p7', name: 'planta aromática', icon: 'plant', row: 1, col: 2 },
				{ id: 'p8', name: 'baúl', icon: 'chest', row: 5, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Gabriela',
				initial: 'G',
				color: 'green',
				clues: [
					{ type: 'notRegion', who: 's1', region: 2 },
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's6' }
				]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 4, than: 's5' }]
			},
			{
				id: 's3',
				name: 'Karina',
				initial: 'K',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 3, than: 's4' }]
			},
			{
				id: 's4',
				name: 'Julián',
				initial: 'J',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 0 }]
			},
			{
				id: 's5',
				name: 'Diego',
				initial: 'D',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'E', steps: 4, than: 's2' }]
			},
			{
				id: 's6',
				name: 'Olivia',
				initial: 'O',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'S', steps: 3, than: 's3' }]
			},
			{
				id: 's7',
				name: 'Hugo',
				initial: 'H',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'N', steps: 7, than: 's6' },
					{ type: 'region', who: 's7', region: 0 }
				]
			},
			{
				id: 's8',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'S', steps: 3, than: 's5' },
					{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's1' }
				]
			},
			{
				id: 's9',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'W', steps: 2, than: 's4' },
					{ type: 'rowEdge', who: 's9', edge: 'bottom' }
				]
			}
		],
		victim: { name: 'Nadia', row: 3, col: 7 },
		solution: {
			s1: { row: 6, col: 2 },
			s2: { row: 0, col: 0 },
			s3: { row: 5, col: 5 },
			s4: { row: 2, col: 8 },
			s5: { row: 4, col: 4 },
			s6: { row: 8, col: 3 },
			s7: { row: 1, col: 1 },
			s8: { row: 7, col: 9 },
			s9: { row: 9, col: 6 }
		},
		killer: 's3',
		meta: { seed: 20882268, clueCount: 13, negatives: 2, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-053',
		game: 'murdoku',
		number: 53,
		title: 'El inventario incompleto',
		setting: 'Un museo después del cierre',
		difficulty: 'hard',
		size: 10,
		estimatedMinutes: 14,
		grid: {
			size: 10,
			regions: [
				[1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
				[4, 1, 1, 1, 3, 3, 3, 3, 5, 5],
				[4, 4, 4, 4, 3, 3, 3, 3, 5, 5],
				[4, 4, 4, 4, 3, 3, 3, 3, 5, 5],
				[4, 4, 4, 4, 3, 3, 3, 5, 5, 5],
				[4, 4, 4, 4, 4, 3, 3, 5, 5, 5],
				[4, 4, 4, 4, 4, 2, 2, 2, 2, 2],
				[4, 4, 4, 4, 2, 2, 2, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Sala egipcia', tone: 1 },
				{ id: 2, name: 'Sala griega', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 },
				{ id: 5, name: 'Patio', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'retrato', icon: 'painting', row: 8, col: 4 },
				{ id: 'p2', name: 'cofre', icon: 'chest', row: 0, col: 9 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 4, col: 7 },
				{ id: 'p4', name: 'vitrina', icon: 'shelf', row: 1, col: 6 },
				{ id: 'p5', name: 'planta', icon: 'plant', row: 2, col: 3 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 4, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 4 }]
			},
			{
				id: 's2',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 4 }]
			},
			{
				id: 's3',
				name: 'Fabián',
				initial: 'F',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'W', steps: 5, than: 's2' },
					{ type: 'colEdge', who: 's3', edge: 'left' }
				]
			},
			{
				id: 's4',
				name: 'Elena',
				initial: 'E',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 1 },
					{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's2' }
				]
			},
			{
				id: 's5',
				name: 'Diego',
				initial: 'D',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'E', steps: 3, than: 's4' },
					{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's7' }
				]
			},
			{
				id: 's6',
				name: 'Bruno',
				initial: 'B',
				color: 'purple',
				clues: [{ type: 'notRegion', who: 's6', region: 2 }]
			},
			{
				id: 's7',
				name: 'Karina',
				initial: 'K',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'N', steps: 2, than: 's1' },
					{ type: 'nearProp', who: 's7', prop: 'p4' }
				]
			},
			{
				id: 's8',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'W', steps: 3, than: 's1' },
					{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's6' }
				]
			},
			{
				id: 's9',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'W', steps: 4, than: 's1' },
					{ type: 'direction', who: 's9', dir: 'N', steps: 1, than: 's6' }
				]
			}
		],
		victim: { name: 'Tomás', row: 4, col: 8 },
		solution: {
			s1: { row: 3, col: 6 },
			s2: { row: 9, col: 5 },
			s3: { row: 0, col: 0 },
			s4: { row: 8, col: 1 },
			s5: { row: 2, col: 4 },
			s6: { row: 6, col: 9 },
			s7: { row: 1, col: 7 },
			s8: { row: 7, col: 3 },
			s9: { row: 5, col: 2 }
		},
		killer: 's6',
		meta: { seed: 20785458, clueCount: 15, negatives: 4, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-054',
		game: 'murdoku',
		number: 54,
		title: 'Una maleta sin dueño',
		setting: 'Un tren nocturno detenido',
		difficulty: 'hard',
		size: 10,
		estimatedMinutes: 14,
		grid: {
			size: 10,
			regions: [
				[1, 1, 1, 1, 1, 1, 3, 3, 3, 3],
				[1, 1, 1, 1, 1, 3, 3, 3, 3, 3],
				[1, 1, 1, 1, 1, 1, 3, 3, 3, 3],
				[1, 1, 1, 1, 1, 1, 3, 3, 2, 2],
				[1, 1, 1, 1, 1, 1, 1, 2, 2, 2],
				[1, 1, 1, 1, 4, 1, 2, 2, 2, 2],
				[1, 1, 0, 1, 4, 4, 2, 2, 2, 2],
				[0, 1, 0, 4, 4, 4, 4, 4, 2, 2],
				[0, 0, 0, 4, 4, 4, 4, 4, 2, 2],
				[0, 0, 0, 4, 4, 4, 4, 4, 4, 4]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'planta', icon: 'plant', row: 0, col: 1 },
				{ id: 'p2', name: 'baúl', icon: 'chest', row: 1, col: 2 },
				{ id: 'p3', name: 'maleta', icon: 'chest', row: 7, col: 4 },
				{ id: 'p4', name: 'candelabro', icon: 'lamp', row: 9, col: 9 },
				{ id: 'p5', name: 'estantería', icon: 'shelf', row: 2, col: 6 },
				{ id: 'p6', name: 'lámpara', icon: 'lamp', row: 8, col: 9 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Fabián',
				initial: 'F',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 4 }]
			},
			{
				id: 's2',
				name: 'Julián',
				initial: 'J',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 6, than: 's6' }]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 4, than: 's4' }]
			},
			{
				id: 's4',
				name: 'Elena',
				initial: 'E',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'W', steps: 3, than: 's2' },
					{ type: 'nearProp', who: 's4', prop: 'p5' }
				]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'E', steps: 4, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Irene',
				initial: 'I',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'S', steps: 6, than: 's2' }]
			},
			{
				id: 's7',
				name: 'Diego',
				initial: 'D',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'S', steps: 9, than: 's3' },
					{ type: 'direction', who: 's7', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's8',
				name: 'Gabriela',
				initial: 'G',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'S', steps: 3, than: 's2' },
					{ type: 'direction', who: 's8', dir: 'E', steps: 1, than: 's3' }
				]
			},
			{
				id: 's9',
				name: 'Marta',
				initial: 'M',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'W', steps: 8, than: 's2' },
					{ type: 'direction', who: 's9', dir: 'S', steps: 1, than: 's3' }
				]
			}
		],
		victim: { name: 'Pilar', row: 6, col: 7 },
		solution: {
			s1: { row: 4, col: 4 },
			s2: { row: 2, col: 9 },
			s3: { row: 0, col: 2 },
			s4: { row: 3, col: 6 },
			s5: { row: 7, col: 8 },
			s6: { row: 8, col: 0 },
			s7: { row: 9, col: 5 },
			s8: { row: 5, col: 3 },
			s9: { row: 1, col: 1 }
		},
		killer: 's5',
		meta: { seed: 21212293, clueCount: 13, negatives: 1, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-055',
		game: 'murdoku',
		number: 55,
		title: 'Marea baja',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'very_hard',
		size: 12,
		estimatedMinutes: 20,
		grid: {
			size: 12,
			regions: [
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 3, 2, 3, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 3, 3, 3, 1, 2, 2],
				[0, 0, 0, 0, 0, 0, 3, 3, 3, 1, 1, 1],
				[0, 0, 0, 0, 3, 3, 3, 3, 1, 1, 1, 1],
				[0, 0, 0, 0, 3, 3, 3, 3, 1, 1, 1, 1],
				[0, 0, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'busto', icon: 'statue', row: 10, col: 5 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 4, col: 10 },
				{ id: 'p3', name: 'baúl', icon: 'chest', row: 3, col: 2 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 2, col: 11 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 0, col: 1 },
				{ id: 'p6', name: 'lámpara', icon: 'lamp', row: 7, col: 0 },
				{ id: 'p7', name: 'estatua', icon: 'statue', row: 6, col: 11 },
				{ id: 'p8', name: 'planta', icon: 'plant', row: 6, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'N', steps: 6, than: 's4' }]
			},
			{
				id: 's2',
				name: 'Bruno',
				initial: 'B',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'E', steps: 6, than: 's3' },
					{ type: 'direction', who: 's2', dir: 'N', steps: 1, than: 's8' }
				]
			},
			{
				id: 's3',
				name: 'Hugo',
				initial: 'H',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'N', steps: 5, than: 's4' }]
			},
			{
				id: 's4',
				name: 'Diego',
				initial: 'D',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 4, than: 's6' }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [{ type: 'notRegion', who: 's5', region: 2 }]
			},
			{
				id: 's6',
				name: 'Fabián',
				initial: 'F',
				color: 'purple',
				clues: [{ type: 'notRegion', who: 's6', region: 2 }]
			},
			{
				id: 's7',
				name: 'Karina',
				initial: 'K',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'W', steps: 7, than: 's2' },
					{ type: 'direction', who: 's7', dir: 'N', steps: 1, than: 's4' }
				]
			},
			{
				id: 's8',
				name: 'Irene',
				initial: 'I',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'W', steps: 8, than: 's4' },
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's7' }
				]
			},
			{
				id: 's9',
				name: 'Carla',
				initial: 'C',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'W', steps: 2, than: 's3' },
					{ type: 'direction', who: 's9', dir: 'N', steps: 1, than: 's5' }
				]
			},
			{
				id: 's10',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's10', dir: 'W', steps: 3, than: 's2' }]
			},
			{
				id: 's11',
				name: 'Lorenzo',
				initial: 'L',
				color: 'orange',
				clues: [{ type: 'direction', who: 's11', dir: 'E', steps: 5, than: 's5' }]
			}
		],
		victim: { name: 'Óscar', row: 7, col: 8 },
		solution: {
			s1: { row: 0, col: 6 },
			s2: { row: 3, col: 10 },
			s3: { row: 1, col: 4 },
			s4: { row: 6, col: 9 },
			s5: { row: 9, col: 0 },
			s6: { row: 10, col: 11 },
			s7: { row: 5, col: 3 },
			s8: { row: 4, col: 1 },
			s9: { row: 8, col: 2 },
			s10: { row: 11, col: 7 },
			s11: { row: 2, col: 5 }
		},
		killer: 's10',
		meta: { seed: 20906025, clueCount: 15, negatives: 2, complexity: 12, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-056',
		game: 'murdoku',
		number: 56,
		title: 'La tramoya a oscuras',
		setting: 'Un teatro después de la función',
		difficulty: 'very_hard',
		size: 12,
		estimatedMinutes: 20,
		grid: {
			size: 12,
			regions: [
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0],
				[0, 0, 0, 0, 3, 0, 3, 3, 3, 3, 3, 0],
				[0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
				[0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
				[3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2],
				[3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'estantería', icon: 'shelf', row: 7, col: 7 },
				{ id: 'p2', name: 'candelabro', icon: 'lamp', row: 10, col: 10 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 2, col: 3 },
				{ id: 'p4', name: 'retrato', icon: 'painting', row: 3, col: 3 },
				{ id: 'p5', name: 'cuadro', icon: 'painting', row: 1, col: 11 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 4, col: 7 },
				{ id: 'p7', name: 'estatua', icon: 'statue', row: 1, col: 5 },
				{ id: 'p8', name: 'lámpara', icon: 'lamp', row: 4, col: 2 },
				{ id: 'p9', name: 'piano', icon: 'piano', row: 7, col: 10 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 3, than: 's5' },
					{ type: 'region', who: 's1', region: 2 }
				]
			},
			{
				id: 's2',
				name: 'Julián',
				initial: 'J',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 0 }]
			},
			{
				id: 's3',
				name: 'Alicia',
				initial: 'A',
				color: 'yellow',
				clues: [
					{ type: 'notRegion', who: 's3', region: 2 },
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's4' }
				]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 3, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Diego',
				initial: 'D',
				color: 'pink',
				clues: [
					{ type: 'notRegion', who: 's5', region: 3 },
					{ type: 'rowEdge', who: 's5', edge: 'bottom' }
				]
			},
			{
				id: 's6',
				name: 'Hugo',
				initial: 'H',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'W', steps: 7, than: 's2' },
					{ type: 'direction', who: 's6', dir: 'S', steps: 1, than: 's9' }
				]
			},
			{
				id: 's7',
				name: 'Marta',
				initial: 'M',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'E', steps: 5, than: 's3' }]
			},
			{
				id: 's8',
				name: 'Lorenzo',
				initial: 'L',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'E', steps: 3, than: 's3' },
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's11' }
				]
			},
			{
				id: 's9',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's9', dir: 'W', steps: 2, than: 's6' }]
			},
			{
				id: 's10',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's10', dir: 'S', steps: 9, than: 's6' },
					{ type: 'direction', who: 's10', dir: 'E', steps: 1, than: 's6' }
				]
			},
			{
				id: 's11',
				name: 'Carla',
				initial: 'C',
				color: 'orange',
				clues: [{ type: 'direction', who: 's11', dir: 'W', steps: 4, than: 's2' }]
			}
		],
		victim: { name: 'Vera', row: 8, col: 8 },
		solution: {
			s1: { row: 9, col: 7 },
			s2: { row: 7, col: 9 },
			s3: { row: 5, col: 1 },
			s4: { row: 4, col: 11 },
			s5: { row: 11, col: 10 },
			s6: { row: 1, col: 2 },
			s7: { row: 6, col: 6 },
			s8: { row: 2, col: 4 },
			s9: { row: 0, col: 0 },
			s10: { row: 10, col: 3 },
			s11: { row: 3, col: 5 }
		},
		killer: 's2',
		meta: { seed: 20704486, clueCount: 17, negatives: 3, complexity: 12, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-057',
		game: 'murdoku',
		number: 57,
		title: 'El retrato del estudio',
		setting: 'Una mansión a medianoche',
		difficulty: 'very_hard',
		size: 12,
		estimatedMinutes: 20,
		grid: {
			size: 12,
			regions: [
				[2, 2, 2, 2, 2, 5, 5, 5, 5, 5, 4, 4],
				[2, 2, 2, 2, 2, 2, 5, 5, 5, 5, 5, 4],
				[2, 2, 2, 2, 2, 2, 5, 5, 4, 4, 4, 4],
				[2, 2, 2, 2, 3, 3, 5, 3, 0, 4, 4, 4],
				[2, 2, 2, 3, 3, 3, 3, 3, 0, 0, 0, 4],
				[2, 2, 2, 3, 3, 3, 3, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 3, 3, 1, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 },
				{ id: 4, name: 'Jardín', tone: 4 },
				{ id: 5, name: 'Terraza', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'lámpara', icon: 'lamp', row: 9, col: 11 },
				{ id: 'p2', name: 'retrato', icon: 'painting', row: 3, col: 10 },
				{ id: 'p3', name: 'cuadro', icon: 'painting', row: 7, col: 10 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 6, col: 6 },
				{ id: 'p5', name: 'baúl', icon: 'chest', row: 7, col: 6 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 2, col: 3 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Bruno',
				initial: 'B',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 4, than: 's5' },
					{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's11' }
				]
			},
			{
				id: 's2',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 3, than: 's5' }]
			},
			{
				id: 's3',
				name: 'Irene',
				initial: 'I',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'N', steps: 4, than: 's5' },
					{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's5' }
				]
			},
			{
				id: 's4',
				name: 'Gabriela',
				initial: 'G',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 4 },
					{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's7' }
				]
			},
			{
				id: 's5',
				name: 'Karina',
				initial: 'K',
				color: 'pink',
				clues: [{ type: 'notRegion', who: 's5', region: 2 }]
			},
			{
				id: 's6',
				name: 'Marta',
				initial: 'M',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'E', steps: 5, than: 's4' }]
			},
			{
				id: 's7',
				name: 'Julián',
				initial: 'J',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'E', steps: 6, than: 's5' }]
			},
			{
				id: 's8',
				name: 'Hugo',
				initial: 'H',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'N', steps: 10, than: 's2' }]
			},
			{
				id: 's9',
				name: 'Carla',
				initial: 'C',
				color: 'blue',
				clues: [{ type: 'direction', who: 's9', dir: 'W', steps: 2, than: 's5' }]
			},
			{
				id: 's10',
				name: 'Diego',
				initial: 'D',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's10', dir: 'E', steps: 5, than: 's3' }]
			},
			{
				id: 's11',
				name: 'Alicia',
				initial: 'A',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's11', dir: 'N', steps: 3, than: 's1' },
					{ type: 'direction', who: 's11', dir: 'S', steps: 1, than: 's6' }
				]
			}
		],
		victim: { name: 'Sofía', row: 7, col: 8 },
		solution: {
			s1: { row: 6, col: 1 },
			s2: { row: 11, col: 6 },
			s3: { row: 4, col: 4 },
			s4: { row: 9, col: 2 },
			s5: { row: 8, col: 5 },
			s6: { row: 2, col: 7 },
			s7: { row: 10, col: 11 },
			s8: { row: 1, col: 10 },
			s9: { row: 5, col: 3 },
			s10: { row: 0, col: 9 },
			s11: { row: 3, col: 0 }
		},
		killer: 's7',
		meta: { seed: 21445508, clueCount: 15, negatives: 2, complexity: 12, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-058',
		game: 'murdoku',
		number: 58,
		title: 'El libro devuelto',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'very_hard',
		size: 12,
		estimatedMinutes: 20,
		grid: {
			size: 12,
			regions: [
				[2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
				[2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
				[2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
				[2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
				[2, 2, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 3, 3, 3, 1, 3, 3],
				[0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3],
				[0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3],
				[0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3],
				[0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3],
				[0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Galería', tone: 1 },
				{ id: 2, name: 'Sala de lectura', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'cofre', icon: 'chest', row: 1, col: 3 },
				{ id: 'p2', name: 'busto', icon: 'statue', row: 9, col: 4 },
				{ id: 'p3', name: 'atril', icon: 'shelf', row: 10, col: 5 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 0, col: 8 },
				{ id: 'p5', name: 'candelabro', icon: 'lamp', row: 8, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Alicia',
				initial: 'A',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'W', steps: 3, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Elena',
				initial: 'E',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'N', steps: 6, than: 's3' },
					{ type: 'direction', who: 's2', dir: 'N', steps: 1, than: 's1' }
				]
			},
			{
				id: 's3',
				name: 'Karina',
				initial: 'K',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 1 }]
			},
			{
				id: 's4',
				name: 'Bruno',
				initial: 'B',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'S', steps: 2, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 4, than: 's6' }]
			},
			{
				id: 's6',
				name: 'Diego',
				initial: 'D',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 5, than: 's3' }]
			},
			{
				id: 's7',
				name: 'Carla',
				initial: 'C',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'W', steps: 8, than: 's2' }]
			},
			{
				id: 's8',
				name: 'Irene',
				initial: 'I',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'W', steps: 2, than: 's4' },
					{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's3' }
				]
			},
			{
				id: 's9',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'W', steps: 8, than: 's5' },
					{ type: 'rowEdge', who: 's9', edge: 'bottom' }
				]
			},
			{
				id: 's10',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's10', dir: 'E', steps: 6, than: 's6' },
					{ type: 'direction', who: 's10', dir: 'S', steps: 1, than: 's6' }
				]
			},
			{
				id: 's11',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's11', dir: 'W', steps: 5, than: 's5' },
					{ type: 'region', who: 's11', region: 0 }
				]
			}
		],
		victim: { name: 'Óscar', row: 8, col: 7 },
		solution: {
			s1: { row: 4, col: 6 },
			s2: { row: 3, col: 9 },
			s3: { row: 9, col: 10 },
			s4: { row: 6, col: 4 },
			s5: { row: 5, col: 8 },
			s6: { row: 1, col: 5 },
			s7: { row: 0, col: 1 },
			s8: { row: 10, col: 2 },
			s9: { row: 11, col: 0 },
			s10: { row: 2, col: 11 },
			s11: { row: 7, col: 3 }
		},
		killer: 's3',
		meta: { seed: 21034511, clueCount: 16, negatives: 1, complexity: 12, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-059',
		game: 'murdoku',
		number: 59,
		title: 'Un tallo quebrado',
		setting: 'Un invernadero al amanecer',
		difficulty: 'hardcore',
		size: 14,
		estimatedMinutes: 28,
		grid: {
			size: 14,
			regions: [
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
				[0, 0, 2, 0, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 3, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
				[3, 3, 3, 3, 3, 0, 0, 1, 1, 1, 0, 1, 1, 1],
				[3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'reloj', icon: 'clock', row: 13, col: 6 },
				{ id: 'p2', name: 'arcón', icon: 'chest', row: 0, col: 1 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 12, col: 4 },
				{ id: 'p4', name: 'piano', icon: 'piano', row: 13, col: 4 },
				{ id: 'p5', name: 'lámpara', icon: 'lamp', row: 8, col: 1 },
				{ id: 'p6', name: 'cuadro', icon: 'painting', row: 8, col: 7 },
				{ id: 'p7', name: 'maceta', icon: 'plant', row: 2, col: 11 },
				{ id: 'p8', name: 'estatua', icon: 'statue', row: 2, col: 1 },
				{ id: 'p9', name: 'helecho', icon: 'plant', row: 7, col: 11 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 0 }]
			},
			{
				id: 's2',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'N', steps: 10, than: 's5' },
					{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's12' }
				]
			},
			{
				id: 's3',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'N', steps: 3, than: 's7' },
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's2' }
				]
			},
			{
				id: 's4',
				name: 'Irene',
				initial: 'I',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'N', steps: 11, than: 's5' },
					{ type: 'direction', who: 's4', dir: 'W', steps: 6, than: 's11' }
				]
			},
			{
				id: 's5',
				name: 'Nicolás',
				initial: 'N',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 12, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Bruno',
				initial: 'B',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 8, than: 's2' }]
			},
			{
				id: 's7',
				name: 'Marta',
				initial: 'M',
				color: 'red',
				clues: [
					{ type: 'notRegion', who: 's7', region: 3 },
					{ type: 'direction', who: 's7', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's8',
				name: 'Lorenzo',
				initial: 'L',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'N', steps: 3, than: 's5' }]
			},
			{
				id: 's9',
				name: 'Fabián',
				initial: 'F',
				color: 'blue',
				clues: [
					{ type: 'notRegion', who: 's9', region: 3 },
					{ type: 'direction', who: 's9', dir: 'S', steps: 1, than: 's11' }
				]
			},
			{
				id: 's10',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's10', dir: 'W', steps: 4, than: 's4' },
					{ type: 'direction', who: 's10', dir: 'N', steps: 1, than: 's5' }
				]
			},
			{
				id: 's11',
				name: 'Julián',
				initial: 'J',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's11', dir: 'N', steps: 3, than: 's6' },
					{ type: 'direction', who: 's11', dir: 'E', steps: 1, than: 's3' }
				]
			},
			{
				id: 's12',
				name: 'Diego',
				initial: 'D',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's12', dir: 'N', steps: 2, than: 's4' },
					{ type: 'direction', who: 's12', dir: 'E', steps: 1, than: 's8' }
				]
			},
			{
				id: 's13',
				name: 'Olivia',
				initial: 'O',
				color: 'purple',
				clues: [
					{ type: 'notRegion', who: 's13', region: 2 },
					{ type: 'direction', who: 's13', dir: 'W', steps: 1, than: 's6' }
				]
			}
		],
		victim: { name: 'Tomás', row: 11, col: 6 },
		solution: {
			s1: { row: 1, col: 4 },
			s2: { row: 3, col: 10 },
			s3: { row: 4, col: 12 },
			s4: { row: 2, col: 7 },
			s5: { row: 13, col: 0 },
			s6: { row: 8, col: 2 },
			s7: { row: 7, col: 5 },
			s8: { row: 10, col: 8 },
			s9: { row: 6, col: 11 },
			s10: { row: 12, col: 3 },
			s11: { row: 5, col: 13 },
			s12: { row: 0, col: 9 },
			s13: { row: 9, col: 1 }
		},
		killer: 's8',
		meta: { seed: 21147159, clueCount: 22, negatives: 4, complexity: 15, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-060',
		game: 'murdoku',
		number: 60,
		title: 'Café a medianoche',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'hardcore',
		size: 14,
		estimatedMinutes: 28,
		grid: {
			size: 14,
			regions: [
				[3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0],
				[3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0],
				[3, 3, 3, 3, 3, 3, 3, 3, 1, 0, 0, 0, 0, 0],
				[3, 3, 3, 3, 3, 3, 1, 1, 1, 0, 0, 0, 0, 0],
				[3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1],
				[3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1],
				[3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1],
				[2, 2, 2, 2, 2, 2, 2, 2, 5, 5, 2, 2, 2, 2],
				[4, 4, 4, 4, 2, 5, 5, 5, 5, 5, 2, 2, 2, 2],
				[4, 4, 4, 4, 4, 5, 5, 5, 5, 2, 2, 2, 2, 2],
				[4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 2, 2, 2, 2],
				[4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 2, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 },
				{ id: 4, name: 'Patio', tone: 4 },
				{ id: 5, name: 'Bodega', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'lámpara', icon: 'lamp', row: 13, col: 1 },
				{ id: 'p2', name: 'planta aromática', icon: 'plant', row: 10, col: 6 },
				{ id: 'p3', name: 'piano', icon: 'piano', row: 9, col: 8 },
				{ id: 'p4', name: 'candelabro', icon: 'lamp', row: 6, col: 8 },
				{ id: 'p5', name: 'figura', icon: 'statue', row: 1, col: 3 },
				{ id: 'p6', name: 'aparador', icon: 'shelf', row: 1, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Marta',
				initial: 'M',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 6, than: 's8' }]
			},
			{
				id: 's2',
				name: 'Fabián',
				initial: 'F',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 2 }]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [
					{ type: 'notRegion', who: 's3', region: 2 },
					{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's1' }
				]
			},
			{
				id: 's4',
				name: 'Elena',
				initial: 'E',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'S', steps: 2, than: 's3' }]
			},
			{
				id: 's5',
				name: 'Lorenzo',
				initial: 'L',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'S', steps: 8, than: 's2' },
					{ type: 'direction', who: 's5', dir: 'W', steps: 1, than: 's6' }
				]
			},
			{
				id: 's6',
				name: 'Irene',
				initial: 'I',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'S', steps: 10, than: 's2' }]
			},
			{
				id: 's7',
				name: 'Bruno',
				initial: 'B',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'W', steps: 2, than: 's2' },
					{ type: 'direction', who: 's7', dir: 'N', steps: 1, than: 's9' }
				]
			},
			{
				id: 's8',
				name: 'Diego',
				initial: 'D',
				color: 'green',
				clues: [
					{ type: 'notRegion', who: 's8', region: 2 },
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's13' }
				]
			},
			{
				id: 's9',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'direction', who: 's9', dir: 'S', steps: 7, than: 's4' }]
			},
			{
				id: 's10',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's10', dir: 'E', steps: 4, than: 's4' }]
			},
			{
				id: 's11',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [{ type: 'direction', who: 's11', dir: 'E', steps: 6, than: 's3' }]
			},
			{
				id: 's12',
				name: 'Karina',
				initial: 'K',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's12', dir: 'W', steps: 5, than: 's5' },
					{ type: 'region', who: 's12', region: 4 }
				]
			},
			{
				id: 's13',
				name: 'Julián',
				initial: 'J',
				color: 'purple',
				clues: [{ type: 'direction', who: 's13', dir: 'W', steps: 4, than: 's2' }]
			}
		],
		victim: { name: 'Óscar', row: 5, col: 8 },
		solution: {
			s1: { row: 1, col: 7 },
			s2: { row: 3, col: 4 },
			s3: { row: 0, col: 6 },
			s4: { row: 2, col: 9 },
			s5: { row: 11, col: 10 },
			s6: { row: 13, col: 11 },
			s7: { row: 8, col: 2 },
			s8: { row: 6, col: 1 },
			s9: { row: 9, col: 3 },
			s10: { row: 10, col: 13 },
			s11: { row: 4, col: 12 },
			s12: { row: 12, col: 5 },
			s13: { row: 7, col: 0 }
		},
		killer: 's11',
		meta: { seed: 20736162, clueCount: 18, negatives: 3, complexity: 14, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-061',
		game: 'murdoku',
		number: 61,
		title: 'La sala griega al alba',
		setting: 'Un museo después del cierre',
		difficulty: 'hardcore',
		size: 15,
		estimatedMinutes: 32,
		grid: {
			size: 15,
			regions: [
				[0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 1, 2],
				[0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
				[0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2],
				[0, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 2],
				[0, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Sala egipcia', tone: 1 },
				{ id: 2, name: 'Sala griega', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'estantería', icon: 'shelf', row: 12, col: 7 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 6, col: 14 },
				{ id: 'p3', name: 'busto', icon: 'statue', row: 13, col: 2 },
				{ id: 'p4', name: 'cofre', icon: 'chest', row: 2, col: 7 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 1, col: 3 },
				{ id: 'p6', name: 'estatua', icon: 'statue', row: 4, col: 14 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Irene',
				initial: 'I',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 0 }, { type: 'region', who: 's1', region: 3 }]
			},
			{
				id: 's2',
				name: 'Elena',
				initial: 'E',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'N', steps: 4, than: 's4' },
					{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's8' }
				]
			},
			{
				id: 's3',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'S', steps: 2, than: 's8' }]
			},
			{
				id: 's4',
				name: 'Karina',
				initial: 'K',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 2 }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'W', steps: 2, than: 's6' },
					{ type: 'direction', who: 's5', dir: 'N', steps: 1, than: 's14' }
				]
			},
			{
				id: 's6',
				name: 'Bruno',
				initial: 'B',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'W', steps: 5, than: 's1' },
					{ type: 'direction', who: 's6', dir: 'S', steps: 1, than: 's2' }
				]
			},
			{
				id: 's7',
				name: 'Carla',
				initial: 'C',
				color: 'red',
				clues: [
					{ type: 'notRegion', who: 's7', region: 3 },
					{ type: 'direction', who: 's7', dir: 'W', steps: 1, than: 's10' }
				]
			},
			{
				id: 's8',
				name: 'Fabián',
				initial: 'F',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'E', steps: 6, than: 's4' }]
			},
			{
				id: 's9',
				name: 'Julián',
				initial: 'J',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's9', dir: 'S', steps: 4, than: 's5' },
					{ type: 'direction', who: 's9', dir: 'W', steps: 1, than: 's13' }
				]
			},
			{
				id: 's10',
				name: 'Marta',
				initial: 'M',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's10', dir: 'N', steps: 5, than: 's4' },
					{ type: 'direction', who: 's10', dir: 'W', steps: 1, than: 's1' }
				]
			},
			{
				id: 's11',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's11', dir: 'E', steps: 5, than: 's4' },
					{ type: 'rowEdge', who: 's11', edge: 'top' }
				]
			},
			{
				id: 's12',
				name: 'Gabriela',
				initial: 'G',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's12', dir: 'N', steps: 5, than: 's1' },
					{ type: 'direction', who: 's12', dir: 'E', steps: 1, than: 's5' }
				]
			},
			{
				id: 's13',
				name: 'Diego',
				initial: 'D',
				color: 'purple',
				clues: [{ type: 'direction', who: 's13', dir: 'N', steps: 6, than: 's4' }]
			},
			{
				id: 's14',
				name: 'Alicia',
				initial: 'A',
				color: 'red',
				clues: [{ type: 'direction', who: 's14', dir: 'E', steps: 2, than: 's2' }]
			}
		],
		victim: { name: 'Simón', row: 1, col: 11 },
		solution: {
			s1: { row: 14, col: 7 },
			s2: { row: 4, col: 10 },
			s3: { row: 13, col: 4 },
			s4: { row: 8, col: 3 },
			s5: { row: 6, col: 0 },
			s6: { row: 5, col: 2 },
			s7: { row: 12, col: 5 },
			s8: { row: 11, col: 9 },
			s9: { row: 10, col: 13 },
			s10: { row: 3, col: 6 },
			s11: { row: 0, col: 8 },
			s12: { row: 9, col: 1 },
			s13: { row: 2, col: 14 },
			s14: { row: 7, col: 12 }
		},
		killer: 's13',
		meta: { seed: 20744081, clueCount: 23, negatives: 3, complexity: 15, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-062',
		game: 'murdoku',
		number: 62,
		title: 'El coche de correo',
		setting: 'Un tren nocturno detenido',
		difficulty: 'hardcore',
		size: 15,
		estimatedMinutes: 32,
		grid: {
			size: 15,
			regions: [
				[2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 3, 0, 0, 0],
				[2, 2, 2, 2, 2, 1, 1, 1, 1, 3, 0, 3, 0, 0, 0],
				[1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3],
				[1, 1, 1, 1, 1, 1, 4, 4, 3, 3, 3, 3, 3, 3, 3],
				[1, 1, 1, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3],
				[4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 13, col: 3 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 1, col: 3 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 1, col: 14 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 4, col: 4 },
				{ id: 'p5', name: 'candelabro', icon: 'lamp', row: 8, col: 5 },
				{ id: 'p6', name: 'piano', icon: 'piano', row: 6, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Lorenzo',
				initial: 'L',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'S', steps: 9, than: 's4' },
					{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's14' }
				]
			},
			{
				id: 's2',
				name: 'Julián',
				initial: 'J',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 12, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'N', steps: 4, than: 's1' },
					{ type: 'direction', who: 's3', dir: 'W', steps: 14, than: 's9' }
				]
			},
			{
				id: 's4',
				name: 'Irene',
				initial: 'I',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 2 }]
			},
			{
				id: 's5',
				name: 'Karina',
				initial: 'K',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'W', steps: 3, than: 's7' }]
			},
			{
				id: 's6',
				name: 'Marta',
				initial: 'M',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'W', steps: 4, than: 's7' },
					{ type: 'direction', who: 's6', dir: 'W', steps: 7, than: 's13' }
				]
			},
			{
				id: 's7',
				name: 'Alicia',
				initial: 'A',
				color: 'red',
				clues: [
					{ type: 'notRegion', who: 's7', region: 0 },
					{ type: 'direction', who: 's7', dir: 'E', steps: 1, than: 's12' }
				]
			},
			{
				id: 's8',
				name: 'Hugo',
				initial: 'H',
				color: 'green',
				clues: [
					{ type: 'notRegion', who: 's8', region: 3 },
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's13' }
				]
			},
			{
				id: 's9',
				name: 'Diego',
				initial: 'D',
				color: 'blue',
				clues: [
					{ type: 'notRegion', who: 's9', region: 2 },
					{ type: 'direction', who: 's9', dir: 'N', steps: 1, than: 's7' }
				]
			},
			{
				id: 's10',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's10', dir: 'E', steps: 8, than: 's7' },
					{ type: 'direction', who: 's10', dir: 'S', steps: 1, than: 's11' }
				]
			},
			{
				id: 's11',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'direction', who: 's11', dir: 'E', steps: 6, than: 's6' }]
			},
			{
				id: 's12',
				name: 'Bruno',
				initial: 'B',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's12', dir: 'N', steps: 7, than: 's6' },
					{ type: 'direction', who: 's12', dir: 'N', steps: 11, than: 's9' }
				]
			},
			{
				id: 's13',
				name: 'Gabriela',
				initial: 'G',
				color: 'purple',
				clues: [{ type: 'direction', who: 's13', dir: 'S', steps: 3, than: 's4' }]
			},
			{
				id: 's14',
				name: 'Olivia',
				initial: 'O',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's14', dir: 'W', steps: 2, than: 's2' },
					{ type: 'direction', who: 's14', dir: 'W', steps: 1, than: 's4' }
				]
			}
		],
		victim: { name: 'Sofía', row: 11, col: 3 },
		solution: {
			s1: { row: 9, col: 9 },
			s2: { row: 14, col: 12 },
			s3: { row: 5, col: 0 },
			s4: { row: 0, col: 11 },
			s5: { row: 4, col: 2 },
			s6: { row: 8, col: 1 },
			s7: { row: 13, col: 5 },
			s8: { row: 2, col: 6 },
			s9: { row: 12, col: 14 },
			s10: { row: 7, col: 13 },
			s11: { row: 6, col: 7 },
			s12: { row: 1, col: 4 },
			s13: { row: 3, col: 8 },
			s14: { row: 10, col: 10 }
		},
		killer: 's7',
		meta: { seed: 21694561, clueCount: 23, negatives: 4, complexity: 18, generatedBy: 'generator' }
	}
];
