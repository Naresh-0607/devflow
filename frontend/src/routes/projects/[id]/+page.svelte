<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		deleteProject,
		fetchProject,
		generateSummary,
		updateProject
	} from '#lib/api';
	import EventRow from '#lib/components/EventRow.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import { daysSince, formatDate, relativeTime } from '#lib/format';
	import type { ProjectDetail, ProjectStatus } from '#lib/types';

	let project = $state<ProjectDetail | null>(null);
	let loading = $state(true);
	let error = $state('');
	let notFound = $state(false);
	let updatingStatus = $state(false);
	let generating = $state(false);
	let actionError = $state('');

	const projectId = $derived(page.params.id ?? '');
	const statuses: ProjectStatus[] = ['ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED'];

	async function load(id: string) {
		loading = true;
		error = '';
		notFound = false;
		try {
			project = await fetchProject(id);
		} catch (err) {
			if (err instanceof Error && err.message.toLowerCase().includes('not found')) {
				notFound = true;
			} else {
				error = err instanceof Error ? err.message : 'Could not load project';
			}
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (projectId) load(projectId);
	});

	async function changeStatus(next: ProjectStatus) {
		if (!project || next === project.status) return;
		updatingStatus = true;
		actionError = '';
		try {
			const updated = await updateProject(project.id, { status: next });
			project = { ...project, ...updated };
		} catch (err) {
			actionError = err instanceof Error ? err.message : 'Could not update status';
		} finally {
			updatingStatus = false;
		}
	}

	async function summarise() {
		if (!project) return;
		generating = true;
		actionError = '';
		try {
			const summary = await generateSummary(project.id, 'PROJECT');
			project = { ...project, latest_summary: summary };
		} catch (err) {
			actionError = err instanceof Error ? err.message : 'Could not generate a summary';
		} finally {
			generating = false;
		}
	}

	async function remove() {
		if (!project) return;
		if (!confirm(`Delete "${project.name}" and its entire history? This cannot be undone.`)) return;
		await deleteProject(project.id);
		await goto('/projects');
	}
</script>

<svelte:head><title>{project?.name ?? 'Project'} — DevFlow</title></svelte:head>

