<script lang="ts">
	import { fetchInsights, generateSummary } from '#lib/api';
	import Icon from '#lib/components/Icon.svelte';
	import { relativeTime } from '#lib/format';
	import type { InsightFeed, Project, Summary, SummaryType } from '#lib/types';
	import { onMount } from 'svelte';

	let feed = $state<InsightFeed | null>(null);
	let loading = $state(true);
	let error = $state('');

	let typeFilter = $state<'ALL' | SummaryType>('ALL');
	let projectFilter = $state('ALL');

	let selectedProject = $state('');
	let selectedType = $state<SummaryType>('PROJECT');
	let generating = $state(false);
	let generateError = $state('');

	const types: Array<'ALL' | SummaryType> = ['ALL', 'DAILY', 'WEEKLY', 'PROJECT'];

	const projectName = (id: string): string =>
		feed?.projects.find((project) => project.id === id)?.name ?? 'Project';

	const visible = $derived(
		(feed?.summaries ?? []).filter((summary) => {
			const matchesType = typeFilter === 'ALL' || summary.summary_type === typeFilter;
			const matchesProject = projectFilter === 'ALL' || summary.project_id === projectFilter;
			return matchesType && matchesProject;
		})
	);

	const typeTone: Record<SummaryType, string> = {
		DAILY: 'bg-sky-400/10 text-sky-300 ring-sky-400/25',
		WEEKLY: 'bg-iris-400/10 text-iris-300 ring-iris-400/25',
		PROJECT: 'bg-mint-400/10 text-mint-300 ring-mint-400/25'
	};

	const typeLabel: Record<SummaryType, string> = {
		DAILY: 'Daily',
		WEEKLY: 'Weekly',
		PROJECT: 'Project'
	};

	async function load() {
		loading = true;
		error = '';
		try {
			feed = await fetchInsights();
			if (!selectedProject && feed.projects.length > 0) {
				selectedProject = feed.projects[0].id;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load insights';
		} finally {
			loading = false;
		}
	}

	async function generate() {
		if (!selectedProject) return;
		generating = true;
		generateError = '';
		try {
			const summary = await generateSummary(selectedProject, selectedType);
			if (feed) feed = { ...feed, summaries: [summary, ...feed.summaries] };
			typeFilter = 'ALL';
			projectFilter = 'ALL';
		} catch (err) {
			generateError = err instanceof Error ? err.message : 'Could not generate a summary';
		} finally {
			generating = false;
		}
	}

	onMount(load);
</script>

<svelte:head><title>AI Insights — DevFlow</title></svelte:head>

<div class="flex flex-col gap-6">
	<div>
		<p class="text-xs font-medium uppercase tracking-[0.2em] text-mint-400/80">Remembered for you</p>
		<h1 class="mt-1.5 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">AI Insights</h1>
		<p class="mt-1.5 text-sm text-zinc-500">Development summaries, written from your own Git activity.</p>
	</div>

	<!-- Generator -->
	<section class="panel relative overflow-hidden p-5 sm:p-6">
		<div class="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-iris-500/10 blur-3xl"></div>
		<div class="relative flex flex-col gap-4 sm:flex-row sm:items-end">
			<div class="flex-1">
				<label class="label" for="summary-project">Project</label>
				<select id="summary-project" class="input" bind:value={selectedProject} disabled={!feed?.projects.length}>
					{#each feed?.projects ?? [] as project (project.id)}
						<option value={project.id}>{project.name}</option>
					{/each}
				</select>
			</div>
			<div class="sm:w-44">
				<label class="label" for="summary-type">Memory type</label>
				<select id="summary-type" class="input" bind:value={selectedType}>
					<option value="PROJECT">Project memory</option>
					<option value="WEEKLY">Weekly summary</option>
					<option value="DAILY">Daily summary</option>
				</select>
			</div>
			<button class="btn-primary shrink-0" onclick={generate} disabled={generating || !selectedProject}>
				{#if generating}
					<span class="h-4 w-4 animate-spin rounded-full border-2 border-ink-950/25 border-t-ink-950"></span> Remembering…
				{:else}
					<Icon name="sparkles" size={15} /> Generate
				{/if}
			</button>
		</div>
		{#if generateError}
			<p class="relative mt-3 text-xs text-red-300">{generateError}</p>
		{:else if !feed?.projects.length && !loading}
			<p class="relative mt-3 text-xs text-zinc-500">Connect a repository first — summaries need a timeline.</p>
		{/if}
	</section>

	<!-- Filters -->
	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div class="flex gap-1.5 overflow-x-auto">
			{#each types as type}
				<button
					class="whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition {typeFilter === type
						? 'bg-white/10 text-zinc-100'
						: 'text-zinc-500 hover:bg-white/5 hover:text-zinc-300'}"
					onclick={() => (typeFilter = type)}
				>
					{type === 'ALL' ? 'All memories' : typeLabel[type]}
				</button>
			{/each}
		</div>
		{#if feed && feed.projects.length > 1}
			<select class="input w-auto py-1.5 text-xs" bind:value={projectFilter} aria-label="Filter by project">
				<option value="ALL">All projects</option>
				{#each feed.projects as project (project.id)}
					<option value={project.id}>{project.name}</option>
				{/each}
			</select>
		{/if}
	</div>

	{#if loading}
		<div class="space-y-4">
			{#each Array(3) as _}
				<div class="panel p-5"><div class="skeleton h-3 w-24"></div><div class="skeleton mt-3 h-4 w-full"></div><div class="skeleton mt-2 h-4 w-2/3"></div></div>
			{/each}
		</div>
	{:else if error}
		<div class="panel flex flex-col items-center gap-3 p-10 text-center">
			<Icon name="alert" size={26} class="text-amber-300" />
			<p class="text-sm text-zinc-400">{error}</p>
			<button class="btn-secondary" onclick={load}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if visible.length === 0}
		<div class="panel flex flex-col items-center px-6 py-16 text-center">
			<div class="grid h-12 w-12 place-items-center rounded-2xl bg-iris-500/10 text-iris-300 ring-1 ring-inset ring-iris-400/20">
				<Icon name="sparkles" size={22} />
			</div>
			<h2 class="mt-4 text-lg font-semibold text-zinc-100">
				{feed?.summaries.length ? 'Nothing matches this filter' : 'No memories yet'}
			</h2>
			<p class="mt-1.5 max-w-sm text-sm text-zinc-500">
				{feed?.summaries.length
					? 'Try a different memory type or project.'
					: 'Generate your first summary above. DevFlow will turn raw Git events into a story you can remember.'}
			</p>
		</div>
	{:else}
		<div class="space-y-4">
			{#each visible as summary (summary.id)}
				<article class="panel panel-hover p-5 sm:p-6">
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<span class="chip {typeTone[summary.summary_type]}">{typeLabel[summary.summary_type]}</span>
							<a href="/projects/{summary.project_id}" class="text-sm font-medium text-zinc-200 hover:text-white">{projectName(summary.project_id)}</a>
						</div>
						<span class="text-[11px] text-zinc-600">{relativeTime(summary.created_at)}</span>
					</div>
					<p class="mt-3.5 text-sm leading-relaxed text-zinc-300">{summary.summary}</p>
				</article>
			{/each}
		</div>
	{/if}
</div>
