import assert from 'node:assert/strict';
import test from 'node:test';
import { allCases, byDifficulty, findCase } from './cases/index.ts';

test('el catálogo estándar trae 48 casos ordenados y sin duplicados', () => {
	assert.equal(allCases.length, 48);

	const ids = new Set<string>();
	const titles = new Set<string>();

	allCases.forEach((entry, index) => {
		assert.equal(entry.number, index + 1);
		assert.equal(entry.id, `murdoku-${String(index + 1).padStart(3, '0')}`);
		assert.ok(!ids.has(entry.id), `id duplicado: ${entry.id}`);
		assert.ok(!titles.has(entry.title), `título duplicado: ${entry.title}`);
		ids.add(entry.id);
		titles.add(entry.title);
	});
});

test('el catálogo respeta la matriz de 5×5 a 9×9', () => {
	const expected = [
		[5, 'very_easy', 6],
		[6, 'easy', 8],
		[7, 'easy', 6],
		[7, 'medium', 6],
		[8, 'medium', 8],
		[9, 'medium', 10],
		[9, 'hard', 4]
	] as const;

	for (const [size, difficulty, count] of expected) {
		const matching = allCases.filter(
			(entry) => entry.size === size && entry.difficulty === difficulty
		);
		assert.equal(matching.length, count, `${size}×${size} ${difficulty}`);
	}
});

test('findCase y byDifficulty resuelven sobre el catálogo', () => {
	assert.equal(findCase('murdoku-001'), allCases[0]);
	assert.equal(findCase('murdoku-999'), undefined);
	assert.equal(byDifficulty('hard').length, 4);
	assert.equal(byDifficulty('all').length, 48);
});