<div class="flex flex-col gap-6">
	<a href="/projects" class="inline-flex w-fit items-center gap-1.5 text-xs font-medium text-zinc-500 transition hover:text-zinc-300">
		<Icon name="arrow-left" size={14} /> All projects
	</a>

	{#if loading}
		<div class="panel p-6"><div class="skeleton h-8 w-1/3"></div><div class="skeleton mt-4 h-4 w-2/3"></div></div>
		<div class="grid gap-4 sm:grid-cols-3">{#each Array(3) as _}<div class="panel h-24"></div>{/each}</div>
		<div class="panel h-80"></div>
	{:else if notFound}
		<div class="panel flex flex-col items-center px-6 py-16 text-center">
			<Icon name="alert" size={28} class="text-amber-300" />
			<h2 class="mt-4 text-lg font-semibold text-zinc-100">Project not found</h2>
			<p class="mt-1.5 text-sm text-zinc-500">It may have been deleted or belongs to another account.</p>
			<a href="/projects" class="btn-secondary mt-5">Back to projects</a>
		</div>
	{:else if error}
		<div class="panel flex flex-col items-center gap-3 p-10 text-center">
			<p class="text-sm text-zinc-400">{error}</p>
			<button class="btn-secondary" onclick={() => load(projectId)}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if project}
		<!-- Header -->
		<header class="panel relative overflow-hidden p-5 sm:p-6">
			<div class="pointer-events-none absolute -right-24 -top-24 h-56 w-56 rounded-full bg-iris-500/10 blur-3xl"></div>
			<div class="relative flex flex-wrap items-start justify-between gap-4">
				<div class="min-w-0">
					<div class="flex flex-wrap items-center gap-2.5">
						<h1 class="text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">{project.name}</h1>
						<StatusBadge status={project.status} />
					</div>
					<p class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500">
						<span class="inline-flex items-center gap-1.5"><Icon name="calendar" size={13} /> Started {formatDate(project.started_at)} · {daysSince(project.started_at)} days ago</span>
						<span class="inline-flex items-center gap-1.5"><Icon name="clock" size={13} /> Last activity {relativeTime(project.last_activity_at)}</span>
					</p>
					{#if project.description}
						<p class="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">{project.description}</p>
					{/if}
				</div>
				<div class="flex flex-wrap items-center gap-2">
					<select
						class="input w-auto py-2 text-xs"
						value={project.status}
						disabled={updatingStatus}
						onchange={(event) => changeStatus((event.currentTarget as HTMLSelectElement).value as ProjectStatus)}
						aria-label="Project status"
					>
						{#each statuses as status}
							<option value={status}>{status.charAt(0) + status.slice(1).toLowerCase()}</option>
						{/each}
					</select>
					<button class="btn-secondary text-xs" onclick={summarise} disabled={generating}>
						{#if generating}<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/20 border-t-mint-300"></span>{:else}<Icon name="sparkles" size={14} />{/if}
						{generating ? 'Remembering…' : 'Summarise'}
					</button>
					<button class="btn-ghost text-xs text-zinc-600 hover:text-red-300" onclick={remove} aria-label="Delete project">
						<Icon name="trash" size={15} />
					</button>
				</div>
			</div>

			{#if actionError}
				<p class="relative mt-3 text-xs text-red-300">{actionError}</p>
			{/if}

			<div class="relative mt-5 grid grid-cols-3 gap-3 border-t border-white/6 pt-4">
				<div><p class="section-title">Events</p><p class="mt-1 text-xl font-semibold text-zinc-100">{project.event_count}</p></div>
				<div><p class="section-title">Repositories</p><p class="mt-1 text-xl font-semibold text-zinc-100">{project.repositories.length}</p></div>
				<div><p class="section-title">Memories</p><p class="mt-1 text-xl font-semibold text-zinc-100">{project.latest_summary ? '1+' : '0'}</p></div>
			</div>
		</header>

		<!-- AI memory -->
		<section class="panel relative overflow-hidden p-5 sm:p-6">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2.5">
					<span class="grid h-8 w-8 place-items-center rounded-lg bg-iris-500/10 text-iris-300 ring-1 ring-inset ring-iris-400/20"><Icon name="sparkles" size={16} /></span>
					<div>
						<p class="text-sm font-semibold text-zinc-100">Project memory</p>
						<p class="text-[11px] text-zinc-600">AI-generated from your Git timeline</p>
					</div>
				</div>
				{#if project.latest_summary}
					<span class="text-[11px] text-zinc-600">{relativeTime(project.latest_summary.created_at)}</span>
				{/if}
			</div>
			{#if project.latest_summary}
				<p class="mt-4 text-sm leading-relaxed text-zinc-300">{project.latest_summary.summary}</p>
			{:else}
				<div class="mt-4 rounded-xl border border-dashed border-white/10 bg-ink-900/40 px-4 py-8 text-center">
					<p class="text-sm text-zinc-400">No memory generated yet.</p>
					<p class="mt-1 text-xs text-zinc-600">Summarise this project to turn commits and branches into a story.</p>
					<button class="btn-secondary mt-4 text-xs" onclick={summarise} disabled={generating}>
						<Icon name="sparkles" size={14} /> Generate memory
					</button>
				</div>
			{/if}
		</section>

		<div class="grid gap-4 lg:grid-cols-5">
			<!-- Timeline -->
			<section class="panel p-5 sm:p-6 lg:col-span-3">
				<div class="flex items-center justify-between">
					<p class="section-title">Timeline</p>
					<span class="text-[11px] text-zinc-600">{project.recent_events.length} recent events</span>
				</div>
				<div class="mt-2 divide-y divide-white/5">
					{#each project.recent_events as event (event.id)}
						<EventRow {event} />
					{:else}
						<p class="py-8 text-center text-sm text-zinc-600">No events yet. Install the agent to start the timeline.</p>
					{/each}
				</div>
			</section>

			<!-- Repositories -->
			<section class="panel h-fit p-5 sm:p-6 lg:col-span-2">
				<p class="section-title">Repositories</p>
				<div class="mt-3 space-y-2.5">
					{#each project.repositories as repo (repo.id)}
						<div class="rounded-xl border border-white/6 bg-ink-900/50 p-3.5">
							<div class="flex items-center gap-2">
								<Icon name="branch" size={14} class="text-iris-300" />
								<p class="truncate text-sm font-medium text-zinc-200">{repo.name}</p>
							</div>
							<p class="mt-1.5 truncate font-mono text-[10px] text-zinc-600" title={repo.local_identifier}>{repo.local_identifier}</p>
							{#if repo.remote_url}
								<a href={repo.remote_url} target="_blank" rel="noreferrer" class="mt-1.5 inline-flex items-center gap-1 text-[11px] text-mint-300 hover:text-mint-200">
									<Icon name="link" size={11} /> Remote
								</a>
							{/if}
						</div>
					{:else}
						<p class="text-sm text-zinc-600">No repositories linked.</p>
					{/each}
				</div>
			</section>
		</div>
	{/if}
</div>
