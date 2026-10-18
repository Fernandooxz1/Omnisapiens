/** Los sonidos del juego; los archivos viven en `static/assets/sfx/`. */
export const SOUNDS = [
	'tick',
	'reveal',
	'correct',
	'wrong',
	'match_start',
	'match_win',
	'match_lose',
	'best_score'
] as const;

export type SoundName = (typeof SOUNDS)[number];

/** El bootstrap de `app.html` no lo lee: el silencio solo importa cuando suena algo. */
const STORAGE_KEY = 'omni-sound';

/** WAV mudo de 10 ms: el gesto que lo reproduce es el que habilita el audio en iOS. */
const SILENCE =
	'data:audio/wav;base64,UklGRnQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVAAAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA==';

function readMuted(): boolean {
	if (typeof localStorage === 'undefined') return false;
	try {
		return localStorage.getItem(STORAGE_KEY) === 'off';
	} catch {
		return false;
	}
}

let muted = $state(readMuted());
let unlocked = false;
const players = new Map<SoundName, HTMLAudioElement>();

function player(name: SoundName): HTMLAudioElement {
	let audio = players.get(name);
	if (!audio) {
		audio = new Audio(`/assets/sfx/${name}.mp3`);
		audio.preload = 'auto';
		audio.volume = 0.55;
		players.set(name, audio);
	}
	return audio;
}

/** iOS solo deja sonar después de un gesto: el primer toque o tecla abre el canal. */
function unlock(): void {
	if (unlocked) return;
	unlocked = true;

	for (const name of SOUNDS) player(name);

	const primer = new Audio(SILENCE);
	primer.volume = 0;
	void primer
		.play()
		.then(() => {
			primer.pause();
		})
		.catch(() => {
			// Otro gesto lo vuelve a intentar.
			unlocked = false;
		});
}

function toggle(): void {
	muted = !muted;

	try {
		localStorage.setItem(STORAGE_KEY, muted ? 'off' : 'on');
	} catch {
		/* sin persistencia: el silencio igual vale para esta pestaña */
	}

	if (!muted) {
		unlock();
		play('tick');
	}
}

function play(name: SoundName): void {
	if (muted) return;

	const audio = player(name);
	try {
		audio.currentTime = 0;
	} catch {
		/* todavía no hay metadatos: el navegador arranca desde el principio igual */
	}
	void audio.play().catch(() => {
		/* el navegador todavía no habilitó el audio: se reintenta en el próximo sonido */
	});
}

export const sound = {
	get muted() {
		return muted;
	},
	toggle,
	play
};

/** Se engancha al primer gesto de la ventana; después, `play` ya puede sonar. */
export function unlockSound(): void {
	unlock();
}
