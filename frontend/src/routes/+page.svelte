<script lang="ts">
	import { fetchDashboard } from '#lib/api';
	import EventRow from '#lib/components/EventRow.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import ProjectCard from '#lib/components/ProjectCard.svelte';
	import StatCard from '#lib/components/StatCard.svelte';
	import { daysSince, eventBranch, relativeTime } from '#lib/format';
	import type { Dashboard } from '#lib/types';
	import { onMount } from 'svelte';

	let data = $state<Dashboard | null>(null);
	let error = $state('');
	let loading = $state(true);

	async function load() {
		loading = true;
		error = '';
		try {
			data = await fetchDashboard();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load your dashboard';
		} finally {
			loading = false;
		}
	}

	onMount(load);

	const hour = new Date().getHours();
	const greeting = hour < 5 ? 'Still up?' : hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

	const focusBranch = $derived.by(() => {
		if (!data?.last_active_project) return null;
		const event = data.recent_activity.find(
			(item) => item.project_id === data?.last_active_project?.id && eventBranch(item.payload)
		);
		return event ? eventBranch(event.payload) : null;
	});

	const summaryProject = $derived.by(() => {
		if (!data?.latest_summary || !data.last_active_project) return data?.last_active_project?.name;
		return data.last_active_project.name;
	});
</script>

<svelte:head><title>Dashboard — DevFlow</title></svelte:head>

<div class="flex flex-col gap-6">
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
		<div class="grid gap-4 sm:grid-cols-3">
			{#each Array(3) as _}
				<div class="panel h-28 p-5"><div class="skeleton h-3 w-20"></div><div class="skeleton mt-4 h-8 w-14"></div></div>
			{/each}
		</div>
		<div class="grid gap-4 lg:grid-cols-5">
			<div class="panel h-72 lg:col-span-3"></div>
			<div class="panel h-72 lg:col-span-2"></div>
		</div>
	{:else if error}
		<div class="panel flex flex-col items-center gap-4 p-10 text-center">
			<Icon name="alert" size={28} class="text-amber-300" />
			<div>
				<p class="font-medium text-zinc-200">Could not reach your memory</p>
				<p class="mt-1 text-sm text-zinc-500">{error}</p>
			</div>
			<button class="btn-secondary" onclick={load}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if data}
		{#if data.total_projects === 0}
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
			<!-- Stats -->
			<div class="grid gap-4 sm:grid-cols-3">
				<StatCard label="Active projects" value={data.active_projects} icon="zap" hint="Currently in motion" />
				<StatCard label="Captured events" value={data.total_events} icon="commit" hint="Commits, branches & pushes" tone="text-iris-300" />
				<StatCard label="Projects in memory" value={data.total_projects} icon="folder" hint="Across all repositories" tone="text-sky-300" />
			</div>

			<div class="grid gap-4 lg:grid-cols-5">
				<!-- Current focus -->
				<section class="panel relative overflow-hidden p-5 sm:p-6 lg:col-span-3">
					<div class="pointer-events-none absolute -right-24 -top-24 h-56 w-56 rounded-full bg-iris-500/10 blur-3xl"></div>
					<div class="relative">
						<div class="flex items-center justify-between">
							<p class="section-title">Last active project</p>
							{#if data.last_active_project}
								<span class="chip bg-mint-400/10 text-mint-300 ring-mint-400/25">
									<span class="h-1.5 w-1.5 rounded-full bg-current"></span> in progress
								</span>
							{/if}
						</div>

						{#if data.last_active_project}
							{@const project = data.last_active_project}
							<a href="/projects/{project.id}" class="group mt-4 block">
								<h2 class="text-2xl font-semibold tracking-tight text-zinc-50 group-hover:text-white">
									{project.name}
								</h2>
								<p class="mt-1.5 text-sm text-zinc-500">
									Started {daysSince(project.started_at)} days ago · Last activity {relativeTime(project.last_activity_at)}
								</p>
							</a>

							<div class="mt-5 grid grid-cols-2 gap-3">
								<div class="rounded-xl border border-white/6 bg-ink-900/60 p-3.5">
									<p class="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Current focus</p>
									<p class="mt-1.5 flex items-center gap-1.5 truncate font-mono text-sm text-iris-200">
										<Icon name="branch" size={13} />{focusBranch ?? 'main'}
									</p>
								</div>
								<div class="rounded-xl border border-white/6 bg-ink-900/60 p-3.5">
									<p class="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Activity</p>
									<p class="mt-1.5 text-sm text-zinc-300">{project.event_count} events · {project.repository_count} repos</p>
								</div>
							</div>

							<div class="mt-5">
								<p class="section-title">Recent work</p>
								<div class="mt-1 divide-y divide-white/5">
									{#each data.recent_activity.filter((e) => e.project_id === project.id).slice(0, 4) as event}
										<EventRow {event} />
									{:else}
										<p class="py-4 text-sm text-zinc-600">No recent events for this project.</p>
									{/each}
								</div>
							</div>
						{:else}
							<p class="mt-4 text-sm text-zinc-500">Connect a repository to see your current focus.</p>
						{/if}
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

					{#if data.latest_summary}
						<p class="mt-4 flex-1 text-[13px] leading-relaxed text-zinc-300">{data.latest_summary.summary}</p>
						<div class="mt-4 border-t border-white/6 pt-3">
							<p class="text-[11px] text-zinc-600">
								{summaryProject} · {relativeTime(data.latest_summary.created_at)}
							</p>
							<a href="/insights" class="mt-2 inline-flex items-center gap-1 text-xs font-medium text-mint-300 hover:text-mint-200">
								All insights <Icon name="chevron-right" size={12} />
							</a>
						</div>
					{:else}
						<div class="flex flex-1 flex-col items-center justify-center py-8 text-center">
							<p class="text-sm text-zinc-400">No memories generated yet.</p>
							<p class="mt-1 max-w-[24ch] text-xs text-zinc-600">Your timeline becomes a story once you ask DevFlow to summarise it.</p>
							<a href="/insights" class="btn-secondary mt-4 text-xs"><Icon name="sparkles" size={14} /> Generate a summary</a>
						</div>
					{/if}
				</section>
			</div>

			<!-- Recent activity -->
			<section class="panel p-5 sm:p-6">
				<div class="flex items-center justify-between">
					<p class="section-title">Recent activity</p>
					<a href="/projects" class="text-xs font-medium text-zinc-500 hover:text-zinc-300">View projects</a>
				</div>
				<div class="mt-2 divide-y divide-white/5">
					{#each data.recent_activity.slice(0, 8) as event}
						<EventRow {event} showProject />
					{:else}
						<p class="py-6 text-center text-sm text-zinc-600">Waiting for the first Git event.</p>
					{/each}
				</div>
			</section>

			{#if data.last_active_project}
				<div class="grid gap-4 sm:grid-cols-2 lg:hidden">
					<ProjectCard project={data.last_active_project} />
				</div>
			{/if}
		{/if}
	{/if}
</div>
