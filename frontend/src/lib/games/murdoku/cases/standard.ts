import type { MurdokuCase } from '../types.ts';

/** Generado por `npm run games:generate -- --max-size 9` (semilla base 20261022). No editar a mano. */
export const standardCases: MurdokuCase[] = [
	{
		id: 'murdoku-001',
		game: 'murdoku',
		number: 1,
		title: 'El estudio',
		setting: 'Una mansión a medianoche',
		difficulty: 'very_easy',
		size: 5,
		estimatedMinutes: 3,
		grid: {
			size: 5,
			regions: [[2, 2, 2, 2, 3], [4, 2, 2, 2, 0], [4, 4, 4, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 },
				{ id: 4, name: 'Jardín', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 1, col: 2 },
				{ id: 'p2', name: 'candelabro', icon: 'lamp', row: 0, col: 3 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 2, col: 0 },
				{ id: 'p4', name: 'retrato', icon: 'painting', row: 4, col: 3 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 4, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Fabián',
				initial: 'F',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [{ type: 'region', who: 's2', region: 1 }]
			},
			{
				id: 's3',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 1 }, { type: 'nearProp', who: 's3', prop: 'p4' }]
			},
			{
				id: 's4',
				name: 'Julián',
				initial: 'J',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 3 }]
			}
		],
		victim: { name: 'Pilar', row: 1, col: 0 },
		solution: {
			s1: { row: 2, col: 1 },
			s2: { row: 4, col: 2 },
			s3: { row: 3, col: 3 },
			s4: { row: 0, col: 4 }
		},
		killer: 's1',
		meta: { seed: 20268941, clueCount: 5, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-002',
		game: 'murdoku',
		number: 2,
		title: 'La biblioteca',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'very_easy',
		size: 5,
		estimatedMinutes: 3,
		grid: {
			size: 5,
			regions: [[2, 3, 3, 3, 3], [2, 3, 3, 3, 3], [0, 3, 3, 3, 3], [0, 1, 1, 1, 1], [0, 1, 1, 1, 1]],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Galería', tone: 1 },
				{ id: 2, name: 'Sala de lectura', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'candelabro', icon: 'lamp', row: 0, col: 4 },
				{ id: 'p2', name: 'cuadro', icon: 'painting', row: 3, col: 2 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 4, col: 0 },
				{ id: 'p4', name: 'lámpara', icon: 'lamp', row: 1, col: 0 },
				{ id: 'p5', name: 'atril', icon: 'shelf', row: 2, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Irene',
				initial: 'I',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Alicia',
				initial: 'A',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's3' },
					{ type: 'colEdge', who: 's2', edge: 'right' }
				]
			},
			{
				id: 's3',
				name: 'Olivia',
				initial: 'O',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Gabriela',
				initial: 'G',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 1 }]
			}
		],
		victim: { name: 'Teresa', row: 0, col: 3 },
		solution: {
			s1: { row: 1, col: 1 },
			s2: { row: 3, col: 4 },
			s3: { row: 2, col: 0 },
			s4: { row: 4, col: 2 }
		},
		killer: 's1',
		meta: { seed: 20381589, clueCount: 5, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-003',
		game: 'murdoku',
		number: 3,
		title: 'El invernadero',
		setting: 'Un invernadero al amanecer',
		difficulty: 'very_easy',
		size: 5,
		estimatedMinutes: 3,
		grid: {
			size: 5,
			regions: [[3, 4, 4, 4, 0], [2, 4, 4, 4, 0], [4, 4, 4, 4, 0], [4, 4, 1, 1, 0], [1, 1, 1, 1, 1]],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 0, col: 1 },
				{ id: 'p2', name: 'maceta', icon: 'plant', row: 1, col: 2 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 0, col: 3 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 2, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Marta',
				initial: 'M',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Julián',
				initial: 'J',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Vera', row: 2, col: 0 },
		solution: {
			s1: { row: 4, col: 3 },
			s2: { row: 1, col: 1 },
			s3: { row: 0, col: 4 },
			s4: { row: 3, col: 2 }
		},
		killer: 's2',
		meta: { seed: 20494237, clueCount: 4, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-004',
		game: 'murdoku',
		number: 4,
		title: 'La cocina de servicio',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'very_easy',
		size: 5,
		estimatedMinutes: 3,
		grid: {
			size: 5,
			regions: [[0, 2, 2, 2, 2], [0, 2, 2, 2, 2], [0, 0, 3, 1, 1], [0, 3, 3, 1, 1], [0, 3, 1, 1, 1]],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'reloj', icon: 'clock', row: 2, col: 2 },
				{ id: 'p2', name: 'aparador', icon: 'shelf', row: 0, col: 3 },
				{ id: 'p3', name: 'baúl', icon: 'chest', row: 0, col: 0 },
				{ id: 'p4', name: 'bodegón', icon: 'painting', row: 4, col: 4 },
				{ id: 'p5', name: 'planta aromática', icon: 'plant', row: 1, col: 1 },
				{ id: 'p6', name: 'candelabro', icon: 'lamp', row: 4, col: 1 },
				{ id: 'p7', name: 'figura', icon: 'statue', row: 1, col: 2 },
				{ id: 'p8', name: 'estantería', icon: 'shelf', row: 0, col: 2 },
				{ id: 'p9', name: 'piano', icon: 'piano', row: 1, col: 0 },
				{ id: 'p10', name: 'lámpara', icon: 'lamp', row: 4, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Gabriela',
				initial: 'G',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Carla',
				initial: 'C',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 1 }]
			},
			{
				id: 's4',
				name: 'Hugo',
				initial: 'H',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'S', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Ramiro', row: 0, col: 1 },
		solution: {
			s1: { row: 1, col: 3 },
			s2: { row: 3, col: 4 },
			s3: { row: 4, col: 2 },
			s4: { row: 2, col: 0 }
		},
		killer: 's1',
		meta: { seed: 20292698, clueCount: 4, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-005',
		game: 'murdoku',
		number: 5,
		title: 'El museo',
		setting: 'Un museo después del cierre',
		difficulty: 'very_easy',
		size: 5,
		estimatedMinutes: 3,
		grid: {
			size: 5,
			regions: [[1, 5, 5, 5, 5], [4, 4, 5, 5, 5], [2, 4, 0, 5, 5], [2, 0, 0, 0, 3], [2, 0, 0, 3, 3]],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Sala egipcia', tone: 1 },
				{ id: 2, name: 'Sala griega', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 },
				{ id: 5, name: 'Patio', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 0, col: 3 },
				{ id: 'p2', name: 'busto', icon: 'statue', row: 1, col: 2 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 3, col: 4 },
				{ id: 'p4', name: 'estantería', icon: 'shelf', row: 2, col: 3 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 1, col: 1 },
				{ id: 'p6', name: 'cofre', icon: 'chest', row: 1, col: 3 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Gabriela',
				initial: 'G',
				color: 'blue',
				clues: [{ type: 'region', who: 's2', region: 0 }]
			},
			{
				id: 's3',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's2' }]
			},
			{
				id: 's4',
				name: 'Diego',
				initial: 'D',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Óscar', row: 1, col: 4 },
		solution: {
			s1: { row: 2, col: 1 },
			s2: { row: 3, col: 3 },
			s3: { row: 0, col: 2 },
			s4: { row: 4, col: 0 }
		},
		killer: 's3',
		meta: { seed: 20510075, clueCount: 4, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-006',
		game: 'murdoku',
		number: 6,
		title: 'El tren nocturno',
		setting: 'Un tren nocturno detenido',
		difficulty: 'very_easy',
		size: 5,
		estimatedMinutes: 3,
		grid: {
			size: 5,
			regions: [[4, 3, 0, 0, 0], [4, 3, 2, 2, 0], [3, 3, 1, 2, 2], [1, 1, 1, 2, 2], [1, 1, 1, 1, 2]],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'baúl', icon: 'chest', row: 4, col: 3 },
				{ id: 'p2', name: 'cuadro', icon: 'painting', row: 0, col: 2 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 1, col: 4 },
				{ id: 'p4', name: 'piano', icon: 'piano', row: 4, col: 0 },
				{ id: 'p5', name: 'estatua', icon: 'statue', row: 3, col: 1 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 1, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's3' },
					{ type: 'region', who: 's1', region: 4 }
				]
			},
			{
				id: 's2',
				name: 'Lorenzo',
				initial: 'L',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Hugo',
				initial: 'H',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Elena',
				initial: 'E',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's2' }]
			}
		],
		victim: { name: 'Simón', row: 4, col: 4 },
		solution: {
			s1: { row: 0, col: 0 },
			s2: { row: 3, col: 3 },
			s3: { row: 1, col: 1 },
			s4: { row: 2, col: 2 }
		},
		killer: 's2',
		meta: { seed: 20727452, clueCount: 5, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-007',
		game: 'murdoku',
		number: 7,
		title: 'El faro',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 2],
				[3, 3, 3, 2, 2, 2],
				[3, 3, 3, 2, 2, 2],
				[3, 4, 4, 2, 0, 2],
				[3, 4, 4, 4, 0, 2]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 },
				{ id: 4, name: 'Terraza', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 5, col: 0 },
				{ id: 'p2', name: 'busto', icon: 'statue', row: 2, col: 1 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 3, col: 0 },
				{ id: 'p4', name: 'planta', icon: 'plant', row: 2, col: 3 },
				{ id: 'p5', name: 'baúl', icon: 'chest', row: 0, col: 2 },
				{ id: 'p6', name: 'lámpara', icon: 'lamp', row: 5, col: 1 },
				{ id: 'p7', name: 'cuadro', icon: 'painting', row: 0, col: 5 },
				{ id: 'p8', name: 'reloj', icon: 'clock', row: 1, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Marta',
				initial: 'M',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 4 }]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 1, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Alicia',
				initial: 'A',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 4 }]
			},
			{
				id: 's4',
				name: 'Gabriela',
				initial: 'G',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's3' }]
			},
			{
				id: 's5',
				name: 'Julián',
				initial: 'J',
				color: 'pink',
				clues: [
					{ type: 'region', who: 's5', region: 3 },
					{ type: 'direction', who: 's5', dir: 'W', steps: 1, than: 's1' }
				]
			}
		],
		victim: { name: 'Tomás', row: 0, col: 4 },
		solution: {
			s1: { row: 5, col: 3 },
			s2: { row: 3, col: 5 },
			s3: { row: 4, col: 1 },
			s4: { row: 1, col: 0 },
			s5: { row: 2, col: 2 }
		},
		killer: 's4',
		meta: { seed: 20421184, clueCount: 6, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-008',
		game: 'murdoku',
		number: 8,
		title: 'El teatro',
		setting: 'Un teatro después de la función',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[1, 1, 1, 1, 1, 1],
				[3, 3, 1, 1, 1, 1],
				[3, 3, 3, 1, 1, 5],
				[0, 3, 3, 2, 5, 5],
				[4, 4, 4, 2, 2, 5],
				[4, 4, 4, 4, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 },
				{ id: 4, name: 'Vestíbulo', tone: 4 },
				{ id: 5, name: 'Tramoya', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'piano', icon: 'piano', row: 2, col: 1 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 2, col: 5 },
				{ id: 'p3', name: 'retrato', icon: 'painting', row: 3, col: 3 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 0, col: 4 },
				{ id: 'p5', name: 'candelabro', icon: 'lamp', row: 0, col: 2 },
				{ id: 'p6', name: 'lámpara', icon: 'lamp', row: 2, col: 0 },
				{ id: 'p7', name: 'cuadro', icon: 'painting', row: 3, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Julián',
				initial: 'J',
				color: 'green',
				clues: [
					{ type: 'region', who: 's1', region: 1 },
					{ type: 'direction', who: 's1', dir: 'N', steps: 3, than: 's4' }
				]
			},
			{
				id: 's2',
				name: 'Bruno',
				initial: 'B',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Lorenzo',
				initial: 'L',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Gabriela',
				initial: 'G',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 1 }]
			}
		],
		victim: { name: 'Óscar', row: 4, col: 0 },
		solution: {
			s1: { row: 0, col: 3 },
			s2: { row: 5, col: 1 },
			s3: { row: 2, col: 4 },
			s4: { row: 3, col: 2 },
			s5: { row: 1, col: 5 }
		},
		killer: 's2',
		meta: { seed: 20429103, clueCount: 6, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-009',
		game: 'murdoku',
		number: 9,
		title: 'La chimenea del estudio',
		setting: 'Una mansión a medianoche',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1],
				[3, 3, 5, 5, 5, 1],
				[3, 3, 5, 5, 4, 2],
				[0, 0, 0, 4, 4, 2],
				[0, 0, 0, 0, 0, 2]
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
				{ id: 'p1', name: 'planta', icon: 'plant', row: 4, col: 1 },
				{ id: 'p2', name: 'estatua', icon: 'statue', row: 1, col: 1 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 3, col: 5 },
				{ id: 'p4', name: 'lámpara', icon: 'lamp', row: 0, col: 5 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 5, col: 3 },
				{ id: 'p6', name: 'estantería', icon: 'shelf', row: 2, col: 5 },
				{ id: 'p7', name: 'piano', icon: 'piano', row: 1, col: 4 },
				{ id: 'p8', name: 'cuadro', icon: 'painting', row: 4, col: 3 },
				{ id: 'p9', name: 'retrato', icon: 'painting', row: 5, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [
					{ type: 'region', who: 's1', region: 1 },
					{ type: 'direction', who: 's1', dir: 'E', steps: 4, than: 's2' }
				]
			},
			{
				id: 's2',
				name: 'Fabián',
				initial: 'F',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Olivia',
				initial: 'O',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 4 }]
			},
			{
				id: 's4',
				name: 'Marta',
				initial: 'M',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Irene',
				initial: 'I',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's3' }]
			}
		],
		victim: { name: 'Simón', row: 5, col: 2 },
		solution: {
			s1: { row: 1, col: 5 },
			s2: { row: 2, col: 1 },
			s3: { row: 3, col: 4 },
			s4: { row: 0, col: 3 },
			s5: { row: 4, col: 0 }
		},
		killer: 's5',
		meta: { seed: 20541751, clueCount: 6, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-010',
		game: 'murdoku',
		number: 10,
		title: 'El atlas abierto',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[1, 1, 1, 5, 5, 5],
				[1, 1, 1, 5, 5, 5],
				[3, 4, 0, 0, 0, 0],
				[3, 4, 0, 0, 0, 0],
				[3, 4, 4, 0, 0, 0],
				[3, 4, 2, 2, 0, 0]
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
				{ id: 'p1', name: 'busto', icon: 'statue', row: 5, col: 3 },
				{ id: 'p2', name: 'reloj', icon: 'clock', row: 0, col: 1 },
				{ id: 'p3', name: 'estantería', icon: 'shelf', row: 5, col: 5 },
				{ id: 'p4', name: 'atril', icon: 'shelf', row: 4, col: 4 },
				{ id: 'p5', name: 'estatua', icon: 'statue', row: 2, col: 5 },
				{ id: 'p6', name: 'cuadro', icon: 'painting', row: 1, col: 5 },
				{ id: 'p7', name: 'candelabro', icon: 'lamp', row: 1, col: 0 },
				{ id: 'p8', name: 'planta', icon: 'plant', row: 0, col: 4 },
				{ id: 'p9', name: 'cofre', icon: 'chest', row: 2, col: 3 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Julián',
				initial: 'J',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Diego',
				initial: 'D',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 0 }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'S', steps: 1, than: 's3' },
					{ type: 'direction', who: 's4', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's5',
				name: 'Irene',
				initial: 'I',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 3 }]
			}
		],
		victim: { name: 'Simón', row: 0, col: 3 },
		solution: {
			s1: { row: 1, col: 4 },
			s2: { row: 2, col: 1 },
			s3: { row: 3, col: 2 },
			s4: { row: 4, col: 5 },
			s5: { row: 5, col: 0 }
		},
		killer: 's1',
		meta: { seed: 20549670, clueCount: 6, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-011',
		game: 'murdoku',
		number: 11,
		title: 'La orquídea negra',
		setting: 'Un invernadero al amanecer',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[1, 1, 3, 3, 3, 0],
				[1, 1, 3, 0, 0, 0],
				[4, 4, 4, 0, 0, 0],
				[4, 4, 4, 2, 2, 5],
				[4, 4, 2, 2, 2, 5],
				[2, 2, 2, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 },
				{ id: 5, name: 'Cobertizo', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'arcón', icon: 'chest', row: 2, col: 2 },
				{ id: 'p2', name: 'reloj', icon: 'clock', row: 0, col: 0 },
				{ id: 'p3', name: 'helecho', icon: 'plant', row: 3, col: 3 },
				{ id: 'p4', name: 'lámpara', icon: 'lamp', row: 4, col: 5 },
				{ id: 'p5', name: 'maceta', icon: 'plant', row: 3, col: 0 },
				{ id: 'p6', name: 'piano', icon: 'piano', row: 2, col: 4 },
				{ id: 'p7', name: 'estantería', icon: 'shelf', row: 2, col: 3 },
				{ id: 'p8', name: 'cuadro', icon: 'painting', row: 5, col: 5 },
				{ id: 'p9', name: 'estatua', icon: 'statue', row: 2, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 3 }]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Karina',
				initial: 'K',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Bruno',
				initial: 'B',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 1 }]
			},
			{
				id: 's5',
				name: 'Fabián',
				initial: 'F',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'N', steps: 1, than: 's3' },
					{ type: 'nearProp', who: 's5', prop: 'p5' }
				]
			}
		],
		victim: { name: 'Lucía', row: 5, col: 4 },
		solution: {
			s1: { row: 0, col: 3 },
			s2: { row: 2, col: 5 },
			s3: { row: 4, col: 2 },
			s4: { row: 1, col: 0 },
			s5: { row: 3, col: 1 }
		},
		killer: 's3',
		meta: { seed: 20452860, clueCount: 6, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-012',
		game: 'murdoku',
		number: 12,
		title: 'El cuchillo del pan',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1],
				[0, 2, 1, 3, 3, 4],
				[2, 2, 2, 3, 4, 4],
				[2, 2, 3, 3, 4, 4]
			],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 },
				{ id: 4, name: 'Patio', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'aparador', icon: 'shelf', row: 0, col: 5 },
				{ id: 'p2', name: 'planta aromática', icon: 'plant', row: 4, col: 1 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 3, col: 3 },
				{ id: 'p4', name: 'estantería', icon: 'shelf', row: 1, col: 0 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 0, col: 0 },
				{ id: 'p6', name: 'baúl', icon: 'chest', row: 5, col: 4 },
				{ id: 'p7', name: 'reloj', icon: 'clock', row: 5, col: 2 },
				{ id: 'p8', name: 'bodegón', icon: 'painting', row: 1, col: 3 },
				{ id: 'p9', name: 'candelabro', icon: 'lamp', row: 1, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 1 }]
			},
			{
				id: 's2',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Marta',
				initial: 'M',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's1' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's4',
				name: 'Lorenzo',
				initial: 'L',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Alicia',
				initial: 'A',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's2' }]
			}
		],
		victim: { name: 'Pilar', row: 5, col: 3 },
		solution: {
			s1: { row: 0, col: 1 },
			s2: { row: 2, col: 5 },
			s3: { row: 1, col: 2 },
			s4: { row: 4, col: 0 },
			s5: { row: 3, col: 4 }
		},
		killer: 's5',
		meta: { seed: 20460779, clueCount: 6, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-013',
		game: 'murdoku',
		number: 13,
		title: 'La vitrina vacía',
		setting: 'Un museo después del cierre',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[2, 2, 2, 4, 4, 4],
				[2, 2, 2, 4, 4, 4],
				[2, 1, 5, 4, 4, 4],
				[5, 5, 5, 5, 3, 3],
				[5, 5, 3, 3, 3, 3],
				[0, 0, 0, 3, 3, 3]
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
				{ id: 'p1', name: 'lámpara', icon: 'lamp', row: 2, col: 4 },
				{ id: 'p2', name: 'planta', icon: 'plant', row: 3, col: 0 },
				{ id: 'p3', name: 'vitrina', icon: 'shelf', row: 5, col: 0 },
				{ id: 'p4', name: 'retrato', icon: 'painting', row: 0, col: 5 },
				{ id: 'p5', name: 'busto', icon: 'statue', row: 5, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Julián',
				initial: 'J',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Alicia',
				initial: 'A',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Lorenzo',
				initial: 'L',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's2' },
					{ type: 'direction', who: 's5', dir: 'W', steps: 1, than: 's2' }
				]
			}
		],
		victim: { name: 'Sofía', row: 3, col: 5 },
		solution: {
			s1: { row: 5, col: 4 },
			s2: { row: 1, col: 2 },
			s3: { row: 0, col: 3 },
			s4: { row: 4, col: 0 },
			s5: { row: 2, col: 1 }
		},
		killer: 's1',
		meta: { seed: 20573427, clueCount: 6, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-014',
		game: 'murdoku',
		number: 14,
		title: 'El vagón restaurante',
		setting: 'Un tren nocturno detenido',
		difficulty: 'easy',
		size: 6,
		estimatedMinutes: 4,
		grid: {
			size: 6,
			regions: [
				[2, 2, 2, 2, 2, 2],
				[4, 2, 2, 2, 2, 2],
				[4, 2, 2, 2, 2, 2],
				[4, 4, 3, 3, 3, 3],
				[4, 4, 3, 3, 3, 3],
				[4, 3, 3, 3, 0, 1]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 0, col: 2 },
				{ id: 'p2', name: 'piano', icon: 'piano', row: 1, col: 0 },
				{ id: 'p3', name: 'baúl', icon: 'chest', row: 5, col: 0 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 3, col: 4 },
				{ id: 'p5', name: 'estantería', icon: 'shelf', row: 4, col: 1 },
				{ id: 'p6', name: 'planta', icon: 'plant', row: 5, col: 1 },
				{ id: 'p7', name: 'lámpara', icon: 'lamp', row: 1, col: 2 },
				{ id: 'p8', name: 'candelabro', icon: 'lamp', row: 1, col: 4 },
				{ id: 'p9', name: 'reloj', icon: 'clock', row: 2, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Lorenzo',
				initial: 'L',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 1 }]
			},
			{
				id: 's2',
				name: 'Diego',
				initial: 'D',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's5' },
					{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's5' }
				]
			},
			{
				id: 's3',
				name: 'Bruno',
				initial: 'B',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 2 }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 2 }, { type: 'nearProp', who: 's4', prop: 'p7' }]
			},
			{
				id: 's5',
				name: 'Karina',
				initial: 'K',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'N', steps: 1, than: 's2' }]
			}
		],
		victim: { name: 'Simón', row: 4, col: 0 },
		solution: {
			s1: { row: 5, col: 5 },
			s2: { row: 3, col: 1 },
			s3: { row: 0, col: 4 },
			s4: { row: 1, col: 3 },
			s5: { row: 2, col: 2 }
		},
		killer: 's2',
		meta: { seed: 20371888, clueCount: 7, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-015',
		game: 'murdoku',
		number: 15,
		title: 'La tormenta en el faro',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'easy',
		size: 7,
		estimatedMinutes: 6,
		grid: {
			size: 7,
			regions: [
				[5, 5, 2, 2, 2, 2, 2],
				[5, 2, 2, 2, 2, 2, 2],
				[5, 2, 2, 1, 1, 1, 1],
				[3, 3, 3, 4, 1, 1, 1],
				[3, 3, 3, 4, 1, 1, 0],
				[3, 3, 3, 4, 0, 0, 0],
				[3, 3, 3, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 },
				{ id: 4, name: 'Terraza', tone: 4 },
				{ id: 5, name: 'Muelle', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 4, col: 1 },
				{ id: 'p2', name: 'candelabro', icon: 'lamp', row: 4, col: 5 },
				{ id: 'p3', name: 'baúl', icon: 'chest', row: 2, col: 5 },
				{ id: 'p4', name: 'planta', icon: 'plant', row: 6, col: 5 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 0, col: 4 },
				{ id: 'p6', name: 'cuadro', icon: 'painting', row: 3, col: 6 },
				{ id: 'p7', name: 'estantería', icon: 'shelf', row: 3, col: 3 },
				{ id: 'p8', name: 'busto', icon: 'statue', row: 4, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Diego',
				initial: 'D',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's2' },
					{ type: 'nearProp', who: 's1', prop: 'p4' }
				]
			},
			{
				id: 's2',
				name: 'Karina',
				initial: 'K',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's4' }]
			},
			{
				id: 's4',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Irene',
				initial: 'I',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's2' }]
			},
			{
				id: 's6',
				name: 'Carla',
				initial: 'C',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's3' }]
			}
		],
		victim: { name: 'Simón', row: 6, col: 1 },
		solution: {
			s1: { row: 5, col: 5 },
			s2: { row: 0, col: 6 },
			s3: { row: 2, col: 3 },
			s4: { row: 3, col: 4 },
			s5: { row: 1, col: 0 },
			s6: { row: 4, col: 2 }
		},
		killer: 's6',
		meta: { seed: 20379807, clueCount: 7, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-016',
		game: 'murdoku',
		number: 16,
		title: 'La función terminó',
		setting: 'Un teatro después de la función',
		difficulty: 'easy',
		size: 7,
		estimatedMinutes: 6,
		grid: {
			size: 7,
			regions: [
				[3, 3, 3, 1, 1, 1, 1],
				[3, 3, 3, 1, 1, 1, 1],
				[3, 3, 2, 1, 1, 1, 1],
				[2, 4, 2, 1, 1, 1, 1],
				[2, 2, 2, 1, 5, 5, 5],
				[2, 2, 2, 0, 5, 5, 5],
				[0, 0, 0, 0, 5, 5, 5]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 },
				{ id: 4, name: 'Vestíbulo', tone: 4 },
				{ id: 5, name: 'Tramoya', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'reloj', icon: 'clock', row: 6, col: 5 },
				{ id: 'p2', name: 'piano', icon: 'piano', row: 1, col: 0 },
				{ id: 'p3', name: 'estantería', icon: 'shelf', row: 1, col: 1 },
				{ id: 'p4', name: 'cuadro', icon: 'painting', row: 0, col: 2 },
				{ id: 'p5', name: 'lámpara', icon: 'lamp', row: 3, col: 4 },
				{ id: 'p6', name: 'candelabro', icon: 'lamp', row: 6, col: 2 },
				{ id: 'p7', name: 'baúl', icon: 'chest', row: 3, col: 2 },
				{ id: 'p8', name: 'retrato', icon: 'painting', row: 6, col: 3 },
				{ id: 'p9', name: 'planta', icon: 'plant', row: 5, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 1 }]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's1' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's2' }
				]
			},
			{
				id: 's4',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's5' }]
			},
			{
				id: 's5',
				name: 'Fabián',
				initial: 'F',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 1 }, { type: 'nearProp', who: 's5', prop: 'p7' }]
			},
			{
				id: 's6',
				name: 'Elena',
				initial: 'E',
				color: 'purple',
				clues: [{ type: 'region', who: 's6', region: 0 }]
			}
		],
		victim: { name: 'Sofía', row: 5, col: 0 },
		solution: {
			s1: { row: 0, col: 4 },
			s2: { row: 4, col: 5 },
			s3: { row: 1, col: 6 },
			s4: { row: 2, col: 2 },
			s5: { row: 3, col: 3 },
			s6: { row: 6, col: 1 }
		},
		killer: 's4',
		meta: { seed: 21958661, clueCount: 8, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-017',
		game: 'murdoku',
		number: 17,
		title: 'Medianoche en el estudio',
		setting: 'Una mansión a medianoche',
		difficulty: 'easy',
		size: 7,
		estimatedMinutes: 6,
		grid: {
			size: 7,
			regions: [
				[4, 4, 4, 2, 2, 2, 3],
				[4, 4, 4, 0, 3, 2, 3],
				[4, 4, 4, 0, 3, 3, 3],
				[4, 4, 4, 0, 0, 3, 3],
				[1, 4, 4, 0, 0, 3, 3],
				[1, 1, 4, 0, 0, 3, 3],
				[1, 1, 1, 1, 1, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 },
				{ id: 4, name: 'Jardín', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estantería', icon: 'shelf', row: 2, col: 1 },
				{ id: 'p2', name: 'candelabro', icon: 'lamp', row: 4, col: 3 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 3, col: 4 },
				{ id: 'p4', name: 'piano', icon: 'piano', row: 1, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Bruno',
				initial: 'B',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'S', steps: 1, than: 's1' },
					{ type: 'colEdge', who: 's4', edge: 'right' }
				]
			},
			{
				id: 's5',
				name: 'Alicia',
				initial: 'A',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 1 }, { type: 'colEdge', who: 's5', edge: 'left' }]
			},
			{
				id: 's6',
				name: 'Carla',
				initial: 'C',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'S', steps: 1, than: 's2' },
					{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's2' }
				]
			}
		],
		victim: { name: 'Vera', row: 0, col: 3 },
		solution: {
			s1: { row: 2, col: 4 },
			s2: { row: 4, col: 2 },
			s3: { row: 1, col: 5 },
			s4: { row: 3, col: 6 },
			s5: { row: 6, col: 0 },
			s6: { row: 5, col: 1 }
		},
		killer: 's3',
		meta: { seed: 20395645, clueCount: 9, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-018',
		game: 'murdoku',
		number: 18,
		title: 'Silencio en la biblioteca',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'easy',
		size: 7,
		estimatedMinutes: 6,
		grid: {
			size: 7,
			regions: [
				[2, 2, 3, 3, 3, 3, 0],
				[2, 2, 2, 3, 3, 3, 3],
				[2, 2, 2, 2, 3, 3, 3],
				[1, 1, 2, 2, 2, 3, 3],
				[1, 1, 2, 2, 2, 2, 2],
				[1, 1, 2, 2, 2, 2, 2],
				[1, 1, 1, 1, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Galería', tone: 1 },
				{ id: 2, name: 'Sala de lectura', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'candelabro', icon: 'lamp', row: 0, col: 6 },
				{ id: 'p2', name: 'atril', icon: 'shelf', row: 1, col: 5 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 4, col: 6 },
				{ id: 'p4', name: 'cofre', icon: 'chest', row: 1, col: 0 },
				{ id: 'p5', name: 'busto', icon: 'statue', row: 2, col: 3 },
				{ id: 'p6', name: 'cuadro', icon: 'painting', row: 6, col: 4 },
				{ id: 'p7', name: 'planta', icon: 'plant', row: 0, col: 1 },
				{ id: 'p8', name: 'reloj', icon: 'clock', row: 5, col: 1 },
				{ id: 'p9', name: 'estatua', icon: 'statue', row: 0, col: 2 },
				{ id: 'p10', name: 'estantería', icon: 'shelf', row: 5, col: 5 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Gabriela',
				initial: 'G',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Alicia',
				initial: 'A',
				color: 'blue',
				clues: [
					{ type: 'region', who: 's2', region: 2 },
					{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's5' }
				]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's2' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's4' }
				]
			},
			{
				id: 's4',
				name: 'Bruno',
				initial: 'B',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 1 }]
			},
			{
				id: 's5',
				name: 'Marta',
				initial: 'M',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'N', steps: 1, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Irene',
				initial: 'I',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Tomás', row: 1, col: 6 },
		solution: {
			s1: { row: 3, col: 1 },
			s2: { row: 4, col: 4 },
			s3: { row: 5, col: 3 },
			s4: { row: 6, col: 2 },
			s5: { row: 2, col: 5 },
			s6: { row: 0, col: 0 }
		},
		killer: 's5',
		meta: { seed: 21346125, clueCount: 8, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-019',
		game: 'murdoku',
		number: 19,
		title: 'Rocío en el invernadero',
		setting: 'Un invernadero al amanecer',
		difficulty: 'easy',
		size: 7,
		estimatedMinutes: 6,
		grid: {
			size: 7,
			regions: [
				[3, 3, 3, 3, 3, 3, 3],
				[2, 2, 1, 3, 3, 3, 1],
				[2, 2, 1, 1, 3, 1, 1],
				[2, 2, 2, 1, 1, 1, 1],
				[2, 2, 2, 0, 1, 1, 1],
				[2, 2, 0, 0, 0, 1, 1],
				[2, 2, 0, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'arcón', icon: 'chest', row: 2, col: 6 },
				{ id: 'p2', name: 'helecho', icon: 'plant', row: 5, col: 6 },
				{ id: 'p3', name: 'cuadro', icon: 'painting', row: 3, col: 4 },
				{ id: 'p4', name: 'candelabro', icon: 'lamp', row: 3, col: 5 },
				{ id: 'p5', name: 'estantería', icon: 'shelf', row: 6, col: 3 },
				{ id: 'p6', name: 'piano', icon: 'piano', row: 1, col: 5 },
				{ id: 'p7', name: 'estatua', icon: 'statue', row: 0, col: 5 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Diego',
				initial: 'D',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 3 }]
			},
			{
				id: 's2',
				name: 'Bruno',
				initial: 'B',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Marta',
				initial: 'M',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's4' },
					{ type: 'region', who: 's3', region: 3 }
				]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'S', steps: 1, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Carla',
				initial: 'C',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's6',
				name: 'Gabriela',
				initial: 'G',
				color: 'purple',
				clues: [{ type: 'region', who: 's6', region: 3 }]
			}
		],
		victim: { name: 'Tomás', row: 4, col: 0 },
		solution: {
			s1: { row: 0, col: 2 },
			s2: { row: 5, col: 1 },
			s3: { row: 2, col: 4 },
			s4: { row: 6, col: 5 },
			s5: { row: 3, col: 6 },
			s6: { row: 1, col: 3 }
		},
		killer: 's2',
		meta: { seed: 20411483, clueCount: 7, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-020',
		game: 'murdoku',
		number: 20,
		title: 'La cena interrumpida',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'easy',
		size: 7,
		estimatedMinutes: 6,
		grid: {
			size: 7,
			regions: [
				[1, 1, 1, 1, 2, 2, 2],
				[1, 1, 2, 2, 2, 2, 2],
				[1, 3, 2, 2, 2, 2, 2],
				[3, 3, 3, 3, 3, 3, 3],
				[3, 3, 3, 3, 3, 0, 3],
				[0, 3, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'figura', icon: 'statue', row: 5, col: 3 },
				{ id: 'p2', name: 'planta aromática', icon: 'plant', row: 4, col: 3 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 3, col: 1 },
				{ id: 'p4', name: 'bodegón', icon: 'painting', row: 3, col: 3 },
				{ id: 'p5', name: 'lámpara', icon: 'lamp', row: 0, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Julián',
				initial: 'J',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's3' },
					{ type: 'direction', who: 's1', dir: 'E', steps: 2, than: 's4' }
				]
			},
			{
				id: 's2',
				name: 'Karina',
				initial: 'K',
				color: 'blue',
				clues: [
					{ type: 'region', who: 's2', region: 2 },
					{ type: 'direction', who: 's2', dir: 'N', steps: 1, than: 's3' }
				]
			},
			{
				id: 's3',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Hugo',
				initial: 'H',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'W', steps: 1, than: 's2' }]
			},
			{
				id: 's6',
				name: 'Carla',
				initial: 'C',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'N', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Teresa', row: 3, col: 0 },
		solution: {
			s1: { row: 6, col: 5 },
			s2: { row: 1, col: 2 },
			s3: { row: 2, col: 6 },
			s4: { row: 0, col: 3 },
			s5: { row: 4, col: 1 },
			s6: { row: 5, col: 4 }
		},
		killer: 's5',
		meta: { seed: 20628860, clueCount: 8, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-021',
		game: 'murdoku',
		number: 21,
		title: 'Después del cierre',
		setting: 'Un museo después del cierre',
		difficulty: 'medium',
		size: 7,
		estimatedMinutes: 7,
		grid: {
			size: 7,
			regions: [
				[0, 0, 0, 1, 1, 1, 1],
				[0, 0, 1, 1, 1, 3, 3],
				[2, 2, 2, 3, 3, 3, 3],
				[2, 2, 2, 3, 3, 3, 3],
				[2, 2, 3, 3, 3, 3, 3],
				[4, 4, 4, 3, 3, 3, 3],
				[4, 4, 3, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Sala egipcia', tone: 1 },
				{ id: 2, name: 'Sala griega', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 3, col: 2 },
				{ id: 'p2', name: 'planta', icon: 'plant', row: 0, col: 5 },
				{ id: 'p3', name: 'cofre', icon: 'chest', row: 5, col: 4 },
				{ id: 'p4', name: 'vitrina', icon: 'shelf', row: 0, col: 4 },
				{ id: 'p5', name: 'lámpara', icon: 'lamp', row: 0, col: 1 },
				{ id: 'p6', name: 'busto', icon: 'statue', row: 5, col: 6 },
				{ id: 'p7', name: 'estantería', icon: 'shelf', row: 0, col: 3 },
				{ id: 'p8', name: 'retrato', icon: 'painting', row: 4, col: 4 },
				{ id: 'p9', name: 'cuadro', icon: 'painting', row: 1, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 4, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 2 }]
			},
			{
				id: 's3',
				name: 'Hugo',
				initial: 'H',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 5, than: 's4' }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 2 }, { type: 'nearProp', who: 's4', prop: 'p3' }]
			},
			{
				id: 's5',
				name: 'Elena',
				initial: 'E',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'E', steps: 3, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Marta',
				initial: 'M',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'N', steps: 4, than: 's3' }]
			}
		],
		victim: { name: 'Pilar', row: 1, col: 3 },
		solution: {
			s1: { row: 4, col: 1 },
			s2: { row: 0, col: 6 },
			s3: { row: 6, col: 0 },
			s4: { row: 5, col: 5 },
			s5: { row: 3, col: 4 },
			s6: { row: 2, col: 2 }
		},
		killer: 's2',
		meta: { seed: 20741508, clueCount: 7, negatives: 2, complexity: 6, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-022',
		game: 'murdoku',
		number: 22,
		title: 'La litera nueve',
		setting: 'Un tren nocturno detenido',
		difficulty: 'medium',
		size: 7,
		estimatedMinutes: 7,
		grid: {
			size: 7,
			regions: [
				[2, 2, 2, 2, 2, 2, 5],
				[2, 2, 2, 2, 0, 5, 5],
				[1, 1, 2, 2, 0, 5, 5],
				[1, 1, 4, 2, 0, 3, 5],
				[4, 4, 4, 0, 0, 3, 3],
				[4, 4, 3, 3, 3, 3, 3],
				[4, 4, 4, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 },
				{ id: 5, name: 'Andén', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'candelabro', icon: 'lamp', row: 0, col: 6 },
				{ id: 'p2', name: 'cuadro', icon: 'painting', row: 2, col: 6 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 1, col: 3 },
				{ id: 'p4', name: 'estantería', icon: 'shelf', row: 3, col: 2 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 5, col: 6 },
				{ id: 'p6', name: 'maleta', icon: 'chest', row: 4, col: 5 },
				{ id: 'p7', name: 'lámpara', icon: 'lamp', row: 1, col: 0 },
				{ id: 'p8', name: 'estatua', icon: 'statue', row: 4, col: 1 },
				{ id: 'p9', name: 'baúl', icon: 'chest', row: 4, col: 6 },
				{ id: 'p10', name: 'piano', icon: 'piano', row: 0, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 5 }]
			},
			{
				id: 's2',
				name: 'Nicolás',
				initial: 'N',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 3, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Julián',
				initial: 'J',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 1 }]
			},
			{
				id: 's4',
				name: 'Olivia',
				initial: 'O',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 5 },
					{ type: 'direction', who: 's4', dir: 'N', steps: 4, than: 's2' }
				]
			},
			{
				id: 's5',
				name: 'Irene',
				initial: 'I',
				color: 'pink',
				clues: [
					{ type: 'notRegion', who: 's5', region: 5 },
					{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's6',
				name: 'Hugo',
				initial: 'H',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'E', steps: 3, than: 's1' },
					{ type: 'region', who: 's6', region: 2 }
				]
			}
		],
		victim: { name: 'Ramiro', row: 5, col: 0 },
		solution: {
			s1: { row: 1, col: 2 },
			s2: { row: 6, col: 1 },
			s3: { row: 3, col: 6 },
			s4: { row: 2, col: 4 },
			s5: { row: 4, col: 3 },
			s6: { row: 0, col: 5 }
		},
		killer: 's2',
		meta: { seed: 20539969, clueCount: 9, negatives: 4, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-023',
		game: 'murdoku',
		number: 23,
		title: 'La lámpara apagada',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'medium',
		size: 7,
		estimatedMinutes: 7,
		grid: {
			size: 7,
			regions: [
				[2, 2, 2, 2, 3, 3, 3],
				[2, 2, 0, 0, 0, 3, 3],
				[2, 0, 0, 0, 0, 3, 3],
				[0, 0, 0, 0, 3, 3, 3],
				[0, 0, 0, 3, 3, 3, 3],
				[5, 1, 1, 3, 3, 3, 4],
				[5, 1, 1, 3, 3, 4, 4]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 },
				{ id: 4, name: 'Terraza', tone: 4 },
				{ id: 5, name: 'Muelle', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'planta', icon: 'plant', row: 2, col: 2 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 1, col: 6 },
				{ id: 'p3', name: 'reloj', icon: 'clock', row: 4, col: 0 },
				{ id: 'p4', name: 'baúl', icon: 'chest', row: 4, col: 2 },
				{ id: 'p5', name: 'estantería', icon: 'shelf', row: 3, col: 1 },
				{ id: 'p6', name: 'estatua', icon: 'statue', row: 6, col: 6 },
				{ id: 'p7', name: 'cuadro', icon: 'painting', row: 0, col: 6 },
				{ id: 'p8', name: 'candelabro', icon: 'lamp', row: 2, col: 1 },
				{ id: 'p9', name: 'piano', icon: 'piano', row: 5, col: 3 },
				{ id: 'p10', name: 'busto', icon: 'statue', row: 5, col: 5 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Irene',
				initial: 'I',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 0 }]
			},
			{
				id: 's2',
				name: 'Julián',
				initial: 'J',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 3 }]
			},
			{
				id: 's3',
				name: 'Diego',
				initial: 'D',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 4 }, { type: 'nearProp', who: 's3', prop: 'p1' }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'E', steps: 3, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Nicolás',
				initial: 'N',
				color: 'pink',
				clues: [
					{ type: 'notRegion', who: 's5', region: 4 },
					{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's3' }
				]
			},
			{
				id: 's6',
				name: 'Carla',
				initial: 'C',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'S', steps: 2, than: 's2' },
					{ type: 'direction', who: 's6', dir: 'N', steps: 1, than: 's5' }
				]
			}
		],
		victim: { name: 'Lucía', row: 5, col: 1 },
		solution: {
			s1: { row: 6, col: 2 },
			s2: { row: 1, col: 0 },
			s3: { row: 2, col: 3 },
			s4: { row: 0, col: 5 },
			s5: { row: 4, col: 4 },
			s6: { row: 3, col: 6 }
		},
		killer: 's1',
		meta: { seed: 20757346, clueCount: 9, negatives: 4, complexity: 7, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-024',
		game: 'murdoku',
		number: 24,
		title: 'El palco abandonado',
		setting: 'Un teatro después de la función',
		difficulty: 'medium',
		size: 7,
		estimatedMinutes: 7,
		grid: {
			size: 7,
			regions: [
				[0, 0, 0, 0, 0, 1, 1],
				[2, 0, 0, 3, 1, 1, 1],
				[2, 2, 0, 3, 1, 1, 1],
				[2, 2, 2, 3, 3, 1, 1],
				[2, 2, 2, 2, 1, 1, 1],
				[2, 2, 2, 2, 1, 1, 1],
				[2, 2, 2, 2, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'estantería', icon: 'shelf', row: 3, col: 6 },
				{ id: 'p2', name: 'planta', icon: 'plant', row: 6, col: 5 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 3, col: 1 },
				{ id: 'p4', name: 'cuadro', icon: 'painting', row: 6, col: 2 },
				{ id: 'p5', name: 'retrato', icon: 'painting', row: 1, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Hugo',
				initial: 'H',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'N', steps: 4, than: 's4' },
					{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's5' }
				]
			},
			{
				id: 's2',
				name: 'Diego',
				initial: 'D',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 2, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Nicolás',
				initial: 'N',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'W', steps: 4, than: 's1' }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 0 }]
			},
			{
				id: 's5',
				name: 'Julián',
				initial: 'J',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 2, than: 's2' }]
			},
			{
				id: 's6',
				name: 'Karina',
				initial: 'K',
				color: 'purple',
				clues: [{ type: 'notRegion', who: 's6', region: 0 }]
			}
		],
		victim: { name: 'Sofía', row: 6, col: 0 },
		solution: {
			s1: { row: 1, col: 5 },
			s2: { row: 2, col: 3 },
			s3: { row: 0, col: 1 },
			s4: { row: 5, col: 6 },
			s5: { row: 4, col: 4 },
			s6: { row: 3, col: 2 }
		},
		killer: 's6',
		meta: { seed: 20451078, clueCount: 7, negatives: 2, complexity: 6, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-025',
		game: 'murdoku',
		number: 25,
		title: 'El sillón vacío',
		setting: 'Una mansión a medianoche',
		difficulty: 'medium',
		size: 7,
		estimatedMinutes: 7,
		grid: {
			size: 7,
			regions: [
				[3, 3, 3, 0, 0, 0, 1],
				[3, 3, 3, 0, 2, 1, 1],
				[3, 3, 3, 0, 2, 1, 1],
				[3, 2, 2, 2, 2, 1, 1],
				[2, 2, 2, 2, 2, 1, 1],
				[2, 2, 2, 2, 1, 1, 1],
				[2, 2, 2, 2, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 4, col: 1 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 0, col: 0 },
				{ id: 'p3', name: 'cuadro', icon: 'painting', row: 1, col: 5 },
				{ id: 'p4', name: 'baúl', icon: 'chest', row: 6, col: 1 },
				{ id: 'p5', name: 'planta', icon: 'plant', row: 6, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [
					{ type: 'notRegion', who: 's1', region: 1 },
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's6' }
				]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 1 }]
			},
			{
				id: 's3',
				name: 'Fabián',
				initial: 'F',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'E', steps: 2, than: 's4' },
					{ type: 'nearProp', who: 's3', prop: 'p3' }
				]
			},
			{
				id: 's4',
				name: 'Diego',
				initial: 'D',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'S', steps: 2, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Julián',
				initial: 'J',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 6, than: 's2' }]
			},
			{
				id: 's6',
				name: 'Bruno',
				initial: 'B',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'N', steps: 2, than: 's5' }]
			}
		],
		victim: { name: 'Simón', row: 2, col: 0 },
		solution: {
			s1: { row: 3, col: 2 },
			s2: { row: 0, col: 1 },
			s3: { row: 1, col: 6 },
			s4: { row: 5, col: 4 },
			s5: { row: 6, col: 5 },
			s6: { row: 4, col: 3 }
		},
		killer: 's2',
		meta: { seed: 20773184, clueCount: 8, negatives: 2, complexity: 6, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-026',
		game: 'murdoku',
		number: 26,
		title: 'La escala prohibida',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'medium',
		size: 7,
		estimatedMinutes: 7,
		grid: {
			size: 7,
			regions: [
				[0, 0, 0, 0, 4, 4, 4],
				[5, 0, 5, 4, 4, 4, 4],
				[5, 5, 5, 4, 4, 4, 2],
				[5, 5, 5, 4, 2, 2, 2],
				[5, 1, 1, 3, 2, 2, 2],
				[1, 1, 1, 3, 2, 2, 2],
				[1, 1, 1, 3, 3, 2, 2]
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
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 4, col: 6 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 1, col: 6 },
				{ id: 'p3', name: 'estantería', icon: 'shelf', row: 4, col: 3 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 0, col: 5 },
				{ id: 'p5', name: 'estatua', icon: 'statue', row: 3, col: 4 },
				{ id: 'p6', name: 'planta', icon: 'plant', row: 2, col: 6 },
				{ id: 'p7', name: 'atril', icon: 'shelf', row: 6, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'E', steps: 3, than: 's2' },
					{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's4' }
				]
			},
			{
				id: 's2',
				name: 'Bruno',
				initial: 'B',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 3, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 0 }]
			},
			{
				id: 's4',
				name: 'Marta',
				initial: 'M',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 1 },
					{ type: 'direction', who: 's4', dir: 'E', steps: 1, than: 's2' }
				]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'E', steps: 4, than: 's2' },
					{ type: 'nearProp', who: 's5', prop: 'p3' }
				]
			},
			{
				id: 's6',
				name: 'Lorenzo',
				initial: 'L',
				color: 'purple',
				clues: [
					{ type: 'notRegion', who: 's6', region: 0 },
					{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's1' }
				]
			}
		],
		victim: { name: 'Ramiro', row: 0, col: 6 },
		solution: {
			s1: { row: 2, col: 3 },
			s2: { row: 5, col: 0 },
			s3: { row: 6, col: 5 },
			s4: { row: 3, col: 1 },
			s5: { row: 4, col: 4 },
			s6: { row: 1, col: 2 }
		},
		killer: 's1',
		meta: { seed: 20885832, clueCount: 10, negatives: 3, complexity: 7, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-027',
		game: 'murdoku',
		number: 27,
		title: 'La maceta volcada',
		setting: 'Un invernadero al amanecer',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[0, 0, 0, 1, 1, 2, 2, 2],
				[0, 0, 0, 1, 1, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 0, 0],
				[3, 3, 3, 0, 0, 0, 0, 0],
				[3, 3, 3, 0, 0, 0, 0, 0],
				[4, 3, 3, 4, 4, 0, 0, 4],
				[4, 4, 4, 4, 4, 4, 4, 4],
				[4, 4, 4, 4, 4, 4, 4, 4]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'piano', icon: 'piano', row: 1, col: 4 },
				{ id: 'p2', name: 'estatua', icon: 'statue', row: 5, col: 3 },
				{ id: 'p3', name: 'helecho', icon: 'plant', row: 2, col: 7 },
				{ id: 'p4', name: 'cuadro', icon: 'painting', row: 1, col: 0 },
				{ id: 'p5', name: 'candelabro', icon: 'lamp', row: 4, col: 3 },
				{ id: 'p6', name: 'estantería', icon: 'shelf', row: 0, col: 2 },
				{ id: 'p7', name: 'lámpara', icon: 'lamp', row: 6, col: 6 },
				{ id: 'p8', name: 'arcón', icon: 'chest', row: 0, col: 0 },
				{ id: 'p9', name: 'maceta', icon: 'plant', row: 0, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 3, than: 's2' },
					{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's4' }
				]
			},
			{
				id: 's2',
				name: 'Julián',
				initial: 'J',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 3, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Hugo',
				initial: 'H',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 1 }, { type: 'region', who: 's3', region: 2 }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'N', steps: 3, than: 's2' },
					{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's5' }
				]
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
				name: 'Gabriela',
				initial: 'G',
				color: 'purple',
				clues: [
					{ type: 'notRegion', who: 's6', region: 1 },
					{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's3' }
				]
			},
			{
				id: 's7',
				name: 'Diego',
				initial: 'D',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'S', steps: 2, than: 's1' }]
			}
		],
		victim: { name: 'Lucía', row: 6, col: 2 },
		solution: {
			s1: { row: 1, col: 3 },
			s2: { row: 5, col: 6 },
			s3: { row: 0, col: 5 },
			s4: { row: 2, col: 0 },
			s5: { row: 4, col: 1 },
			s6: { row: 7, col: 4 },
			s7: { row: 3, col: 7 }
		},
		killer: 's6',
		meta: { seed: 20579564, clueCount: 11, negatives: 3, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-028',
		game: 'murdoku',
		number: 28,
		title: 'Vapor en la despensa',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[2, 2, 2, 2, 2, 2, 2, 2],
				[1, 1, 1, 1, 1, 2, 2, 2],
				[1, 1, 1, 1, 1, 1, 2, 2],
				[0, 0, 1, 1, 1, 1, 2, 2],
				[0, 0, 0, 1, 1, 1, 4, 4],
				[0, 0, 0, 1, 1, 1, 4, 4],
				[3, 3, 3, 4, 4, 4, 4, 4],
				[3, 3, 3, 4, 4, 4, 4, 4]
			],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 },
				{ id: 4, name: 'Patio', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'figura', icon: 'statue', row: 7, col: 1 },
				{ id: 'p2', name: 'aparador', icon: 'shelf', row: 5, col: 5 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 7, col: 4 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 1, col: 1 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 2, col: 5 },
				{ id: 'p6', name: 'candelabro', icon: 'lamp', row: 4, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 2 }]
			},
			{
				id: 's2',
				name: 'Gabriela',
				initial: 'G',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 3, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Diego',
				initial: 'D',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 3, than: 's2' },
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's5' }
				]
			},
			{
				id: 's4',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 0 },
					{ type: 'direction', who: 's4', dir: 'W', steps: 4, than: 's3' }
				]
			},
			{
				id: 's5',
				name: 'Alicia',
				initial: 'A',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'N', steps: 2, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Hugo',
				initial: 'H',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'E', steps: 3, than: 's2' },
					{ type: 'direction', who: 's6', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's7',
				name: 'Marta',
				initial: 'M',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'N', steps: 5, than: 's1' }]
			}
		],
		victim: { name: 'Tomás', row: 4, col: 5 },
		solution: {
			s1: { row: 7, col: 3 },
			s2: { row: 3, col: 1 },
			s3: { row: 6, col: 6 },
			s4: { row: 0, col: 2 },
			s5: { row: 5, col: 0 },
			s6: { row: 1, col: 4 },
			s7: { row: 2, col: 7 }
		},
		killer: 's6',
		meta: { seed: 20482754, clueCount: 10, negatives: 2, complexity: 9, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-029',
		game: 'murdoku',
		number: 29,
		title: 'La sala egipcia',
		setting: 'Un museo después del cierre',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[0, 0, 0, 0, 1, 1, 1, 1],
				[0, 0, 0, 0, 1, 1, 1, 1],
				[0, 0, 0, 0, 1, 1, 1, 1],
				[0, 0, 0, 0, 0, 0, 0, 2],
				[3, 0, 0, 0, 0, 0, 0, 2],
				[3, 0, 0, 0, 0, 2, 2, 2],
				[3, 3, 3, 0, 0, 0, 2, 2],
				[3, 3, 3, 3, 3, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Sala egipcia', tone: 1 },
				{ id: 2, name: 'Sala griega', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 1, col: 0 },
				{ id: 'p2', name: 'busto', icon: 'statue', row: 2, col: 3 },
				{ id: 'p3', name: 'cofre', icon: 'chest', row: 5, col: 2 },
				{ id: 'p4', name: 'retrato', icon: 'painting', row: 0, col: 5 },
				{ id: 'p5', name: 'estantería', icon: 'shelf', row: 6, col: 5 },
				{ id: 'p6', name: 'planta', icon: 'plant', row: 4, col: 1 },
				{ id: 'p7', name: 'reloj', icon: 'clock', row: 6, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'N', steps: 7, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 6, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Alicia',
				initial: 'A',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 2, than: 's6' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's4' }
				]
			},
			{
				id: 's4',
				name: 'Gabriela',
				initial: 'G',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 6, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Lorenzo',
				initial: 'L',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'N', steps: 4, than: 's3' }]
			},
			{
				id: 's6',
				name: 'Diego',
				initial: 'D',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'S', steps: 4, than: 's1' }]
			},
			{
				id: 's7',
				name: 'Elena',
				initial: 'E',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'S', steps: 2, than: 's4' },
					{ type: 'direction', who: 's7', dir: 'W', steps: 4, than: 's5' }
				]
			}
		],
		victim: { name: 'Teresa', row: 5, col: 1 },
		solution: {
			s1: { row: 0, col: 4 },
			s2: { row: 7, col: 2 },
			s3: { row: 6, col: 6 },
			s4: { row: 1, col: 5 },
			s5: { row: 2, col: 7 },
			s6: { row: 4, col: 0 },
			s7: { row: 3, col: 3 }
		},
		killer: 's7',
		meta: { seed: 20595402, clueCount: 9, negatives: 0, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-030',
		game: 'murdoku',
		number: 30,
		title: 'El andén sin luces',
		setting: 'Un tren nocturno detenido',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[1, 1, 1, 1, 1, 1, 3, 3],
				[1, 1, 1, 1, 1, 1, 3, 3],
				[1, 1, 1, 1, 1, 1, 3, 3],
				[1, 1, 1, 1, 1, 1, 3, 3],
				[1, 1, 1, 1, 1, 0, 3, 3],
				[4, 4, 0, 0, 0, 0, 0, 0],
				[4, 4, 0, 0, 0, 0, 0, 0],
				[4, 4, 4, 0, 0, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estantería', icon: 'shelf', row: 0, col: 5 },
				{ id: 'p2', name: 'cuadro', icon: 'painting', row: 4, col: 2 },
				{ id: 'p3', name: 'baúl', icon: 'chest', row: 5, col: 6 },
				{ id: 'p4', name: 'piano', icon: 'piano', row: 1, col: 1 },
				{ id: 'p5', name: 'planta', icon: 'plant', row: 1, col: 3 },
				{ id: 'p6', name: 'estatua', icon: 'statue', row: 4, col: 3 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Julián',
				initial: 'J',
				color: 'green',
				clues: [
					{ type: 'notRegion', who: 's1', region: 1 },
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's7' }
				]
			},
			{
				id: 's2',
				name: 'Lorenzo',
				initial: 'L',
				color: 'blue',
				clues: [{ type: 'notRegion', who: 's2', region: 3 }, { type: 'nearProp', who: 's2', prop: 'p5' }]
			},
			{
				id: 's3',
				name: 'Hugo',
				initial: 'H',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 0 }]
			},
			{
				id: 's4',
				name: 'Karina',
				initial: 'K',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'E', steps: 3, than: 's3' }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [
					{ type: 'notRegion', who: 's5', region: 2 },
					{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's3' }
				]
			},
			{
				id: 's6',
				name: 'Nicolás',
				initial: 'N',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'N', steps: 5, than: 's1' },
					{ type: 'region', who: 's6', region: 3 }
				]
			},
			{
				id: 's7',
				name: 'Irene',
				initial: 'I',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'S', steps: 2, than: 's2' }]
			}
		],
		victim: { name: 'Sofía', row: 5, col: 0 },
		solution: {
			s1: { row: 6, col: 1 },
			s2: { row: 0, col: 3 },
			s3: { row: 3, col: 4 },
			s4: { row: 7, col: 7 },
			s5: { row: 4, col: 5 },
			s6: { row: 1, col: 6 },
			s7: { row: 2, col: 2 }
		},
		killer: 's1',
		meta: { seed: 21022237, clueCount: 11, negatives: 4, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-031',
		game: 'murdoku',
		number: 31,
		title: 'El mar embravecido',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[1, 1, 5, 5, 5, 2, 3, 3],
				[1, 1, 1, 5, 5, 2, 3, 3],
				[1, 1, 1, 5, 5, 5, 5, 3],
				[4, 1, 1, 4, 5, 5, 5, 0],
				[4, 4, 4, 4, 4, 5, 0, 0],
				[4, 4, 4, 4, 4, 0, 0, 0],
				[4, 4, 4, 4, 0, 0, 0, 0],
				[4, 4, 4, 4, 4, 4, 4, 0]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 },
				{ id: 4, name: 'Terraza', tone: 4 },
				{ id: 5, name: 'Muelle', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'planta', icon: 'plant', row: 4, col: 5 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 3, col: 5 },
				{ id: 'p3', name: 'piano', icon: 'piano', row: 6, col: 3 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 1, col: 4 },
				{ id: 'p5', name: 'estatua', icon: 'statue', row: 7, col: 0 },
				{ id: 'p6', name: 'cuadro', icon: 'painting', row: 4, col: 3 },
				{ id: 'p7', name: 'baúl', icon: 'chest', row: 7, col: 2 },
				{ id: 'p8', name: 'candelabro', icon: 'lamp', row: 1, col: 5 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [
					{ type: 'notRegion', who: 's1', region: 1 },
					{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's3' }
				]
			},
			{
				id: 's2',
				name: 'Alicia',
				initial: 'A',
				color: 'blue',
				clues: [
					{ type: 'notRegion', who: 's2', region: 3 },
					{ type: 'direction', who: 's2', dir: 'S', steps: 3, than: 's4' }
				]
			},
			{
				id: 's3',
				name: 'Fabián',
				initial: 'F',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'E', steps: 4, than: 's5' },
					{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's5' }
				]
			},
			{
				id: 's4',
				name: 'Nicolás',
				initial: 'N',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 0 }]
			},
			{
				id: 's5',
				name: 'Bruno',
				initial: 'B',
				color: 'pink',
				clues: [{ type: 'notRegion', who: 's5', region: 5 }, { type: 'nearProp', who: 's5', prop: 'p5' }]
			},
			{
				id: 's6',
				name: 'Diego',
				initial: 'D',
				color: 'purple',
				clues: [
					{ type: 'notRegion', who: 's6', region: 5 },
					{ type: 'direction', who: 's6', dir: 'S', steps: 1, than: 's7' }
				]
			},
			{
				id: 's7',
				name: 'Elena',
				initial: 'E',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'N', steps: 5, than: 's2' },
					{ type: 'direction', who: 's7', dir: 'W', steps: 1, than: 's4' }
				]
			}
		],
		victim: { name: 'Pilar', row: 4, col: 0 },
		solution: {
			s1: { row: 3, col: 6 },
			s2: { row: 5, col: 7 },
			s3: { row: 6, col: 5 },
			s4: { row: 2, col: 4 },
			s5: { row: 7, col: 1 },
			s6: { row: 1, col: 2 },
			s7: { row: 0, col: 3 }
		},
		killer: 's5',
		meta: { seed: 20611240, clueCount: 13, negatives: 5, complexity: 9, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-032',
		game: 'murdoku',
		number: 32,
		title: 'Telón abajo',
		setting: 'Un teatro después de la función',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[2, 0, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 0, 2, 0, 0, 0],
				[2, 2, 2, 2, 2, 2, 0, 0],
				[2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 1, 1],
				[2, 2, 2, 2, 3, 3, 1, 1],
				[2, 2, 2, 2, 2, 2, 1, 1],
				[2, 2, 2, 2, 2, 2, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 6, col: 1 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 6, col: 2 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 1, col: 4 },
				{ id: 'p4', name: 'baúl', icon: 'chest', row: 7, col: 6 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 0, col: 2 },
				{ id: 'p6', name: 'planta', icon: 'plant', row: 3, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Fabián',
				initial: 'F',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 3, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'W', steps: 3, than: 's1' },
					{ type: 'direction', who: 's2', dir: 'N', steps: 1, than: 's5' }
				]
			},
			{
				id: 's3',
				name: 'Gabriela',
				initial: 'G',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'E', steps: 6, than: 's2' },
					{ type: 'nearProp', who: 's3', prop: 'p4' }
				]
			},
			{
				id: 's4',
				name: 'Irene',
				initial: 'I',
				color: 'orange',
				clues: [
					{ type: 'notRegion', who: 's4', region: 1 },
					{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's3' }
				]
			},
			{
				id: 's5',
				name: 'Marta',
				initial: 'M',
				color: 'pink',
				clues: [
					{ type: 'notRegion', who: 's5', region: 1 },
					{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's2' }
				]
			},
			{
				id: 's6',
				name: 'Diego',
				initial: 'D',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'N', steps: 4, than: 's2' }]
			},
			{
				id: 's7',
				name: 'Hugo',
				initial: 'H',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'W', steps: 4, than: 's3' }]
			}
		],
		victim: { name: 'Nadia', row: 2, col: 6 },
		solution: {
			s1: { row: 3, col: 4 },
			s2: { row: 4, col: 1 },
			s3: { row: 7, col: 7 },
			s4: { row: 6, col: 5 },
			s5: { row: 5, col: 2 },
			s6: { row: 0, col: 0 },
			s7: { row: 1, col: 3 }
		},
		killer: 's7',
		meta: { seed: 20933346, clueCount: 11, negatives: 2, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-033',
		game: 'murdoku',
		number: 33,
		title: 'La puerta del estudio',
		setting: 'Una mansión a medianoche',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[1, 1, 1, 1, 1, 1, 1, 0],
				[1, 1, 1, 1, 1, 1, 0, 0],
				[1, 1, 1, 1, 1, 1, 0, 0],
				[2, 2, 1, 1, 1, 1, 1, 0],
				[2, 2, 1, 1, 1, 1, 1, 1],
				[2, 2, 3, 3, 1, 1, 1, 1],
				[2, 2, 3, 3, 3, 1, 1, 1],
				[2, 2, 3, 3, 3, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'piano', icon: 'piano', row: 3, col: 6 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 6, col: 5 },
				{ id: 'p3', name: 'baúl', icon: 'chest', row: 7, col: 3 },
				{ id: 'p4', name: 'lámpara', icon: 'lamp', row: 2, col: 2 },
				{ id: 'p5', name: 'cuadro', icon: 'painting', row: 2, col: 6 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 0, col: 2 },
				{ id: 'p7', name: 'retrato', icon: 'painting', row: 1, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Marta',
				initial: 'M',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 5, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 4, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Lorenzo',
				initial: 'L',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'N', steps: 3, than: 's6' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 5, than: 's4' }
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
				name: 'Bruno',
				initial: 'B',
				color: 'pink',
				clues: [
					{ type: 'notRegion', who: 's5', region: 1 },
					{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's6',
				name: 'Elena',
				initial: 'E',
				color: 'purple',
				clues: [{ type: 'notRegion', who: 's6', region: 0 }]
			},
			{
				id: 's7',
				name: 'Karina',
				initial: 'K',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'W', steps: 2, than: 's2' }]
			}
		],
		victim: { name: 'Simón', row: 6, col: 4 },
		solution: {
			s1: { row: 7, col: 6 },
			s2: { row: 3, col: 3 },
			s3: { row: 2, col: 5 },
			s4: { row: 0, col: 0 },
			s5: { row: 1, col: 7 },
			s6: { row: 5, col: 2 },
			s7: { row: 4, col: 1 }
		},
		killer: 's6',
		meta: { seed: 21150723, clueCount: 9, negatives: 2, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-034',
		game: 'murdoku',
		number: 34,
		title: 'El catálogo roto',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'medium',
		size: 8,
		estimatedMinutes: 8,
		grid: {
			size: 8,
			regions: [
				[4, 2, 2, 3, 3, 3, 3, 3],
				[4, 4, 2, 3, 3, 3, 3, 3],
				[4, 4, 2, 1, 3, 3, 3, 3],
				[4, 4, 2, 1, 3, 3, 3, 3],
				[4, 4, 1, 1, 1, 1, 1, 3],
				[4, 4, 1, 1, 1, 0, 0, 0],
				[4, 1, 1, 0, 0, 0, 0, 0],
				[1, 1, 1, 0, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Galería', tone: 1 },
				{ id: 2, name: 'Sala de lectura', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 },
				{ id: 4, name: 'Patio', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estantería', icon: 'shelf', row: 2, col: 4 },
				{ id: 'p2', name: 'cuadro', icon: 'painting', row: 1, col: 3 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 1, col: 1 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 2, col: 2 },
				{ id: 'p5', name: 'candelabro', icon: 'lamp', row: 2, col: 5 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [{ type: 'notRegion', who: 's1', region: 4 }]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 4, than: 's1' }]
			},
			{
				id: 's3',
				name: 'Alicia',
				initial: 'A',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'S', steps: 6, than: 's6' }]
			},
			{
				id: 's4',
				name: 'Lorenzo',
				initial: 'L',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 5, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Karina',
				initial: 'K',
				color: 'pink',
				clues: [{ type: 'notRegion', who: 's5', region: 4 }, { type: 'region', who: 's5', region: 0 }]
			},
			{
				id: 's6',
				name: 'Gabriela',
				initial: 'G',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 3, than: 's1' }]
			},
			{
				id: 's7',
				name: 'Hugo',
				initial: 'H',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'N', steps: 3, than: 's1' },
					{ type: 'direction', who: 's7', dir: 'W', steps: 1, than: 's4' }
				]
			}
		],
		victim: { name: 'Sofía', row: 2, col: 6 },
		solution: {
			s1: { row: 7, col: 3 },
			s2: { row: 3, col: 7 },
			s3: { row: 6, col: 4 },
			s4: { row: 1, col: 2 },
			s5: { row: 5, col: 5 },
			s6: { row: 0, col: 0 },
			s7: { row: 4, col: 1 }
		},
		killer: 's2',
		meta: { seed: 20634997, clueCount: 9, negatives: 2, complexity: 7, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-035',
		game: 'murdoku',
		number: 35,
		title: 'El cristal empañado',
		setting: 'Un invernadero al amanecer',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[4, 4, 4, 4, 4, 4, 4, 2, 2],
				[4, 5, 4, 4, 4, 4, 4, 2, 2],
				[5, 5, 5, 5, 2, 2, 2, 2, 2],
				[5, 5, 5, 5, 5, 2, 2, 2, 2],
				[5, 5, 5, 5, 5, 0, 0, 0, 0],
				[5, 1, 5, 5, 5, 3, 0, 0, 0],
				[1, 1, 1, 1, 1, 3, 3, 3, 0],
				[1, 1, 3, 3, 1, 3, 3, 3, 3],
				[3, 3, 3, 3, 3, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 },
				{ id: 5, name: 'Cobertizo', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'reloj', icon: 'clock', row: 5, col: 1 },
				{ id: 'p2', name: 'estatua', icon: 'statue', row: 3, col: 5 },
				{ id: 'p3', name: 'maceta', icon: 'plant', row: 7, col: 1 },
				{ id: 'p4', name: 'estantería', icon: 'shelf', row: 8, col: 8 },
				{ id: 'p5', name: 'arcón', icon: 'chest', row: 5, col: 3 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's3' },
					{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's7' }
				]
			},
			{
				id: 's2',
				name: 'Hugo',
				initial: 'H',
				color: 'blue',
				clues: [{ type: 'region', who: 's2', region: 5 }]
			},
			{
				id: 's3',
				name: 'Irene',
				initial: 'I',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's1' },
					{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's5' }
				]
			},
			{
				id: 's4',
				name: 'Olivia',
				initial: 'O',
				color: 'orange',
				clues: [
					{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's2' },
					{ type: 'direction', who: 's4', dir: 'N', steps: 3, than: 's1' }
				]
			},
			{
				id: 's5',
				name: 'Julián',
				initial: 'J',
				color: 'pink',
				clues: [
					{ type: 'region', who: 's5', region: 0 },
					{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's2' }
				]
			},
			{
				id: 's6',
				name: 'Bruno',
				initial: 'B',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's8' }]
			},
			{
				id: 's7',
				name: 'Karina',
				initial: 'K',
				color: 'red',
				clues: [{ type: 'region', who: 's7', region: 3 }]
			},
			{
				id: 's8',
				name: 'Lorenzo',
				initial: 'L',
				color: 'green',
				clues: [
					{ type: 'region', who: 's8', region: 5 },
					{ type: 'direction', who: 's8', dir: 'W', steps: 1, than: 's4' }
				]
			}
		],
		victim: { name: 'Tomás', row: 6, col: 4 },
		solution: {
			s1: { row: 5, col: 6 },
			s2: { row: 3, col: 3 },
			s3: { row: 0, col: 7 },
			s4: { row: 2, col: 2 },
			s5: { row: 4, col: 8 },
			s6: { row: 7, col: 0 },
			s7: { row: 8, col: 5 },
			s8: { row: 1, col: 1 }
		},
		killer: 's6',
		meta: { seed: 20642916, clueCount: 13, negatives: 0, complexity: 2, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-036',
		game: 'murdoku',
		number: 36,
		title: 'El horno encendido',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[0, 0, 0, 0, 0, 0, 5, 5, 5],
				[0, 0, 0, 2, 0, 0, 5, 5, 5],
				[0, 0, 0, 2, 2, 2, 2, 5, 5],
				[0, 0, 0, 2, 2, 2, 2, 2, 5],
				[3, 3, 2, 2, 2, 2, 2, 5, 5],
				[3, 3, 3, 3, 2, 2, 2, 2, 5],
				[3, 3, 3, 3, 2, 2, 2, 2, 2],
				[3, 3, 3, 3, 2, 2, 2, 2, 1],
				[3, 4, 4, 4, 4, 4, 2, 1, 1]
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
				{ id: 'p1', name: 'bodegón', icon: 'painting', row: 0, col: 4 },
				{ id: 'p2', name: 'planta aromática', icon: 'plant', row: 8, col: 1 },
				{ id: 'p3', name: 'lámpara', icon: 'lamp', row: 4, col: 2 },
				{ id: 'p4', name: 'estantería', icon: 'shelf', row: 6, col: 6 },
				{ id: 'p5', name: 'figura', icon: 'statue', row: 6, col: 0 },
				{ id: 'p6', name: 'piano', icon: 'piano', row: 5, col: 6 },
				{ id: 'p7', name: 'baúl', icon: 'chest', row: 4, col: 0 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Fabián',
				initial: 'F',
				color: 'blue',
				clues: [{ type: 'region', who: 's2', region: 5 }]
			},
			{
				id: 's3',
				name: 'Karina',
				initial: 'K',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's2' }]
			},
			{
				id: 's4',
				name: 'Diego',
				initial: 'D',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Julián',
				initial: 'J',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 1 }]
			},
			{
				id: 's6',
				name: 'Marta',
				initial: 'M',
				color: 'purple',
				clues: [{ type: 'region', who: 's6', region: 3 }]
			},
			{
				id: 's7',
				name: 'Gabriela',
				initial: 'G',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'N', steps: 1, than: 's1' }]
			},
			{
				id: 's8',
				name: 'Lorenzo',
				initial: 'L',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's4' },
					{ type: 'direction', who: 's8', dir: 'W', steps: 2, than: 's1' }
				]
			}
		],
		victim: { name: 'Óscar', row: 7, col: 5 },
		solution: {
			s1: { row: 3, col: 2 },
			s2: { row: 4, col: 7 },
			s3: { row: 5, col: 4 },
			s4: { row: 0, col: 6 },
			s5: { row: 8, col: 8 },
			s6: { row: 6, col: 3 },
			s7: { row: 2, col: 1 },
			s8: { row: 1, col: 0 }
		},
		killer: 's3',
		meta: { seed: 21698125, clueCount: 9, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-037',
		game: 'murdoku',
		number: 37,
		title: 'El mármol roto',
		setting: 'Un museo después del cierre',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[2, 2, 3, 3, 3, 3, 3, 3, 3],
				[2, 2, 1, 3, 3, 3, 3, 3, 3],
				[2, 2, 1, 1, 1, 3, 3, 3, 3],
				[2, 2, 1, 1, 1, 3, 3, 3, 3],
				[2, 2, 1, 1, 4, 4, 0, 3, 3],
				[2, 2, 1, 1, 4, 4, 0, 0, 3],
				[2, 2, 2, 1, 0, 0, 0, 0, 5],
				[1, 1, 1, 1, 1, 1, 0, 5, 5],
				[1, 1, 1, 1, 1, 1, 0, 5, 5]
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
				{ id: 'p1', name: 'busto', icon: 'statue', row: 1, col: 1 },
				{ id: 'p2', name: 'cofre', icon: 'chest', row: 1, col: 2 },
				{ id: 'p3', name: 'vitrina', icon: 'shelf', row: 1, col: 5 },
				{ id: 'p4', name: 'planta', icon: 'plant', row: 8, col: 4 },
				{ id: 'p5', name: 'lámpara', icon: 'lamp', row: 7, col: 5 },
				{ id: 'p6', name: 'estatua', icon: 'statue', row: 4, col: 3 },
				{ id: 'p7', name: 'reloj', icon: 'clock', row: 5, col: 8 },
				{ id: 'p8', name: 'estantería', icon: 'shelf', row: 5, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Olivia',
				initial: 'O',
				color: 'blue',
				clues: [{ type: 'region', who: 's2', region: 0 }]
			},
			{
				id: 's3',
				name: 'Fabián',
				initial: 'F',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 0 }]
			},
			{
				id: 's4',
				name: 'Gabriela',
				initial: 'G',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 5 }]
			},
			{
				id: 's5',
				name: 'Bruno',
				initial: 'B',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's4' }]
			},
			{
				id: 's6',
				name: 'Nicolás',
				initial: 'N',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's7',
				name: 'Carla',
				initial: 'C',
				color: 'red',
				clues: [{ type: 'region', who: 's7', region: 1 }, { type: 'nearProp', who: 's7', prop: 'p6' }]
			},
			{
				id: 's8',
				name: 'Alicia',
				initial: 'A',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's5' }]
			}
		],
		victim: { name: 'Pilar', row: 2, col: 1 },
		solution: {
			s1: { row: 7, col: 4 },
			s2: { row: 6, col: 5 },
			s3: { row: 5, col: 6 },
			s4: { row: 8, col: 7 },
			s5: { row: 0, col: 8 },
			s6: { row: 3, col: 3 },
			s7: { row: 4, col: 2 },
			s8: { row: 1, col: 0 }
		},
		killer: 's8',
		meta: { seed: 20763483, clueCount: 9, negatives: 0, complexity: 0, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-038',
		game: 'murdoku',
		number: 38,
		title: 'Un freno de emergencia',
		setting: 'Un tren nocturno detenido',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[1, 1, 1, 1, 4, 4, 4, 4, 4],
				[1, 1, 1, 1, 5, 4, 4, 4, 4],
				[1, 1, 1, 1, 5, 4, 4, 4, 4],
				[1, 1, 1, 1, 5, 4, 4, 4, 4],
				[1, 1, 1, 5, 5, 4, 4, 4, 0],
				[3, 3, 1, 5, 5, 5, 2, 0, 0],
				[3, 3, 3, 5, 5, 5, 2, 0, 0],
				[3, 3, 3, 5, 5, 2, 2, 0, 0],
				[3, 3, 3, 5, 5, 2, 2, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 },
				{ id: 4, name: 'Cabina', tone: 4 },
				{ id: 5, name: 'Andén', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'planta', icon: 'plant', row: 3, col: 3 },
				{ id: 'p2', name: 'estatua', icon: 'statue', row: 1, col: 4 },
				{ id: 'p3', name: 'maleta', icon: 'chest', row: 4, col: 4 },
				{ id: 'p4', name: 'baúl', icon: 'chest', row: 8, col: 5 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 6, col: 8 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 4, col: 6 },
				{ id: 'p7', name: 'estantería', icon: 'shelf', row: 2, col: 4 },
				{ id: 'p8', name: 'cuadro', icon: 'painting', row: 5, col: 1 },
				{ id: 'p9', name: 'lámpara', icon: 'lamp', row: 2, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Hugo',
				initial: 'H',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's2' },
					{ type: 'direction', who: 's1', dir: 'W', steps: 1, than: 's2' }
				]
			},
			{
				id: 's2',
				name: 'Gabriela',
				initial: 'G',
				color: 'blue',
				clues: [
					{ type: 'region', who: 's2', region: 4 },
					{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's5' }
				]
			},
			{
				id: 's3',
				name: 'Bruno',
				initial: 'B',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's5' },
					{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's8' }
				]
			},
			{
				id: 's4',
				name: 'Diego',
				initial: 'D',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Marta',
				initial: 'M',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 0 }]
			},
			{
				id: 's6',
				name: 'Lorenzo',
				initial: 'L',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's3' },
					{ type: 'direction', who: 's6', dir: 'S', steps: 1, than: 's4' }
				]
			},
			{
				id: 's7',
				name: 'Julián',
				initial: 'J',
				color: 'red',
				clues: [
					{ type: 'region', who: 's7', region: 4 },
					{ type: 'direction', who: 's7', dir: 'N', steps: 1, than: 's2' }
				]
			},
			{
				id: 's8',
				name: 'Alicia',
				initial: 'A',
				color: 'green',
				clues: [{ type: 'region', who: 's8', region: 3 }]
			}
		],
		victim: { name: 'Sofía', row: 7, col: 3 },
		solution: {
			s1: { row: 2, col: 5 },
			s2: { row: 1, col: 6 },
			s3: { row: 6, col: 1 },
			s4: { row: 3, col: 4 },
			s5: { row: 5, col: 7 },
			s6: { row: 4, col: 0 },
			s7: { row: 0, col: 8 },
			s8: { row: 8, col: 2 }
		},
		killer: 's4',
		meta: { seed: 20876131, clueCount: 13, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-039',
		game: 'murdoku',
		number: 39,
		title: 'La escalera de caracol',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[5, 4, 4, 4, 4, 4, 4, 1, 1],
				[5, 5, 4, 4, 4, 4, 2, 2, 1],
				[5, 5, 5, 4, 4, 4, 2, 2, 1],
				[5, 5, 5, 4, 4, 4, 2, 2, 1],
				[5, 5, 5, 5, 3, 2, 2, 2, 1],
				[5, 5, 5, 5, 3, 0, 1, 1, 1],
				[5, 3, 3, 3, 3, 0, 0, 0, 0],
				[3, 3, 3, 3, 3, 0, 0, 0, 0],
				[3, 3, 3, 3, 3, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 },
				{ id: 4, name: 'Terraza', tone: 4 },
				{ id: 5, name: 'Muelle', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'candelabro', icon: 'lamp', row: 1, col: 4 },
				{ id: 'p2', name: 'busto', icon: 'statue', row: 1, col: 5 },
				{ id: 'p3', name: 'estantería', icon: 'shelf', row: 4, col: 1 },
				{ id: 'p4', name: 'lámpara', icon: 'lamp', row: 1, col: 6 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Marta',
				initial: 'M',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's4' }]
			},
			{
				id: 's2',
				name: 'Karina',
				initial: 'K',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's3' },
					{ type: 'direction', who: 's2', dir: 'N', steps: 3, than: 's5' }
				]
			},
			{
				id: 's3',
				name: 'Irene',
				initial: 'I',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's2' },
					{ type: 'colEdge', who: 's3', edge: 'left' }
				]
			},
			{
				id: 's4',
				name: 'Elena',
				initial: 'E',
				color: 'orange',
				clues: [
					{ type: 'region', who: 's4', region: 3 },
					{ type: 'direction', who: 's4', dir: 'E', steps: 1, than: 's5' }
				]
			},
			{
				id: 's5',
				name: 'Diego',
				initial: 'D',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's6',
				name: 'Nicolás',
				initial: 'N',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'N', steps: 1, than: 's2' },
					{ type: 'direction', who: 's6', dir: 'E', steps: 1, than: 's2' }
				]
			},
			{
				id: 's7',
				name: 'Lorenzo',
				initial: 'L',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's8',
				name: 'Bruno',
				initial: 'B',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'W', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Pilar', row: 1, col: 8 },
		solution: {
			s1: { row: 8, col: 6 },
			s2: { row: 3, col: 1 },
			s3: { row: 5, col: 0 },
			s4: { row: 7, col: 4 },
			s5: { row: 6, col: 3 },
			s6: { row: 2, col: 2 },
			s7: { row: 0, col: 7 },
			s8: { row: 4, col: 5 }
		},
		killer: 's7',
		meta: { seed: 20884050, clueCount: 12, negatives: 0, complexity: 2, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-040',
		game: 'murdoku',
		number: 40,
		title: 'El camerino vacío',
		setting: 'Un teatro después de la función',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[3, 3, 3, 3, 3, 3, 4, 4, 4],
				[0, 0, 0, 3, 3, 3, 4, 4, 4],
				[0, 0, 3, 3, 3, 3, 4, 4, 4],
				[3, 3, 3, 3, 3, 3, 3, 4, 4],
				[3, 3, 1, 1, 1, 3, 3, 4, 4],
				[2, 2, 1, 1, 1, 1, 2, 2, 4],
				[2, 2, 2, 2, 2, 1, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2],
				[2, 2, 2, 2, 2, 2, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 },
				{ id: 4, name: 'Vestíbulo', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 5, col: 3 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 1, col: 4 },
				{ id: 'p3', name: 'reloj', icon: 'clock', row: 3, col: 6 },
				{ id: 'p4', name: 'candelabro', icon: 'lamp', row: 4, col: 2 },
				{ id: 'p5', name: 'planta', icon: 'plant', row: 1, col: 1 },
				{ id: 'p6', name: 'estantería', icon: 'shelf', row: 7, col: 2 },
				{ id: 'p7', name: 'piano', icon: 'piano', row: 4, col: 8 },
				{ id: 'p8', name: 'retrato', icon: 'painting', row: 1, col: 8 },
				{ id: 'p9', name: 'cuadro', icon: 'painting', row: 2, col: 2 },
				{ id: 'p10', name: 'baúl', icon: 'chest', row: 6, col: 7 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [{ type: 'region', who: 's1', region: 4 }]
			},
			{
				id: 's2',
				name: 'Lorenzo',
				initial: 'L',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's2' },
					{ type: 'nearProp', who: 's3', prop: 'p6' }
				]
			},
			{
				id: 's4',
				name: 'Carla',
				initial: 'C',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'N', steps: 1, than: 's1' }]
			},
			{
				id: 's5',
				name: 'Nicolás',
				initial: 'N',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'W', steps: 1, than: 's1' },
					{ type: 'rowEdge', who: 's5', edge: 'bottom' }
				]
			},
			{
				id: 's6',
				name: 'Fabián',
				initial: 'F',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's4' }]
			},
			{
				id: 's7',
				name: 'Irene',
				initial: 'I',
				color: 'red',
				clues: [{ type: 'region', who: 's7', region: 2 }, { type: 'nearProp', who: 's7', prop: 'p6' }]
			},
			{
				id: 's8',
				name: 'Gabriela',
				initial: 'G',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's1' }]
			}
		],
		victim: { name: 'Teresa', row: 1, col: 3 },
		solution: {
			s1: { row: 3, col: 8 },
			s2: { row: 0, col: 0 },
			s3: { row: 7, col: 1 },
			s4: { row: 2, col: 6 },
			s5: { row: 8, col: 7 },
			s6: { row: 5, col: 5 },
			s7: { row: 6, col: 2 },
			s8: { row: 4, col: 4 }
		},
		killer: 's2',
		meta: { seed: 20891969, clueCount: 11, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-041',
		game: 'murdoku',
		number: 41,
		title: 'Un piano desafinado',
		setting: 'Una mansión a medianoche',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[0, 0, 0, 2, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 2, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 2, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 2, 3, 2],
				[0, 0, 0, 0, 0, 0, 2, 3, 2],
				[1, 1, 1, 0, 0, 0, 0, 3, 3],
				[1, 1, 1, 0, 3, 3, 3, 3, 3],
				[1, 1, 3, 3, 3, 3, 3, 3, 3],
				[1, 1, 3, 3, 3, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Estudio', tone: 0 },
				{ id: 1, name: 'Biblioteca', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Cocina', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 2, col: 6 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 6, col: 0 },
				{ id: 'p3', name: 'retrato', icon: 'painting', row: 7, col: 2 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 3, col: 8 },
				{ id: 'p5', name: 'reloj', icon: 'clock', row: 6, col: 1 },
				{ id: 'p6', name: 'candelabro', icon: 'lamp', row: 0, col: 8 },
				{ id: 'p7', name: 'baúl', icon: 'chest', row: 8, col: 0 },
				{ id: 'p8', name: 'lámpara', icon: 'lamp', row: 1, col: 3 },
				{ id: 'p9', name: 'piano', icon: 'piano', row: 4, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Fabián',
				initial: 'F',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 1, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Marta',
				initial: 'M',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 1, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Diego',
				initial: 'D',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's2' },
					{ type: 'direction', who: 's3', dir: 'E', steps: 1, than: 's5' }
				]
			},
			{
				id: 's4',
				name: 'Irene',
				initial: 'I',
				color: 'orange',
				clues: [
					{ type: 'region', who: 's4', region: 3 },
					{ type: 'adjacent', a: 's4', b: 's5', diagonal: true }
				]
			},
			{
				id: 's5',
				name: 'Alicia',
				initial: 'A',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 1, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Bruno',
				initial: 'B',
				color: 'purple',
				clues: [{ type: 'region', who: 's6', region: 2 }, { type: 'colEdge', who: 's6', edge: 'right' }]
			},
			{
				id: 's7',
				name: 'Carla',
				initial: 'C',
				color: 'red',
				clues: [{ type: 'region', who: 's7', region: 3 }]
			},
			{
				id: 's8',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's1' },
					{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's3' }
				]
			}
		],
		victim: { name: 'Tomás', row: 0, col: 2 },
		solution: {
			s1: { row: 5, col: 1 },
			s2: { row: 2, col: 0 },
			s3: { row: 3, col: 6 },
			s4: { row: 7, col: 4 },
			s5: { row: 6, col: 5 },
			s6: { row: 1, col: 8 },
			s7: { row: 8, col: 3 },
			s8: { row: 4, col: 7 }
		},
		killer: 's2',
		meta: { seed: 20899888, clueCount: 12, negatives: 0, complexity: 2, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-042',
		game: 'murdoku',
		number: 42,
		title: 'Última consulta',
		setting: 'Una biblioteca cerrada al público',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[2, 3, 3, 3, 3, 3, 0, 0, 0],
				[2, 3, 3, 3, 3, 3, 0, 0, 0],
				[4, 3, 3, 3, 3, 0, 0, 0, 0],
				[4, 4, 3, 3, 0, 0, 0, 0, 0],
				[4, 4, 3, 3, 0, 0, 0, 0, 0],
				[4, 4, 4, 0, 0, 0, 0, 0, 0],
				[4, 4, 1, 1, 0, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 0, 0, 0, 0],
				[1, 1, 1, 1, 1, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Galería', tone: 1 },
				{ id: 2, name: 'Sala de lectura', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 },
				{ id: 4, name: 'Patio', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 0, col: 7 },
				{ id: 'p2', name: 'reloj', icon: 'clock', row: 8, col: 1 },
				{ id: 'p3', name: 'atril', icon: 'shelf', row: 3, col: 6 },
				{ id: 'p4', name: 'cofre', icon: 'chest', row: 6, col: 1 },
				{ id: 'p5', name: 'busto', icon: 'statue', row: 5, col: 6 },
				{ id: 'p6', name: 'candelabro', icon: 'lamp', row: 8, col: 0 },
				{ id: 'p7', name: 'estantería', icon: 'shelf', row: 1, col: 4 },
				{ id: 'p8', name: 'estatua', icon: 'statue', row: 0, col: 2 },
				{ id: 'p9', name: 'lámpara', icon: 'lamp', row: 3, col: 3 },
				{ id: 'p10', name: 'planta', icon: 'plant', row: 7, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Diego',
				initial: 'D',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'W', steps: 1, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Fabián',
				initial: 'F',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 0 }, { type: 'nearProp', who: 's3', prop: 'p5' }]
			},
			{
				id: 's4',
				name: 'Karina',
				initial: 'K',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'E', steps: 1, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [{ type: 'region', who: 's5', region: 0 }, { type: 'colEdge', who: 's5', edge: 'right' }]
			},
			{
				id: 's6',
				name: 'Carla',
				initial: 'C',
				color: 'purple',
				clues: [
					{ type: 'direction', who: 's6', dir: 'N', steps: 1, than: 's2' },
					{ type: 'direction', who: 's6', dir: 'E', steps: 1, than: 's8' }
				]
			},
			{
				id: 's7',
				name: 'Gabriela',
				initial: 'G',
				color: 'red',
				clues: [
					{ type: 'direction', who: 's7', dir: 'W', steps: 1, than: 's2' },
					{ type: 'rowEdge', who: 's7', edge: 'top' }
				]
			},
			{
				id: 's8',
				name: 'Bruno',
				initial: 'B',
				color: 'green',
				clues: [{ type: 'region', who: 's8', region: 0 }]
			}
		],
		victim: { name: 'Pilar', row: 1, col: 5 },
		solution: {
			s1: { row: 7, col: 7 },
			s2: { row: 4, col: 1 },
			s3: { row: 6, col: 6 },
			s4: { row: 2, col: 2 },
			s5: { row: 8, col: 8 },
			s6: { row: 3, col: 4 },
			s7: { row: 0, col: 0 },
			s8: { row: 5, col: 3 }
		},
		killer: 's4',
		meta: { seed: 20803078, clueCount: 12, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-043',
		game: 'murdoku',
		number: 43,
		title: 'Flores de medianoche',
		setting: 'Un invernadero al amanecer',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[3, 3, 3, 3, 3, 1, 1, 1, 1],
				[2, 3, 3, 3, 3, 3, 1, 1, 1],
				[2, 2, 2, 3, 3, 3, 1, 1, 1],
				[2, 2, 2, 3, 3, 3, 1, 1, 1],
				[2, 3, 3, 3, 3, 3, 1, 1, 1],
				[3, 3, 3, 3, 3, 3, 1, 1, 1],
				[3, 3, 0, 3, 3, 3, 1, 1, 1],
				[3, 0, 0, 0, 0, 1, 1, 1, 1],
				[3, 3, 0, 0, 0, 0, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Invernadero', tone: 0 },
				{ id: 1, name: 'Orangerie', tone: 1 },
				{ id: 2, name: 'Fuente', tone: 2 },
				{ id: 3, name: 'Rosaleda', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'arcón', icon: 'chest', row: 1, col: 0 },
				{ id: 'p2', name: 'reloj', icon: 'clock', row: 1, col: 5 },
				{ id: 'p3', name: 'candelabro', icon: 'lamp', row: 2, col: 6 },
				{ id: 'p4', name: 'lámpara', icon: 'lamp', row: 8, col: 4 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 4, col: 8 },
				{ id: 'p6', name: 'estatua', icon: 'statue', row: 8, col: 8 },
				{ id: 'p7', name: 'cuadro', icon: 'painting', row: 4, col: 5 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Olivia',
				initial: 'O',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's3' },
					{ type: 'direction', who: 's1', dir: 'N', steps: 1, than: 's7' }
				]
			},
			{
				id: 's2',
				name: 'Gabriela',
				initial: 'G',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'E', steps: 1, than: 's3' },
					{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's5' }
				]
			},
			{
				id: 's3',
				name: 'Karina',
				initial: 'K',
				color: 'yellow',
				clues: [{ type: 'region', who: 's3', region: 1 }]
			},
			{
				id: 's4',
				name: 'Irene',
				initial: 'I',
				color: 'orange',
				clues: [{ type: 'region', who: 's4', region: 0 }]
			},
			{
				id: 's5',
				name: 'Bruno',
				initial: 'B',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's1' }]
			},
			{
				id: 's6',
				name: 'Hugo',
				initial: 'H',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's1' }]
			},
			{
				id: 's7',
				name: 'Lorenzo',
				initial: 'L',
				color: 'red',
				clues: [{ type: 'region', who: 's7', region: 1 }, { type: 'nearProp', who: 's7', prop: 'p3' }]
			},
			{
				id: 's8',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'S', steps: 1, than: 's4' }]
			}
		],
		victim: { name: 'Teresa', row: 4, col: 0 },
		solution: {
			s1: { row: 2, col: 2 },
			s2: { row: 6, col: 8 },
			s3: { row: 1, col: 7 },
			s4: { row: 7, col: 4 },
			s5: { row: 5, col: 3 },
			s6: { row: 0, col: 1 },
			s7: { row: 3, col: 6 },
			s8: { row: 8, col: 5 }
		},
		killer: 's1',
		meta: { seed: 20706268, clueCount: 11, negatives: 0, complexity: 1, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-044',
		game: 'murdoku',
		number: 44,
		title: 'La mesa sin postre',
		setting: 'Una cocina de servicio en plena cena',
		difficulty: 'medium',
		size: 9,
		estimatedMinutes: 10,
		grid: {
			size: 9,
			regions: [
				[2, 2, 0, 0, 0, 0, 0, 0, 0],
				[2, 2, 2, 2, 2, 0, 0, 0, 0],
				[2, 2, 2, 3, 3, 3, 0, 0, 0],
				[2, 2, 2, 2, 3, 3, 0, 0, 0],
				[2, 2, 2, 3, 3, 3, 0, 0, 0],
				[2, 3, 3, 3, 3, 3, 3, 0, 0],
				[1, 3, 3, 3, 3, 3, 3, 0, 0],
				[1, 1, 3, 3, 3, 3, 3, 0, 3],
				[1, 1, 1, 3, 3, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Cocina', tone: 0 },
				{ id: 1, name: 'Despensa', tone: 1 },
				{ id: 2, name: 'Comedor', tone: 2 },
				{ id: 3, name: 'Office', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'figura', icon: 'statue', row: 1, col: 4 },
				{ id: 'p2', name: 'bodegón', icon: 'painting', row: 1, col: 8 },
				{ id: 'p3', name: 'estantería', icon: 'shelf', row: 4, col: 4 },
				{ id: 'p4', name: 'planta aromática', icon: 'plant', row: 5, col: 2 },
				{ id: 'p5', name: 'piano', icon: 'piano', row: 1, col: 6 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 0, col: 0 },
				{ id: 'p7', name: 'candelabro', icon: 'lamp', row: 6, col: 2 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Carla',
				initial: 'C',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Karina',
				initial: 'K',
				color: 'blue',
				clues: [{ type: 'region', who: 's2', region: 3 }, { type: 'rowEdge', who: 's2', edge: 'bottom' }]
			},
			{
				id: 's3',
				name: 'Fabián',
				initial: 'F',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's1' },
					{ type: 'direction', who: 's3', dir: 'W', steps: 1, than: 's5' }
				]
			},
			{
				id: 's4',
				name: 'Gabriela',
				initial: 'G',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'W', steps: 1, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Bruno',
				initial: 'B',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'N', steps: 1, than: 's3' }]
			},
			{
				id: 's6',
				name: 'Julián',
				initial: 'J',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 1, than: 's3' }]
			},
			{
				id: 's7',
				name: 'Diego',
				initial: 'D',
				color: 'red',
				clues: [
					{ type: 'region', who: 's7', region: 3 },
					{ type: 'adjacent', a: 's2', b: 's7', diagonal: true }
				]
			},
			{
				id: 's8',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'E', steps: 1, than: 's1' },
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's6' }
				]
			}
		],
		victim: { name: 'Sofía', row: 1, col: 0 },
		solution: {
			s1: { row: 6, col: 1 },
			s2: { row: 8, col: 4 },
			s3: { row: 5, col: 7 },
			s4: { row: 0, col: 3 },
			s5: { row: 4, col: 8 },
			s6: { row: 3, col: 6 },
			s7: { row: 7, col: 5 },
			s8: { row: 2, col: 2 }
		},
		killer: 's8',
		meta: { seed: 20923645, clueCount: 12, negatives: 0, complexity: 2, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-045',
		game: 'murdoku',
		number: 45,
		title: 'Una sombra en el pasillo',
		setting: 'Un museo después del cierre',
		difficulty: 'hard',
		size: 9,
		estimatedMinutes: 12,
		grid: {
			size: 9,
			regions: [
				[0, 0, 0, 0, 0, 0, 4, 4, 4],
				[0, 0, 0, 0, 0, 4, 4, 4, 3],
				[0, 0, 0, 0, 0, 4, 4, 4, 3],
				[3, 3, 3, 3, 0, 3, 3, 3, 3],
				[3, 3, 3, 3, 3, 3, 3, 3, 3],
				[3, 2, 2, 2, 3, 3, 3, 3, 1],
				[2, 2, 2, 2, 3, 3, 1, 1, 1],
				[2, 2, 2, 2, 2, 3, 1, 1, 1],
				[2, 2, 2, 2, 2, 2, 1, 1, 1]
			],
			regionList: [
				{ id: 0, name: 'Vestíbulo', tone: 0 },
				{ id: 1, name: 'Sala egipcia', tone: 1 },
				{ id: 2, name: 'Sala griega', tone: 2 },
				{ id: 3, name: 'Depósito', tone: 3 },
				{ id: 4, name: 'Taller', tone: 4 }
			],
			props: [
				{ id: 'p1', name: 'estatua', icon: 'statue', row: 1, col: 2 },
				{ id: 'p2', name: 'busto', icon: 'statue', row: 8, col: 2 },
				{ id: 'p3', name: 'planta', icon: 'plant', row: 1, col: 4 },
				{ id: 'p4', name: 'reloj', icon: 'clock', row: 4, col: 6 },
				{ id: 'p5', name: 'estantería', icon: 'shelf', row: 8, col: 8 },
				{ id: 'p6', name: 'cuadro', icon: 'painting', row: 8, col: 0 },
				{ id: 'p7', name: 'vitrina', icon: 'shelf', row: 7, col: 1 },
				{ id: 'p8', name: 'cofre', icon: 'chest', row: 2, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Bruno',
				initial: 'B',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 2, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'N', steps: 3, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Elena',
				initial: 'E',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'E', steps: 4, than: 's2' }]
			},
			{
				id: 's4',
				name: 'Karina',
				initial: 'K',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 0 }]
			},
			{
				id: 's5',
				name: 'Carla',
				initial: 'C',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'N', steps: 2, than: 's3' },
					{ type: 'direction', who: 's5', dir: 'E', steps: 8, than: 's4' }
				]
			},
			{
				id: 's6',
				name: 'Lorenzo',
				initial: 'L',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'W', steps: 2, than: 's3' }]
			},
			{
				id: 's7',
				name: 'Marta',
				initial: 'M',
				color: 'red',
				clues: [{ type: 'notRegion', who: 's7', region: 0 }, { type: 'rowEdge', who: 's7', edge: 'top' }]
			},
			{
				id: 's8',
				name: 'Julián',
				initial: 'J',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'W', steps: 2, than: 's2' },
					{ type: 'nearProp', who: 's8', prop: 'p6' }
				]
			}
		],
		victim: { name: 'Pilar', row: 7, col: 2 },
		solution: {
			s1: { row: 4, col: 4 },
			s2: { row: 2, col: 3 },
			s3: { row: 3, col: 7 },
			s4: { row: 5, col: 0 },
			s5: { row: 1, col: 8 },
			s6: { row: 6, col: 5 },
			s7: { row: 0, col: 6 },
			s8: { row: 8, col: 1 }
		},
		killer: 's8',
		meta: { seed: 20722106, clueCount: 11, negatives: 2, complexity: 10, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-046',
		game: 'murdoku',
		number: 46,
		title: 'El último silbato',
		setting: 'Un tren nocturno detenido',
		difficulty: 'hard',
		size: 9,
		estimatedMinutes: 12,
		grid: {
			size: 9,
			regions: [
				[0, 0, 0, 0, 0, 0, 3, 3, 3],
				[0, 0, 0, 0, 0, 0, 3, 3, 3],
				[0, 0, 0, 0, 0, 0, 0, 3, 3],
				[1, 1, 1, 0, 0, 0, 3, 3, 3],
				[0, 0, 1, 0, 0, 0, 3, 3, 3],
				[0, 0, 0, 0, 0, 0, 3, 3, 3],
				[0, 0, 0, 0, 0, 2, 2, 2, 3],
				[0, 0, 0, 0, 0, 0, 2, 2, 2],
				[0, 0, 0, 0, 0, 0, 2, 2, 2]
			],
			regionList: [
				{ id: 0, name: 'Vagón restaurante', tone: 0 },
				{ id: 1, name: 'Vagón litera', tone: 1 },
				{ id: 2, name: 'Pasillo', tone: 2 },
				{ id: 3, name: 'Furgón', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'planta', icon: 'plant', row: 4, col: 1 },
				{ id: 'p2', name: 'lámpara', icon: 'lamp', row: 7, col: 2 },
				{ id: 'p3', name: 'piano', icon: 'piano', row: 8, col: 3 },
				{ id: 'p4', name: 'candelabro', icon: 'lamp', row: 6, col: 1 },
				{ id: 'p5', name: 'maleta', icon: 'chest', row: 0, col: 6 },
				{ id: 'p6', name: 'reloj', icon: 'clock', row: 3, col: 8 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 5, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Elena',
				initial: 'E',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'S', steps: 2, than: 's4' }]
			},
			{
				id: 's3',
				name: 'Julián',
				initial: 'J',
				color: 'yellow',
				clues: [
					{ type: 'direction', who: 's3', dir: 'W', steps: 2, than: 's4' },
					{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's7' }
				]
			},
			{
				id: 's4',
				name: 'Bruno',
				initial: 'B',
				color: 'orange',
				clues: [{ type: 'direction', who: 's4', dir: 'E', steps: 3, than: 's2' }]
			},
			{
				id: 's5',
				name: 'Olivia',
				initial: 'O',
				color: 'pink',
				clues: [{ type: 'direction', who: 's5', dir: 'S', steps: 6, than: 's4' }]
			},
			{
				id: 's6',
				name: 'Marta',
				initial: 'M',
				color: 'purple',
				clues: [{ type: 'notRegion', who: 's6', region: 0 }]
			},
			{
				id: 's7',
				name: 'Irene',
				initial: 'I',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'W', steps: 7, than: 's1' }]
			},
			{
				id: 's8',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'W', steps: 6, than: 's1' },
					{ type: 'direction', who: 's8', dir: 'N', steps: 1, than: 's4' }
				]
			}
		],
		victim: { name: 'Tomás', row: 3, col: 6 },
		solution: {
			s1: { row: 0, col: 7 },
			s2: { row: 4, col: 2 },
			s3: { row: 6, col: 3 },
			s4: { row: 2, col: 5 },
			s5: { row: 8, col: 4 },
			s6: { row: 7, col: 8 },
			s7: { row: 5, col: 0 },
			s8: { row: 1, col: 1 }
		},
		killer: 's1',
		meta: { seed: 20834754, clueCount: 10, negatives: 1, complexity: 8, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-047',
		game: 'murdoku',
		number: 47,
		title: 'Luces en la niebla',
		setting: 'Un faro aislado por la tormenta',
		difficulty: 'hard',
		size: 9,
		estimatedMinutes: 12,
		grid: {
			size: 9,
			regions: [
				[3, 3, 3, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 1, 1, 1, 1, 1, 1],
				[3, 3, 3, 2, 2, 1, 1, 1, 2],
				[3, 3, 3, 2, 2, 2, 2, 2, 2],
				[3, 3, 3, 3, 2, 2, 2, 2, 2],
				[3, 3, 3, 3, 3, 0, 2, 2, 2],
				[3, 3, 0, 3, 0, 0, 0, 0, 0],
				[3, 3, 0, 0, 0, 0, 0, 0, 0],
				[3, 3, 0, 0, 0, 0, 0, 0, 0]
			],
			regionList: [
				{ id: 0, name: 'Sala de máquinas', tone: 0 },
				{ id: 1, name: 'Escalera', tone: 1 },
				{ id: 2, name: 'Cocina', tone: 2 },
				{ id: 3, name: 'Dormitorio', tone: 3 }
			],
			props: [
				{ id: 'p1', name: 'piano', icon: 'piano', row: 0, col: 2 },
				{ id: 'p2', name: 'reloj', icon: 'clock', row: 2, col: 2 },
				{ id: 'p3', name: 'estantería', icon: 'shelf', row: 4, col: 0 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 0, col: 3 },
				{ id: 'p5', name: 'planta', icon: 'plant', row: 0, col: 4 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Karina',
				initial: 'K',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'E', steps: 2, than: 's3' }]
			},
			{
				id: 's2',
				name: 'Irene',
				initial: 'I',
				color: 'blue',
				clues: [
					{ type: 'direction', who: 's2', dir: 'E', steps: 4, than: 's1' },
					{ type: 'direction', who: 's2', dir: 'S', steps: 1, than: 's7' }
				]
			},
			{
				id: 's3',
				name: 'Carla',
				initial: 'C',
				color: 'yellow',
				clues: [{ type: 'notRegion', who: 's3', region: 1 }, { type: 'nearProp', who: 's3', prop: 'p2' }]
			},
			{
				id: 's4',
				name: 'Fabián',
				initial: 'F',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 2 }]
			},
			{
				id: 's5',
				name: 'Hugo',
				initial: 'H',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'N', steps: 3, than: 's2' },
					{ type: 'direction', who: 's5', dir: 'E', steps: 1, than: 's1' }
				]
			},
			{
				id: 's6',
				name: 'Nicolás',
				initial: 'N',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'E', steps: 8, than: 's4' }]
			},
			{
				id: 's7',
				name: 'Lorenzo',
				initial: 'L',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'E', steps: 5, than: 's3' }]
			},
			{
				id: 's8',
				name: 'Diego',
				initial: 'D',
				color: 'green',
				clues: [{ type: 'direction', who: 's8', dir: 'N', steps: 7, than: 's4' }]
			}
		],
		victim: { name: 'Óscar', row: 6, col: 2 },
		solution: {
			s1: { row: 8, col: 3 },
			s2: { row: 4, col: 7 },
			s3: { row: 2, col: 1 },
			s4: { row: 7, col: 0 },
			s5: { row: 1, col: 4 },
			s6: { row: 5, col: 8 },
			s7: { row: 3, col: 6 },
			s8: { row: 0, col: 5 }
		},
		killer: 's1',
		meta: { seed: 20842673, clueCount: 11, negatives: 2, complexity: 9, generatedBy: 'generator' }
	},
	{
		id: 'murdoku-048',
		game: 'murdoku',
		number: 48,
		title: 'Aplausos de medianoche',
		setting: 'Un teatro después de la función',
		difficulty: 'hard',
		size: 9,
		estimatedMinutes: 12,
		grid: {
			size: 9,
			regions: [
				[5, 5, 5, 5, 5, 5, 5, 0, 0],
				[5, 5, 5, 2, 2, 2, 2, 2, 0],
				[4, 4, 4, 2, 2, 2, 2, 0, 0],
				[4, 4, 4, 2, 2, 2, 0, 0, 0],
				[4, 4, 4, 4, 4, 3, 3, 3, 0],
				[4, 4, 4, 4, 3, 3, 3, 3, 3],
				[1, 1, 1, 1, 3, 3, 3, 3, 3],
				[1, 1, 1, 1, 3, 3, 3, 3, 3],
				[1, 1, 1, 1, 1, 3, 3, 3, 3]
			],
			regionList: [
				{ id: 0, name: 'Escenario', tone: 0 },
				{ id: 1, name: 'Platea', tone: 1 },
				{ id: 2, name: 'Palco', tone: 2 },
				{ id: 3, name: 'Camerinos', tone: 3 },
				{ id: 4, name: 'Vestíbulo', tone: 4 },
				{ id: 5, name: 'Tramoya', tone: 5 }
			],
			props: [
				{ id: 'p1', name: 'cuadro', icon: 'painting', row: 8, col: 1 },
				{ id: 'p2', name: 'estantería', icon: 'shelf', row: 4, col: 0 },
				{ id: 'p3', name: 'reloj', icon: 'clock', row: 3, col: 3 },
				{ id: 'p4', name: 'estatua', icon: 'statue', row: 0, col: 7 },
				{ id: 'p5', name: 'retrato', icon: 'painting', row: 3, col: 4 },
				{ id: 'p6', name: 'piano', icon: 'piano', row: 6, col: 3 },
				{ id: 'p7', name: 'planta', icon: 'plant', row: 0, col: 1 },
				{ id: 'p8', name: 'lámpara', icon: 'lamp', row: 1, col: 1 },
				{ id: 'p9', name: 'baúl', icon: 'chest', row: 5, col: 1 }
			]
		},
		suspects: [
			{
				id: 's1',
				name: 'Nicolás',
				initial: 'N',
				color: 'green',
				clues: [{ type: 'direction', who: 's1', dir: 'S', steps: 5, than: 's2' }]
			},
			{
				id: 's2',
				name: 'Lorenzo',
				initial: 'L',
				color: 'blue',
				clues: [{ type: 'direction', who: 's2', dir: 'E', steps: 2, than: 's3' }]
			},
			{
				id: 's3',
				name: 'Julián',
				initial: 'J',
				color: 'yellow',
				clues: [{ type: 'direction', who: 's3', dir: 'S', steps: 5, than: 's4' }]
			},
			{
				id: 's4',
				name: 'Marta',
				initial: 'M',
				color: 'orange',
				clues: [{ type: 'notRegion', who: 's4', region: 3 }]
			},
			{
				id: 's5',
				name: 'Diego',
				initial: 'D',
				color: 'pink',
				clues: [
					{ type: 'direction', who: 's5', dir: 'N', steps: 6, than: 's1' },
					{ type: 'direction', who: 's5', dir: 'W', steps: 1, than: 's1' }
				]
			},
			{
				id: 's6',
				name: 'Irene',
				initial: 'I',
				color: 'purple',
				clues: [{ type: 'direction', who: 's6', dir: 'N', steps: 4, than: 's1' }]
			},
			{
				id: 's7',
				name: 'Bruno',
				initial: 'B',
				color: 'red',
				clues: [{ type: 'direction', who: 's7', dir: 'W', steps: 7, than: 's1' }]
			},
			{
				id: 's8',
				name: 'Elena',
				initial: 'E',
				color: 'green',
				clues: [
					{ type: 'direction', who: 's8', dir: 'S', steps: 3, than: 's2' },
					{ type: 'direction', who: 's8', dir: 'E', steps: 1, than: 's1' }
				]
			}
		],
		victim: { name: 'Ramiro', row: 5, col: 3 },
		solution: {
			s1: { row: 6, col: 7 },
			s2: { row: 1, col: 4 },
			s3: { row: 8, col: 2 },
			s4: { row: 3, col: 1 },
			s5: { row: 0, col: 6 },
			s6: { row: 2, col: 5 },
			s7: { row: 7, col: 0 },
			s8: { row: 4, col: 8 }
		},
		killer: 's4',
		meta: { seed: 22212069, clueCount: 10, negatives: 1, complexity: 8, generatedBy: 'generator' }
	}
];
