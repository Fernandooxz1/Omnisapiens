<script lang="ts">
	import { t } from '#lib/i18n';
</script>

<header>
	<h1>{t('app.title')}</h1>
	<p>{t('home.tagline')}</p>
</header>

<nav aria-label={t('app.title')}>
	<a class="link-tile" href="/play">
		<strong>{t('home.play_online')}</strong>
		<span>{t('home.play_online_hint')}</span>
	</a>
	<a class="link-tile" href="/arcade">
		<strong>{t('home.play_arcade')}</strong>
		<span>{t('home.play_arcade_hint')}</span>
	</a>
</nav>

<style>
	header {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding-top: var(--s-7);
	}

	h1 {
		font-size: clamp(2.5rem, 12vw, 3.5rem);
	}

	header p {
		color: var(--ink-2);
		font-size: 1.125rem;
	}

	nav {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
	}
</style>
