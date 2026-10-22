<script lang="ts">
	import { page } from '$app/state';
	import Icon from '#lib/components/Icon.svelte';
	import { t, type MessageKey } from '#lib/i18n';

	interface Tab {
		href: string;
		icon: 'home' | 'grid' | 'trophy';
		label: MessageKey;
	}

	const TABS: Tab[] = [
		{ href: '/', icon: 'home', label: 'nav.home' },
		{ href: '/juegos', icon: 'grid', label: 'nav.games' },
		{ href: '/ranking', icon: 'trophy', label: 'nav.ranking' }
	];

	const path = $derived(page.url.pathname.replace(/\/+$/, '') || '/');

	function isActive(href: string): boolean {
		if (href === '/') return path === '/';
		return path === href || path.startsWith(`${href}/`);
	}
</script>

<nav class="tabbar" aria-label={t('nav.label')}>
	<div class="tabbar__inner">
		{#each TABS as tab (tab.href)}
			<a
				class="tabbar__tab"
				class:is-active={isActive(tab.href)}
				href={tab.href}
				aria-current={isActive(tab.href) ? 'page' : undefined}
			>
				<span class="tabbar__icon"><Icon name={tab.icon} size={22} /></span>
				<span class="tabbar__label">{t(tab.label)}</span>
			</a>
		{/each}
	</div>
</nav>

<style>
	.tabbar {
		position: fixed;
		inset-inline: 0;
		bottom: 0;
		z-index: 20;
		display: flex;
		justify-content: center;
		border-top: var(--border-w) solid var(--panel-edge);
		background: var(--card-edge);
		padding-bottom: env(safe-area-inset-bottom);
	}

	.tabbar__inner {
		display: flex;
		width: 100%;
		max-width: var(--shell-max);
	}

	.tabbar__tab {
		position: relative;
		display: flex;
		flex: 1 1 0;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1px;
		min-height: var(--tabbar-h);
		padding: var(--s-1) var(--s-2);
		color: var(--ink-3);
		font-family: var(--font-ui);
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.02em;
		text-decoration: none;
		-webkit-tap-highlight-color: transparent;
	}

	.tabbar__tab:hover {
		color: var(--ink-2);
	}

	.tabbar__tab.is-active {
		color: var(--accent);
	}

	/* Barra corta: marca el destino sin subrayar todo el ancho del blanco táctil. */
	.tabbar__tab.is-active::after {
		content: '';
		position: absolute;
		bottom: 0;
		width: 32px;
		height: 3px;
		border-radius: 3px 3px 0 0;
		background: var(--accent);
	}

	.tabbar__icon {
		display: inline-flex;
	}

	.tabbar__label {
		line-height: 1.2;
	}
</style>
