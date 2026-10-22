<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		/** Cuántas piezas caen. */
		count?: number;
		/** Milisegundos que dura la lluvia completa. */
		duration?: number;
		/** Se avisa al terminar para que la pantalla desmonte el canvas. */
		onDone?: () => void;
	}

	let { count = 90, duration = 2800, onDone }: Props = $props();

	let canvas = $state<HTMLCanvasElement | null>(null);

	/** La paleta vive acá porque el canvas no lee variables CSS. */
	const COLORS = ['#1ec765', '#0098e6', '#ffc800', '#ff7800', '#ec388b', '#9338c6'];

	onMount(() => {
		const element = canvas;
		if (!element) return;

		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
			onDone?.();
			return;
		}

		const context = element.getContext('2d');
		if (!context) return;

		const node: HTMLCanvasElement = element;
		const ctx: CanvasRenderingContext2D = context;

		let width = 0;
		let height = 0;
		const ratio = Math.min(window.devicePixelRatio || 1, 2);

		function resize() {
			width = node.clientWidth;
			height = node.clientHeight;
			node.width = Math.round(width * ratio);
			node.height = Math.round(height * ratio);
			ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
		}

		resize();
		window.addEventListener('resize', resize);

		const pieces = Array.from({ length: count }, () => ({
			x: Math.random() * width,
			// Escalonadas fuera de pantalla: entran en cascada, no todas de golpe.
			y: -20 - Math.random() * height * 0.8,
			vx: (Math.random() - 0.5) * 90,
			vy: 60 + Math.random() * 150,
			w: 5 + Math.random() * 5,
			h: 8 + Math.random() * 7,
			spin: Math.random() * Math.PI,
			spinSpeed: (Math.random() - 0.5) * 9,
			color: COLORS[Math.floor(Math.random() * COLORS.length)],
			round: Math.random() < 0.3
		}));

		const start = performance.now();
		let previous = start;
		let frame = requestAnimationFrame(step);

		function step(time: number) {
			const dt = Math.min(32, time - previous) / 1000;
			previous = time;
			const age = time - start;
			const alpha = Math.max(0, Math.min(1, (duration - age) / 600));

			ctx.clearRect(0, 0, width, height);
			ctx.globalAlpha = alpha;

			for (const piece of pieces) {
				piece.vy += 900 * dt;
				piece.vx *= 1 - 0.6 * dt;
				piece.x += piece.vx * dt;
				piece.y += piece.vy * dt;
				piece.spin += piece.spinSpeed * dt;

				if (piece.y - piece.h > height) continue;

				ctx.save();
				ctx.translate(piece.x, piece.y);
				ctx.rotate(piece.spin);
				ctx.fillStyle = piece.color;
				if (piece.round) {
					ctx.beginPath();
					ctx.arc(0, 0, piece.w / 2, 0, Math.PI * 2);
					ctx.fill();
				} else {
					ctx.fillRect(-piece.w / 2, -piece.h / 2, piece.w, piece.h);
				}
				ctx.restore();
			}

			if (age < duration) {
				frame = requestAnimationFrame(step);
			} else {
				ctx.clearRect(0, 0, width, height);
				onDone?.();
			}
		}

		return () => {
			cancelAnimationFrame(frame);
			window.removeEventListener('resize', resize);
		};
	});
</script>

<canvas class="confetti" bind:this={canvas} aria-hidden="true"></canvas>

<style>
	.confetti {
		position: fixed;
		inset: 0;
		z-index: 45;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
</style>
