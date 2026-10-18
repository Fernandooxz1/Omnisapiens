interface AnswerKeys {
	/** Solo se escucha mientras el turno espera una respuesta. */
	enabled: () => boolean;
	/** Cuántas opciones tiene la pregunta actual. */
	count: () => number;
	select: (index: number) => void;
	confirm: () => void;
}

const FORM = 'input, textarea, select, [contenteditable="true"]';

/**
 * `1`–`4` elige y `Enter` confirma. Se ignora lo que ya consumió otro control
 * (inputs del lobby, botones con foco) y los atajos con modificadores.
 */
export function bindAnswerKeys(keys: AnswerKeys): void {
	$effect(() => {
		function onKeydown(event: KeyboardEvent) {
			if (event.defaultPrevented || event.repeat) return;
			if (event.metaKey || event.ctrlKey || event.altKey) return;

			const target = event.target;
			if (target instanceof HTMLElement && target.closest(FORM)) return;

			if (event.key >= '1' && event.key <= '4') {
				if (!keys.enabled()) return;

				const index = Number(event.key) - 1;
				if (index >= keys.count()) return;

				event.preventDefault();
				keys.select(index);
				return;
			}

			if (event.key === 'Enter') {
				if (!keys.enabled()) return;

				event.preventDefault();
				keys.confirm();
			}
		}

		window.addEventListener('keydown', onKeydown);
		return () => window.removeEventListener('keydown', onKeydown);
	});
}
