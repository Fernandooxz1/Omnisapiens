import type { CasePreview } from '../types';

/**
 * Previews mínimos para dibujar sobres y probar los extremos de tamaño.
 * No son casos jugables: los casos reales llegan con el generador.
 */

/** Regiones rectangulares contiguas: alcanzan para el catálogo de muestra. */
function blockRegions(size: number, columns: number, rows: number): number[][] {
	const regions: number[][] = [];

	for (let row = 0; row < size; row += 1) {
		const band = Math.floor((row * rows) / size);
		const line: number[] = [];

		for (let col = 0; col < size; col += 1) {
			line.push(band * columns + Math.floor((col * columns) / size));
		}

		regions.push(line);
	}

	return regions;
}

export const fixturePreviews: CasePreview[] = [
	{
		meta: {
			id: 'murdoku-001',
			game: 'murdoku',
			number: 1,
			title: 'El estudio',
			setting: 'Una mansión a medianoche',
			difficulty: 'very_easy',
			size: 5,
			estimatedMinutes: 3,
			tutorial: true
		},
		regions: blockRegions(5, 2, 2),
		victim: { row: 2, col: 2 }
	},
	{
		meta: {
			id: 'murdoku-021',
			game: 'murdoku',
			number: 21,
			title: 'La biblioteca',
			setting: 'Una biblioteca cerrada al público',
			difficulty: 'medium',
			size: 9,
			estimatedMinutes: 10
		},
		regions: blockRegions(9, 2, 3),
		victim: { row: 4, col: 4 }
	},
	{
		meta: {
			id: 'murdoku-061',
			game: 'murdoku',
			number: 61,
			title: 'El faro',
			setting: 'Un faro aislado por la tormenta',
			difficulty: 'hardcore',
			size: 15,
			estimatedMinutes: 32
		},
		regions: blockRegions(15, 3, 2),
		victim: { row: 7, col: 7 }
	}
];
