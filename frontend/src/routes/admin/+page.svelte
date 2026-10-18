<script lang="ts">
	import { onMount } from 'svelte';
	import {
		importQuestions,
		listQuestions,
		readAdminToken,
		writeAdminToken
	} from '#lib/api/admin';
	import { ApiError, NETWORK_ERROR } from '#lib/api/client';
	import type {
		AdminQuestionPage,
		ImportReport,
		QuestionStatus
	} from '#lib/api/types';
	import Button from '#lib/components/Button.svelte';
	import CategoryBadge from '#lib/components/CategoryBadge.svelte';
	import { CATEGORIES, categoryKey, type Category } from '#lib/categories';
	import { t, type MessageKey } from '#lib/i18n';
	import { toast } from '#lib/toast.svelte';

	const PAGE_SIZE = 20;
	const STATUSES: QuestionStatus[] = ['draft', 'published', 'archived'];
	const DIFFICULTIES = [1, 2, 3, 4, 5] as const;

	let adminToken = $state('');
	let tokenInput = $state('');
	let checking = $state(false);
	let tokenError = $state<MessageKey | null>(null);
	let unlocked = $state(false);

	let status = $state<QuestionStatus | ''>('');
	let category = $state<Category | ''>('');
	let difficulty = $state<number | ''>('');
	let query = $state('');
	let appliedQuery = $state('');
	let page = $state(1);

	let result = $state<AdminQuestionPage | null>(null);
	let loading = $state(false);
	let failure = $state<MessageKey | null>(null);
	let request = 0;

	let file = $state<File | null>(null);
	let fileInput = $state<HTMLInputElement | undefined>();
	let importStatus = $state<QuestionStatus>('draft');
	let importing = $state(false);
	let report = $state<ImportReport | null>(null);
	let importFailure = $state<MessageKey | null>(null);
	let importReason = $state<string | null>(null);

	const hasFilters = $derived(
		status !== '' || category !== '' || difficulty !== '' || appliedQuery !== ''
	);

	onMount(() => {
		const saved = readAdminToken();
		if (!saved) return;

		adminToken = saved;
		tokenInput = saved;
		void unlock();
	});

	async function unlock() {
		const value = tokenInput.trim();
		if (!value || checking) return;

		const current = ++request;
		checking = true;
		tokenError = null;
		failure = null;

		try {
			const first = await listQuestions(value, filtersFor(1));
			if (current !== request) return;

			adminToken = value;
			writeAdminToken(value);
			unlocked = true;
			tokenInput = '';
			page = 1;
			result = first;
		} catch (error) {
			if (current !== request) return;

			const key = errorKey(error);
			tokenError = key;
			failure = null;
			result = null;
			unlocked = false;
			if (key !== 'admin.error_token') toast.failure(error, t(key));

			if (error instanceof ApiError && error.code === 'ADMIN_REQUIRED') {
				adminToken = '';
				writeAdminToken(null);
				tokenInput = '';
			}
		} finally {
			if (current === request) checking = false;
		}
	}

	async function load() {
		if (!adminToken) return;

		const current = ++request;
		loading = true;
		failure = null;

		try {
			const next = await listQuestions(adminToken, filtersFor());
			if (current !== request) return;

			if (page > 1 && next.items.length === 0 && next.total > 0) {
				page = Math.max(1, next.pages);
				void load();
				return;
			}

			result = next;
		} catch (error) {
			if (current !== request) return;

			if (error instanceof ApiError && error.code === 'ADMIN_REQUIRED') {
				changeToken();
				tokenError = 'admin.error_token';
				return;
			}

			const key = errorKey(error);
			failure = key;
			toast.failure(error, t(key));
		} finally {
			if (current === request) loading = false;
		}
	}

	function filtersFor(target = page) {
		return {
			status: status || undefined,
			category: category || undefined,
			difficulty: difficulty === '' ? undefined : difficulty,
			q: appliedQuery || undefined,
			page: target,
			page_size: PAGE_SIZE
		};
	}

	function refresh() {
		page = 1;
		void load();
	}

	function submitToken(event: SubmitEvent) {
		event.preventDefault();
		void unlock();
	}

	function submitSearch(event: SubmitEvent) {
		event.preventDefault();
		appliedQuery = query.trim();
		refresh();
	}

	function setStatus(event: Event) {
		status = (event.currentTarget as HTMLSelectElement).value as QuestionStatus | '';
		refresh();
	}

	function setCategory(event: Event) {
		category = (event.currentTarget as HTMLSelectElement).value as Category | '';
		refresh();
	}

	function setDifficulty(event: Event) {
		const value = (event.currentTarget as HTMLSelectElement).value;
		difficulty = value === '' ? '' : Number(value);
		refresh();
	}

	function clearFilters() {
		status = '';
		category = '';
		difficulty = '';
		query = '';
		appliedQuery = '';
		refresh();
	}

	function go(target: number) {
		if (!result || target < 1 || target > result.pages) return;
		page = target;
		void load();
	}

	function changeToken() {
		adminToken = '';
		writeAdminToken(null);
		unlocked = false;
		result = null;
		failure = null;
		tokenError = null;
		tokenInput = '';
		page = 1;
	}

	function pickFile(event: Event) {
		file = (event.currentTarget as HTMLInputElement).files?.[0] ?? null;
		report = null;
		importFailure = null;
		importReason = null;
	}

	async function upload() {
		if (!file || !adminToken || importing) return;

		importing = true;
		report = null;
		importFailure = null;
		importReason = null;

		try {
			report = await importQuestions(adminToken, file, importStatus);
			file = null;
			if (fileInput) fileInput.value = '';
			page = 1;
			await load();
		} catch (error) {
			if (error instanceof ApiError && error.code === 'ADMIN_REQUIRED') {
				changeToken();
				tokenError = 'admin.error_token';
			} else if (error instanceof ApiError && error.code === 'IMPORT_FORMAT') {
				importReason = error.message;
			} else {
				const key = errorKey(error);
				importFailure = key;
				toast.failure(error, t(key));
			}
		} finally {
			importing = false;
		}
	}

	function errorKey(error: unknown): MessageKey {
		if (!(error instanceof ApiError)) return 'admin.error_generic';

		switch (error.code) {
			case NETWORK_ERROR:
				return 'admin.error_offline';
			case 'ADMIN_REQUIRED':
				return 'admin.error_token';
			default:
				return 'admin.error_generic';
		}
	}

	function statusLabel(value: QuestionStatus): string {
		switch (value) {
			case 'draft':
				return t('admin.status_draft');
			case 'published':
				return t('admin.status_published');
			case 'archived':
				return t('admin.status_archived');
		}
	}
