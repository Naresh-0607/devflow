<script lang="ts">
	import { fetchDashboard, writeCache } from '#lib/api';
	import EventRow from '#lib/components/EventRow.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import StatCard from '#lib/components/StatCard.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import { daysSince, eventBranch, relativeTime } from '#lib/format';
	import type { SwrResult } from '#lib/load';
	import type { Dashboard } from '#lib/types';

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
</script>

<svelte:head><title>Dashboard — DevFlow</title></svelte:head>

<div class="flex flex-col gap-5 sm:gap-6">
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div>
			<p class="text-xs font-medium uppercase tracking-[0.2em] text-mint-400/80">{greeting}</p>
			<h1 class="mt-1.5 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
				Here's what you were building.
			</h1>
		</div>
		<a href="/projects" class="btn-secondary hidden sm:inline-flex">
			<Icon name="folder" size={15} /> All projects
		</a>
	</div>

	{#if loading}
		<div class="panel h-56 p-6 sm:h-52">
			<div class="skeleton h-3 w-40"></div>
			<div class="skeleton mt-5 h-8 w-2/3"></div>
			<div class="skeleton mt-3 h-4 w-1/2"></div>
			<div class="mt-6 flex gap-3"><div class="skeleton h-10 w-32"></div><div class="skeleton h-10 w-32"></div></div>
		</div>
		<div class="grid gap-4 sm:grid-cols-3">
			{#each Array(3) as _}
				<div class="panel h-28 p-5"><div class="skeleton h-3 w-20"></div><div class="skeleton mt-4 h-8 w-14"></div></div>
			{/each}
		</div>
		<div class="grid gap-4 lg:grid-cols-5">
			<div class="panel h-72 lg:col-span-3"><div class="skeleton m-5 h-4 w-28"></div></div>
			<div class="panel h-72 lg:col-span-2"><div class="skeleton m-5 h-4 w-28"></div></div>
		</div>
	{:else if error && !dashboard}
		<div class="panel flex flex-col items-center gap-4 p-10 text-center">
			<Icon name="alert" size={28} class="text-amber-300" />
			<div>
				<p class="font-medium text-zinc-200">Could not reach your memory</p>
				<p class="mt-1 text-sm text-zinc-500">{error}</p>
			</div>
			<button class="btn-secondary" onclick={reload}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if dashboard}
		{#if dashboard.total_projects === 0}
			<div class="panel relative overflow-hidden p-6 sm:p-10">
				<div class="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-mint-400/10 blur-3xl"></div>
				<div class="relative max-w-xl">
					<div class="grid h-12 w-12 place-items-center rounded-2xl bg-mint-400/10 text-mint-300 ring-1 ring-inset ring-mint-400/20">
						<Icon name="zap" size={22} />
					</div>
					<h2 class="mt-5 text-xl font-semibold text-zinc-50">Your memory starts with one commit.</h2>
					<p class="mt-2 text-sm leading-relaxed text-zinc-400">
						Install the DevFlow agent, connect your machine, and every commit, branch and push
						becomes part of a timeline you can actually remember.
					</p>
					<div class="mt-6 flex flex-wrap gap-3">
						<a href="/settings" class="btn-primary"><Icon name="key" size={15} /> Connect a device</a>
						<a href="/projects" class="btn-secondary"><Icon name="plus" size={15} /> Create a project</a>
					</div>
				</div>
			</div>
		{:else}
			<!-- Hero: the first thing visible on a phone. -->
			{#if dashboard.last_active_project}
				{@const project = dashboard.last_active_project}
				<section
					class="panel relative overflow-hidden p-5 sm:p-6"
					aria-labelledby="continue-heading"
				>
					<div class="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-iris-500/12 blur-3xl"></div>
					<div class="pointer-events-none absolute -bottom-24 -left-16 h-56 w-56 rounded-full bg-mint-400/8 blur-3xl"></div>
					<div class="relative">
						<div class="flex items-center justify-between gap-3">
							<p class="section-title">Continue where you left off</p>
							<StatusBadge status={project.status} />
						</div>

						<h2 id="continue-heading" class="mt-3 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
							{project.name}
						</h2>
						<p class="mt-1.5 text-sm text-zinc-500">
							Started {daysSince(project.started_at)} days ago · Last activity {relativeTime(project.last_activity_at)}
						</p>

						<div class="mt-4 flex flex-wrap gap-2">
							<span class="chip bg-iris-500/10 font-mono text-iris-200 ring-iris-400/25">
								<Icon name="branch" size={11} /> {focusBranch ?? 'main'}
							</span>
							<span class="chip bg-white/5 text-zinc-400 ring-white/10">
								<Icon name="commit" size={11} /> {project.event_count} events
							</span>
							<span class="chip bg-white/5 text-zinc-400 ring-white/10">
								<Icon name="folder" size={11} /> {project.repository_count} repos
							</span>
						</div>

						{#if dashboard.latest_summary}
							<div class="mt-5 rounded-xl border border-white/6 bg-ink-900/60 p-4">
								<p class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
									<Icon name="sparkles" size={12} class="text-iris-300" /> Latest memory
								</p>
								<p class="mt-2 line-clamp-3 text-[13px] leading-relaxed text-zinc-300">
									{dashboard.latest_summary.summary}
								</p>
							</div>
						{/if}

						<div class="mt-5 flex flex-wrap gap-2.5">
							<a href="/projects/{project.id}" class="btn-primary">
								Open project <Icon name="chevron-right" size={15} />
							</a>
							<a href="/chat" class="btn-secondary">
								<Icon name="message" size={15} /> Ask DevFlow
							</a>
						</div>
					</div>
				</section>
			{/if}

			<!-- Stats -->
			<div class="grid gap-4 sm:grid-cols-3">
				<StatCard label="Active projects" value={dashboard.active_projects} icon="zap" hint="Currently in motion" />
				<StatCard label="Captured events" value={dashboard.total_events} icon="commit" hint="Commits, branches & pushes" tone="text-iris-300" />
				<StatCard label="Projects in memory" value={dashboard.total_projects} icon="folder" hint="Across all repositories" tone="text-sky-300" />
			</div>

			<div class="grid gap-4 lg:grid-cols-5">
				<!-- Recent activity -->
				<section class="panel p-5 sm:p-6 lg:col-span-3">
					<div class="flex items-center justify-between">
						<p class="section-title">Recent activity</p>
						<a href="/projects" class="text-xs font-medium text-zinc-500 hover:text-zinc-300">View projects</a>
					</div>
					<div class="mt-2 divide-y divide-white/5">
						{#each dashboard.recent_activity.slice(0, 8) as event}
							<EventRow {event} showProject />
						{:else}
							<p class="py-6 text-center text-sm text-zinc-600">Waiting for the first Git event.</p>
						{/each}
					</div>
				</section>

				<!-- Latest AI summary -->
				<section class="panel flex flex-col p-5 sm:p-6 lg:col-span-2">
					<div class="flex items-center justify-between">
						<p class="section-title">Latest memory</p>
						<span class="grid h-8 w-8 place-items-center rounded-lg bg-iris-500/10 text-iris-300 ring-1 ring-inset ring-iris-400/20">
							<Icon name="sparkles" size={16} />
						</span>
					</div>

					{#if dashboard.latest_summary}
						<p class="mt-4 flex-1 text-[13px] leading-relaxed text-zinc-300">{dashboard.latest_summary.summary}</p>
						<div class="mt-4 border-t border-white/6 pt-3">
							<p class="text-[11px] text-zinc-600">
								{dashboard.last_active_project?.name ?? 'Project'} · {relativeTime(dashboard.latest_summary.created_at)}
							</p>
							<a href="/chat" class="mt-2 inline-flex min-h-11 items-center gap-1 text-xs font-medium text-mint-300 hover:text-mint-200">
								Ask about it <Icon name="chevron-right" size={12} />
							</a>
						</div>
					{:else}
						<div class="flex flex-1 flex-col items-center justify-center py-8 text-center">
							<p class="text-sm text-zinc-400">No memories generated yet.</p>
							<p class="mt-1 max-w-[24ch] text-xs text-zinc-600">Your timeline becomes a story once you ask DevFlow to summarise it.</p>
							<a href="/projects" class="btn-secondary mt-4 text-xs"><Icon name="sparkles" size={14} /> Open a project</a>
						</div>
					{/if}
				</section>
			</div>

			{#if refreshing}
				<p class="text-center text-[11px] text-zinc-600" aria-live="polite">Refreshing in the background…</p>
			{/if}
		{/if}
	{/if}
</div>
