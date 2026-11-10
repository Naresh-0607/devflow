<script lang="ts">
	import { fetchDashboard, writeCache } from '#lib/api';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import EventRow from '#lib/components/EventRow.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import Sparkline from '#lib/components/Sparkline.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import { daysSince, eventBranch, relativeTime } from '#lib/format';
	import type { SwrResult } from '#lib/load';
	import type { Dashboard, ProjectStatus } from '#lib/types';

	let { data }: { data: SwrResult<Dashboard> } = $props();

	// Seed from the cache once; the effect below swaps in fresh data.
	// svelte-ignore state_referenced_locally
	let dashboard = $state<Dashboard | null>(data.cached);
	let error = $state('');
	// svelte-ignore state_referenced_locally
	let loading = $state(!data.cached);
	// svelte-ignore state_referenced_locally
	let refreshing = $state(Boolean(data.cached));

	$effect(() => {
		let active = true;
		data.fresh.then((result) => {
			if (!active) return;
			if (result.data) {
				dashboard = result.data;
				error = '';
			} else {
				error = result.error ?? 'Could not load your dashboard';
			}
			loading = false;
			refreshing = false;
		});
		return () => {
			active = false;
		};
	});

	async function reload() {
		loading = !dashboard;
		error = '';
		try {
			const fresh = await fetchDashboard();
			dashboard = fresh;
			writeCache('/dashboard', fresh);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load your dashboard';
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	const hour = new Date().getHours();
	const greeting =
		hour < 5 ? 'Still up?' : hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

	const focusBranch = $derived.by(() => {
		if (!dashboard?.last_active_project) return null;
		const event = dashboard.recent_activity.find(
			(item) =>
				item.project_id === dashboard?.last_active_project?.id && eventBranch(item.payload)
		);
		return event ? eventBranch(event.payload) : null;
	});

	type Pulse = {
		id: string;
		name: string;
		last: string;
		branch: string | null;
		status: ProjectStatus | null;
		series: number[];
	};

	function daySeries(projectId: string): number[] {
		const series = Array.from({ length: 14 }, () => 0);
		const now = new Date();
		const start =
			new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime() - 13 * 86400000;
		for (const event of dashboard?.recent_activity ?? []) {
			if (event.project_id !== projectId) continue;
			const date = new Date(event.created_at);
			const bucket = Math.round(
				(new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime() - start) /
					86400000
			);
			if (bucket >= 0 && bucket < 14) series[bucket] += 1;
		}
		return series;
	}

	// Only real activity is shown: projects that appear in the recent timeline.
	const recentProjects = $derived.by(() => {
		const map = new Map<string, Pulse>();
		const focus = dashboard?.last_active_project ?? null;
		for (const event of dashboard?.recent_activity ?? []) {
			if (!event.project_id) continue;
			const branch = eventBranch(event.payload);
			const existing = map.get(event.project_id);
			if (!existing) {
				map.set(event.project_id, {
					id: event.project_id,
					name: event.project_name ?? 'Project',
					last: event.created_at,
					branch,
					status: focus?.id === event.project_id ? focus.status : null,
					series: []
				});
			} else {
				if (new Date(event.created_at) > new Date(existing.last)) existing.last = event.created_at;
				if (!existing.branch && branch) existing.branch = branch;
			}
		}
		return [...map.values()]
			.slice(0, 4)
			.map((project) => ({ ...project, series: daySeries(project.id) }));
	});
</script>

<svelte:head><title>Dashboard — DevFlow</title></svelte:head>

<div class="flex flex-col gap-8">
	<PageHeader title={greeting} subtitle="Here's what you were building, and where you left off.">
		<a href="/projects" class="btn-secondary">
			<Icon name="folder" size={15} /> All projects
		</a>
	</PageHeader>

	{#if loading}
		<div class="card h-64 p-6 sm:p-8">
			<div class="skeleton h-3 w-40"></div>
			<div class="skeleton mt-5 h-8 w-2/3"></div>
			<div class="skeleton mt-3 h-4 w-1/2"></div>
			<div class="skeleton mt-6 h-10 w-36"></div>
		</div>
		<div class="grid gap-3 sm:grid-cols-2">
			{#each Array(2) as _}
				<div class="card h-32 p-5">
					<div class="skeleton h-4 w-1/2"></div>
					<div class="skeleton mt-3 h-3 w-2/3"></div>
					<div class="skeleton mt-5 h-6 w-full"></div>
				</div>
			{/each}
		</div>
		<div class="card h-80 p-5">
			<div class="skeleton h-4 w-32"></div>
			<div class="skeleton mt-5 h-12 w-full"></div>
			<div class="skeleton mt-3 h-12 w-full"></div>
			<div class="skeleton mt-3 h-12 w-full"></div>
		</div>
	{:else if error && !dashboard}
		<div class="card flex flex-col items-center gap-4 p-10 text-center">
			<Icon name="alert" size={24} class="text-warning" />
			<div>
				<p class="text-sm font-medium text-text">Could not reach your memory</p>
				<p class="mt-1 text-sm text-muted">{error}</p>
			</div>
			<button class="btn-secondary" onclick={reload}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if dashboard}
		{#if dashboard.total_projects === 0}
			<EmptyState
				icon="sparkles"
				title="Your memory starts with one commit."
				description="Install the DevFlow agent, connect your machine, and every commit, branch and push becomes part of a timeline you can actually remember."
			>
				<a href="/settings" class="btn-primary"><Icon name="key" size={15} /> Connect your laptop</a>
				<a href="/projects" class="btn-secondary"><Icon name="plus" size={15} /> Create a project</a>
			</EmptyState>
		{:else}
			<!-- Hero: the first thing visible on a phone. -->
			{#if dashboard.last_active_project}
				{@const project = dashboard.last_active_project}
				<section class="card p-6 sm:p-8" aria-labelledby="continue-heading">
					<div class="flex items-center justify-between gap-3">
						<p class="eyebrow text-accent">Continue where you left off</p>
						<StatusBadge status={project.status} />
					</div>

					<h2
						id="continue-heading"
						class="mt-3 text-3xl font-semibold tracking-tight text-text"
					>
						{project.name}
					</h2>
					<p class="mt-1.5 text-sm text-muted">
						Started {daysSince(project.started_at)} days ago · Last active {relativeTime(
							project.last_activity_at
						)}
					</p>

					<div class="mt-4 flex flex-wrap items-center gap-2 text-sm">
						<span class="text-muted">Current focus</span>
						<span
							class="inline-flex items-center gap-1.5 rounded-control border border-border bg-raised px-2 py-1 font-mono text-xs text-text"
						>
							<Icon name="branch" size={12} class="text-accent" />
							{focusBranch ?? 'main'}
						</span>
					</div>

					{#if dashboard.latest_summary}
						<div class="mt-6 border-t border-border pt-4">
							<p class="eyebrow">Latest memory</p>
							<p class="mt-2 line-clamp-3 max-w-2xl text-sm leading-relaxed text-muted">
								{dashboard.latest_summary.summary}
							</p>
						</div>
					{/if}

					<div class="mt-6 flex flex-wrap gap-2">
						<a href="/projects/{project.id}" class="btn-primary">
							Open project <Icon name="arrow-right" size={15} />
						</a>
						<a href="/chat" class="btn-secondary">
							<Icon name="message" size={15} /> Ask DevFlow
						</a>
					</div>
				</section>
			{/if}

			<!-- Active projects from the recent timeline -->
			{#if recentProjects.length > 0}
				<section>
					<div class="mb-3 flex items-center justify-between gap-3">
						<h2 class="section-title">In motion</h2>
						<a
							href="/projects"
							class="inline-flex min-h-11 items-center gap-1 text-xs font-medium text-muted transition hover:text-text"
						>
							All projects <Icon name="chevron-right" size={13} />
						</a>
					</div>
					<div class="grid gap-3 sm:grid-cols-2">
						{#each recentProjects as project (project.id)}
							<a
								href="/projects/{project.id}"
								class="card group p-5 transition duration-150 hover:border-accent/40"
								aria-label="Open {project.name}"
							>
								<div class="flex items-start justify-between gap-3">
									<h3 class="min-w-0 truncate text-sm font-semibold text-text">
										{project.name}
									</h3>
									{#if project.status}
										<StatusBadge status={project.status} />
									{:else}
										<span class="pill border-border bg-raised text-muted">
											<span class="h-1.5 w-1.5 rounded-full bg-muted"></span>
											Recent
										</span>
									{/if}
								</div>
								<p class="mt-1 text-xs text-muted">
									Last active {relativeTime(project.last)}
								</p>
								<div class="mt-4 flex items-end justify-between gap-3">
									<span
										class="inline-flex min-w-0 items-center gap-1.5 font-mono text-[11px] text-muted"
									>
										<Icon name="branch" size={11} />
										<span class="truncate">{project.branch ?? 'main'}</span>
									</span>
									<Sparkline values={project.series} label="{project.name} activity" />
								</div>
							</a>
						{/each}
					</div>
				</section>
			{/if}

			<!-- Recent activity -->
			<section>
				<div class="mb-3 flex items-center justify-between gap-3">
					<h2 class="section-title">Recent activity</h2>
					<a
						href="/chat"
						class="inline-flex min-h-11 items-center gap-1 text-xs font-medium text-muted transition hover:text-text"
					>
						Ask about it <Icon name="chevron-right" size={13} />
					</a>
				</div>
				<div class="card px-5 py-1 sm:px-6">
					<div class="divide-y divide-border">
						{#each dashboard.recent_activity.slice(0, 8) as event (event.id)}
							<EventRow {event} showProject />
						{:else}
							<p class="py-8 text-center text-sm text-muted">
								Waiting for the first Git event.
							</p>
						{/each}
					</div>
				</div>
			</section>

			{#if refreshing}
				<p class="text-center text-xs text-muted" aria-live="polite">Refreshing in the background…</p>
			{/if}
		{/if}
	{/if}
</div>