</script>

<section class="admin">
	<header class="admin__intro">
		<h1 class="page-title">{t('admin.title')}</h1>
		<p class="muted">{t('admin.subtitle')}</p>
	</header>

	{#if !unlocked}
		<form class="admin__card" onsubmit={submitToken}>
			<div class="field">
				<label class="field__label" for="admin-token">{t('admin.token_label')}</label>
				<span class="field__well" class:field__well--bad={!!tokenError}>
					<input
						id="admin-token"
						class="field__input token-input"
						type="password"
						autocomplete="off"
						spellcheck="false"
						bind:value={tokenInput}
					/>
				</span>
				<span class="field__hint">{t('admin.token_hint')}</span>
			</div>

			{#if tokenError}
				<p class="admin__error" role="alert">{t(tokenError)}</p>
			{/if}

			<Button
				variant="green"
				title={checking ? t('admin.checking') : t('admin.enter')}
				disabled={checking || !tokenInput.trim()}
				onclick={() => unlock()}
			/>
		</form>
	{:else}
		<div class="admin__bar">
			<span class="admin__session">{t('admin.unlocked')}</span>
			<button type="button" class="mini mini--ghost" onclick={changeToken}>
				{t('admin.change_token')}
			</button>
		</div>

		<form class="admin__card" onsubmit={submitSearch}>
			<h2 class="admin__title">{t('admin.filters')}</h2>

			<div class="filters">
				<label class="filters__cell">
					<span class="field__label">{t('admin.status')}</span>
					<select class="select" value={status} onchange={setStatus}>
						<option value="">{t('admin.all_statuses')}</option>
						{#each STATUSES as value (value)}
							<option {value}>{statusLabel(value)}</option>
						{/each}
					</select>
				</label>

				<label class="filters__cell">
					<span class="field__label">{t('admin.category')}</span>
					<select class="select" value={category} onchange={setCategory}>
						<option value="">{t('admin.all_categories')}</option>
						{#each CATEGORIES as value (value)}
							<option {value}>{t(categoryKey(value))}</option>
						{/each}
					</select>
				</label>

				<label class="filters__cell">
					<span class="field__label">{t('admin.difficulty')}</span>
					<select class="select" value={difficulty} onchange={setDifficulty}>
						<option value="">{t('admin.all_difficulties')}</option>
						{#each DIFFICULTIES as value (value)}
							<option {value}>{value}</option>
						{/each}
					</select>
				</label>

				<div class="filters__cell filters__search">
					<label class="field__label" for="admin-search">{t('admin.search_label')}</label>
					<span class="filters__row">
						<span class="field__well">
							<input
								id="admin-search"
								class="field__input filters__input"
								bind:value={query}
								autocomplete="off"
							/>
						</span>
						<button class="mini" type="submit">{t('admin.search')}</button>
					</span>
				</div>
			</div>

			{#if hasFilters}
				<button type="button" class="mini mini--ghost" onclick={clearFilters}>
					{t('admin.clear')}
				</button>
			{/if}
		</form>

		{#if loading}
			<p class="admin__state">{t('admin.loading')}</p>
		{:else if failure}
			<div class="admin__state">
				<p>{t(failure)}</p>
				<Button variant="slate" title={t('admin.retry')} onclick={() => load()} />
			</div>
		{:else if result}
			<div class="admin__summary">
				<span>{t('admin.total', { n: result.total })}</span>
				{#if result.pages > 1}
					<span>{t('admin.page', { page: result.page, pages: result.pages })}</span>
				{/if}
			</div>

			{#if result.items.length === 0}
				<p class="admin__state">{t('admin.empty')}</p>
			{:else}
				<ol class="questions">
					{#each result.items as item (item.id)}
						<li class="q">
							<header class="q__head">
								<CategoryBadge
									category={item.category}
									label={t(categoryKey(item.category))}
								/>
								<span class="q__status" data-status={item.status}>
									{statusLabel(item.status)}
								</span>
							</header>

							<p class="q__prompt">{item.prompt}</p>

							<ul class="q__options">
								{#each item.options as option, index (index)}
									<li class="q__option" class:is-correct={index === item.correct_index}>
										<span class="q__key">{String.fromCharCode(65 + index)}</span>
										<span>{option}</span>
										{#if index === item.correct_index}
											<span class="q__check">{t('admin.correct')}</span>
										{/if}
									</li>
								{/each}
							</ul>

							{#if item.explanation}
								<p class="q__note">
									<strong>{t('admin.explanation')}:</strong>
									{item.explanation}
								</p>
							{/if}

							<footer class="q__meta">
								<span>{t('admin.difficulty_value', { n: item.difficulty })}</span>
								{#if item.source}
									<span>{t('admin.source')}: {item.source}</span>
								{/if}
								{#if item.tags.length > 0}
									<span>{item.tags.join(' · ')}</span>
								{/if}
								{#if item.media_url}
									<a
										class="q__media"
										href={item.media_url}
										target="_blank"
										rel="noreferrer"
									>
										{t('admin.media')}
									</a>
								{/if}
							</footer>
						</li>
					{/each}
				</ol>

				{#if result.pages > 1}
					{@const currentPage = result.page}
					{@const totalPages = result.pages}
					<div class="pager">
						<button
							type="button"
							class="mini"
							disabled={currentPage <= 1 || loading}
							onclick={() => go(currentPage - 1)}
						>
							{t('admin.prev')}
						</button>
						<span class="pager__state">
							{t('admin.page', { page: currentPage, pages: totalPages })}
						</span>
						<button
							type="button"
							class="mini"
							disabled={currentPage >= totalPages || loading}
							onclick={() => go(currentPage + 1)}
						>
							{t('admin.next')}
						</button>
					</div>
				{/if}
			{/if}
		{/if}

		<section class="admin__card">
			<h2 class="admin__title">{t('admin.import_title')}</h2>
			<p class="muted">{t('admin.import_hint')}</p>

			<a class="template" href="/plantilla-preguntas.csv" download>
				{t('admin.import_template')}
			</a>

			<label class="field">
				<span class="field__label">{t('admin.import_file')}</span>
				<input
					class="file"
					type="file"
					accept=".csv,.json,text/csv,application/json"
					bind:this={fileInput}
					onchange={pickFile}
				/>
				{#if file}
					<span class="field__hint">{file.name}</span>
				{/if}
			</label>

			<fieldset class="status-choice">
				<legend class="field__label">{t('admin.import_status')}</legend>
				<div class="segmented" role="group" aria-label={t('admin.import_status')}>
					{#each STATUSES as value (value)}
						<button
							type="button"
							class="segment"
							class:is-on={importStatus === value}
							aria-pressed={importStatus === value}
							onclick={() => (importStatus = value)}
						>
							{statusLabel(value)}
						</button>
					{/each}
				</div>
			</fieldset>

			<p class="muted">{t('admin.import_publish_hint')}</p>

			<Button
				variant="blue"
				title={importing ? t('admin.importing') : t('admin.import')}
				disabled={!file || importing}
				onclick={() => upload()}
			/>

			{#if importReason}
				<p class="admin__error" role="alert">{importReason}</p>
			{:else if importFailure}
				<p class="admin__error" role="alert">{t(importFailure)}</p>
			{/if}

			{#if report}
				<div class="report" aria-live="polite">
					<h3 class="report__title">{t('admin.import_report')}</h3>
					<dl class="report__stats">
						<div>
							<dt>{t('admin.import_total')}</dt>
							<dd>{report.total}</dd>
						</div>
						<div>
							<dt>{t('admin.import_imported')}</dt>
							<dd>{report.imported}</dd>
						</div>
						<div>
							<dt>{t('admin.import_duplicated')}</dt>
							<dd>{report.duplicated}</dd>
						</div>
					</dl>

					{#if report.rejected.length > 0}
						<h4 class="report__title">{t('admin.import_rejected')}</h4>
						<ul class="report__list">
							{#each report.rejected as row (row.row)}
								<li>{t('admin.import_rejected_row', { row: row.row, reason: row.reason })}</li>
							{/each}
						</ul>
					{/if}
				</div>
			{/if}
		</section>
	{/if}

	<a class="rank-link" href="/">{t('common.back')}</a>
</section>

<style>
	.admin {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-4);
	}

	.admin__intro {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding-top: var(--s-4);
	}

	.admin__card {
		display: flex;
		flex-direction: column;
		gap: var(--s-4);
		padding: var(--s-4);
		border-radius: var(--r-lg);
		background: var(--panel-bg);
		box-shadow: 0 5px 0 var(--panel-edge);
	}

	.template {
		display: inline-flex;
		align-items: center;
		align-self: flex-start;
		min-height: 44px;
		padding: 0 var(--s-3);
		border-radius: var(--r-sm);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
		color: var(--ink-2);
		font-size: 0.85rem;
		font-weight: 600;
		text-decoration: none;
	}

	.template:hover {
		color: var(--ink);
	}

	.admin__title {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.2rem;
	}

	.admin__bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--s-3);
	}

	.admin__session {
		color: var(--ink-3);
		font-size: 0.8rem;
	}

	.admin__summary {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--s-3);
		color: var(--ink-3);
		font-size: 0.82rem;
	}

	.admin__state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--s-3);
		padding: var(--s-6) var(--s-4);
		color: var(--ink-3);
		text-align: center;
	}

	.admin__error {
		color: var(--red-ink);
		font-size: 0.85rem;
		font-weight: 600;
	}

	.token-input {
		font-family: var(--font-ui);
		font-size: 1rem;
		font-weight: 500;
	}

	.filters {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--s-3);
	}

	.filters__cell {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		min-width: 0;
	}

	.filters__search {
		grid-column: 1 / -1;
	}

	.filters__row {
		display: flex;
		align-items: stretch;
		gap: var(--s-2);
	}

	.filters__row .field__well {
		flex: 1;
		min-width: 0;
	}

	.filters__input {
		font-family: var(--font-ui);
		font-size: 1rem;
		font-weight: 500;
	}

	.select {
		width: 100%;
		min-height: 44px;
		padding: 0 var(--s-3);
		border: 2px solid var(--field-border-color);
		border-radius: var(--r-md);
		background: var(--field-bg);
		box-shadow: var(--field-shadow);
		color: var(--ink);
		font-family: var(--font-ui);
		font-size: 0.95rem;
	}

	.mini {
		flex: none;
		min-height: 44px;
		padding: 0 var(--s-3);
		border: 0;
		border-radius: var(--r-md);
		background: var(--well-border);
		color: var(--ink);
		font-family: var(--font-ui);
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
	}

	.mini--ghost {
		align-self: flex-start;
		background: var(--well-bg);
		box-shadow: inset 0 0 0 2px var(--well-border);
		color: var(--ink-3);
	}

	.mini:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.questions {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.q {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
		padding: var(--s-4);
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
	}

	.q__head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--s-2);
	}

	.q__status {
		flex: none;
		padding: 3px 10px;
		border-radius: var(--r-full);
		background: var(--panel-bg);
		color: var(--ink-3);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.q__status[data-status='published'] {
		background: var(--green);
		box-shadow: 0 2px 0 var(--green-edge);
		color: #ffffff;
	}

	.q__status[data-status='archived'] {
		background: var(--yellow);
		box-shadow: 0 2px 0 var(--yellow-edge);
		color: #3f2d00;
	}

	.q__prompt {
		font-size: 1rem;
		font-weight: 700;
		line-height: 1.35;
	}

	.q__options {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.q__option {
		display: flex;
		align-items: flex-start;
		gap: var(--s-2);
		padding: 6px 8px;
		border-radius: var(--r-sm);
		color: var(--ink-2);
		font-size: 0.88rem;
	}

	.q__option.is-correct {
		background: rgb(30 199 101 / 0.16);
		box-shadow: inset 0 0 0 1.5px var(--green);
		color: var(--ink);
	}

	.q__key {
		display: grid;
		place-items: center;
		flex: none;
		width: 20px;
		height: 20px;
		border-radius: 6px;
		background: var(--panel-bg);
		color: var(--ink-3);
		font-size: 0.7rem;
		font-weight: 700;
	}

	.q__option.is-correct .q__key {
		background: var(--green);
		color: #ffffff;
	}

	.q__check {
		margin-left: auto;
		color: var(--green);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.q__note {
		color: var(--ink-3);
		font-size: 0.82rem;
		line-height: 1.4;
	}

	.q__note strong {
		color: var(--ink-2);
	}

	.q__meta {
		display: flex;
		flex-wrap: wrap;
		gap: var(--s-2) var(--s-3);
		color: var(--ink-3);
		font-size: 0.75rem;
	}

	.q__media {
		color: var(--blue);
		font-weight: 600;
	}

	.pager {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--s-3);
	}

	.pager__state {
		color: var(--ink-3);
		font-size: 0.82rem;
		text-align: center;
	}

	.file {
		width: 100%;
		min-height: 44px;
		padding: 9px;
		border: 2px dashed var(--well-border);
		border-radius: var(--r-md);
		background: var(--well-bg);
		color: var(--ink-2);
		font-family: var(--font-ui);
		font-size: 0.85rem;
	}

	.file::file-selector-button {
		min-height: 32px;
		margin-right: var(--s-3);
		padding: 0 var(--s-3);
		border: 0;
		border-radius: var(--r-sm);
		background: var(--well-border);
		color: var(--ink);
		font-family: var(--font-ui);
		font-size: 0.8rem;
		font-weight: 700;
		cursor: pointer;
	}

	.status-choice {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		min-inline-size: 0;
		margin: 0;
		padding: 0;
		border: 0;
	}

	.segmented {
		display: flex;
		gap: var(--s-1);
		padding: 4px;
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.35);
	}

	.segment {
		flex: 1;
		min-height: 40px;
		border: 0;
		border-radius: var(--r-sm);
		background: transparent;
		color: var(--ink-3);
		font-family: var(--font-display);
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
	}

	.segment.is-on {
		background: var(--panel-bg);
		box-shadow: 0 3px 0 var(--panel-edge);
		color: var(--ink);
	}

	.report {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
		padding: var(--s-3);
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.3);
	}

	.report__title {
		color: var(--ink-2);
		font-family: var(--font-display);
		font-size: 0.95rem;
	}

	.report__stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--s-2);
		margin: 0;
	}

	.report__stats dt {
		color: var(--ink-3);
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.report__stats dd {
		margin: 0;
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.3rem;
		font-weight: 700;
	}

	.report__list {
		max-height: 180px;
		margin: 0;
		padding-left: 1.1rem;
		overflow: auto;
		color: var(--red-ink);
		font-size: 0.8rem;
		line-height: 1.45;
	}
</style>
