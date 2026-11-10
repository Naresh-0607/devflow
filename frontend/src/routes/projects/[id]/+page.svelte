<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		deleteProject,
		fetchProject,
		generateSummary,
		updateProject,
		writeCache
	} from '#lib/api';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import Timeline from '#lib/components/Timeline.svelte';
	import { eventBranches } from '#lib/events';
	import { daysSince, eventBranch, formatDate, relativeTime } from '#lib/format';
	import type { SwrResult } from '#lib/load';
	import { toast } from '#lib/toast.svelte';
	import type { ProjectDetail, ProjectStatus } from '#lib/types';

	let { data }: { data: SwrResult<ProjectDetail> } = $props();

	// svelte-ignore state_referenced_locally
	let project = $state<ProjectDetail | null>(data.cached);
	// svelte-ignore state_referenced_locally
	let loading = $state(!data.cached);
	let error = $state('');
	let notFound = $state(false);
	let updatingStatus = $state(false);
	let generating = $state(false);
	let actionError = $state('');
	let branchFilter = $state('ALL');

	const projectId = $derived(page.params.id ?? '');
	const statuses: ProjectStatus[] = ['ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED'];

	$effect(() => {
		const source = data;
		let active = true;
		project = source.cached;
		loading = !source.cached;
		error = '';
		notFound = false;

		source.fresh.then((result) => {
			if (!active) return;
			if (result.data) {
				project = result.data;
				error = '';
			} else {
				const message = result.error ?? 'Could not load project';
				if (message.toLowerCase().includes('not found')) notFound = true;
				else error = message;
			}
			loading = false;
		});
		return () => {
			active = false;
		};
	});

	const branches = $derived(project ? eventBranches(project.recent_events) : []);
	const commits = $derived(
		project?.recent_events.filter((event) => event.event_type === 'commit').length ?? 0
	);
	const visibleEvents = $derived(
		!project
			? []
			: branchFilter === 'ALL'
				? project.recent_events
				: project.recent_events.filter((event) => eventBranch(event.payload) === branchFilter)
	);

	async function load(id: string) {
		loading = !project;
		error = '';
		notFound = false;
		try {
			const fresh = await fetchProject(id);
			project = fresh;
			writeCache(`/projects/${id}`, fresh);
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

	async function changeStatus(next: ProjectStatus) {
		if (!project || next === project.status) return;
		updatingStatus = true;
		actionError = '';
		try {
			const updated = await updateProject(project.id, { status: next });
			project = { ...project, ...updated };
			writeCache(`/projects/${project.id}`, project);
			toast.show(`Status updated to ${next.toLowerCase()}`);
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
			project = {
				...project,
				latest_summary: summary,
				summary_count: project.summary_count + 1
			};
			writeCache(`/projects/${project.id}`, project);
			toast.show('Summary generated');
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
	<a
		href="/projects"
		class="inline-flex w-fit items-center gap-1.5 text-xs font-medium text-muted transition hover:text-text"
	>
		<Icon name="arrow-left" size={14} /> All projects
	</a>

	{#if loading}
		<div class="card p-6">
			<div class="skeleton h-8 w-1/3"></div>
			<div class="skeleton mt-3 h-4 w-2/3"></div>
		</div>
		<div class="card grid grid-cols-2 gap-px overflow-hidden bg-border sm:grid-cols-4">
			{#each Array(4) as _}
				<div class="bg-surface p-4"><div class="skeleton h-3 w-16"></div><div class="skeleton mt-3 h-6 w-24"></div></div>
			{/each}
		</div>
		<div class="card h-40 p-6"><div class="skeleton h-4 w-32"></div></div>
		<div class="card h-96 p-6"><div class="skeleton h-4 w-24"></div></div>
	{:else if notFound}
		<EmptyState
			icon="folder"
			title="Project not found"
			description="It may have been deleted or belongs to another account."
		>
			<a href="/projects" class="btn-secondary">Back to projects</a>
		</EmptyState>
	{:else if error}
		<div class="card flex flex-col items-center gap-3 p-10 text-center">
			<Icon name="alert" size={24} class="text-warning" />
			<p class="text-sm text-muted">{error}</p>
			<button class="btn-secondary" onclick={() => load(projectId)}>
				<Icon name="refresh" size={15} /> Retry
			</button>
		</div>
	{:else if project}
		<PageHeader
			title={project.name}
			subtitle={project.description ??
				`Started ${formatDate(project.started_at)} · Last active ${relativeTime(project.last_activity_at)}`}
		>
			<StatusBadge status={project.status} />
			<button
				class="btn-icon text-muted hover:text-danger"
				onclick={remove}
				aria-label="Delete project"
			>
				<Icon name="trash" size={16} />
			</button>
		</PageHeader>

		<!-- Status switcher -->
		<div class="flex flex-wrap items-center gap-2">
			<div
				class="inline-flex max-w-full overflow-x-auto rounded-control border border-border bg-surface p-0.5"
				role="group"
				aria-label="Project status"
			>
				{#each statuses as status}
					<button
						type="button"
						class="inline-flex min-h-11 shrink-0 items-center justify-center rounded-[6px] px-3 text-xs font-medium transition {project.status ===
						status
							? 'bg-raised text-text'
							: 'text-muted hover:text-text'}"
						aria-pressed={project.status === status}
						disabled={updatingStatus}
						onclick={() => changeStatus(status)}
					>
						{status.charAt(0) + status.slice(1).toLowerCase()}
					</button>
				{/each}
			</div>
			{#if updatingStatus}
				<span class="text-xs text-muted">Updating…</span>
			{/if}
		</div>

		{#if actionError}
			<p class="text-xs text-danger">{actionError}</p>
		{/if}

		<!-- Stats -->
		<div class="card grid grid-cols-2 gap-px overflow-hidden bg-border sm:grid-cols-4">
			<div class="bg-surface px-4 py-4">
				<p class="text-xs text-muted">Started</p>
				<p class="mt-1.5 text-base font-semibold text-text">{formatDate(project.started_at)}</p>
				<p class="mt-0.5 text-xs text-muted">{daysSince(project.started_at)} days ago</p>
			</div>
			<div class="bg-surface px-4 py-4">
				<p class="text-xs text-muted">Last active</p>
				<p class="mt-1.5 text-base font-semibold text-text">
					{relativeTime(project.last_activity_at)}
				</p>
				<p class="mt-0.5 text-xs text-muted">Latest Git event</p>
			</div>
			<div class="bg-surface px-4 py-4">
				<p class="text-xs text-muted">Commits</p>
				<p class="mt-1.5 text-base font-semibold text-text">{commits}</p>
				<p class="mt-0.5 text-xs text-muted">In recent events</p>
			</div>
			<div class="bg-surface px-4 py-4">
				<p class="text-xs text-muted">Branches</p>
				<p class="mt-1.5 text-base font-semibold text-text">{branches.length}</p>
				<p class="mt-0.5 text-xs text-muted">In recent events</p>
			</div>
		</div>

		<!-- AI memory -->
		<section class="card p-6">
			<div class="flex flex-wrap items-start justify-between gap-3">
				<div>
					<p class="eyebrow">Project memory</p>
					<h2 class="mt-1 text-base font-semibold text-text">Latest summary</h2>
				</div>
				<button class="btn-secondary" onclick={summarise} disabled={generating}>
					{#if generating}
						<span
							class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-border border-t-accent"
						></span>
					{:else}
						<Icon name="sparkles" size={14} />
					{/if}
					{generating ? 'Generating…' : 'Generate summary'}
				</button>
			</div>

			{#if project.latest_summary}
				<p class="mt-4 text-sm leading-relaxed text-text">{project.latest_summary.summary}</p>
				<p class="mt-3 text-xs text-muted">
					{relativeTime(project.latest_summary.created_at)} · {project.summary_count} {project.summary_count ===
					1
						? 'summary'
						: 'summaries'}
				</p>
			{:else}
				<div class="mt-4 rounded-control border border-dashed border-border px-4 py-8 text-center">
					<p class="text-sm text-muted">No summary yet.</p>
					<p class="mt-1 text-xs text-muted">
						Generate one to turn this project's commits and branches into a short memory.
					</p>
				</div>
			{/if}
		</section>

		<!-- Timeline -->
		<section class="card p-6">
			<div class="flex flex-wrap items-center justify-between gap-3">
				<div>
					<p class="eyebrow">Timeline</p>
					<h2 class="mt-1 text-base font-semibold text-text">Recent activity</h2>
				</div>
				<span class="text-xs text-muted">{visibleEvents.length} events</span>
			</div>

			{#if branches.length > 0}
				<div class="mt-4 flex flex-wrap gap-1.5" role="group" aria-label="Filter by branch">
					<button
						class="chip {branchFilter === 'ALL' ? 'chip-active' : ''}"
						aria-pressed={branchFilter === 'ALL'}
						onclick={() => (branchFilter = 'ALL')}
					>
						All branches
					</button>
					{#each branches as branch}
						<button
							class="chip font-mono {branchFilter === branch ? 'chip-active' : ''}"
							aria-pressed={branchFilter === branch}
							onclick={() => (branchFilter = branch)}
						>
							<Icon name="branch" size={11} />{branch}
						</button>
					{/each}
				</div>
			{/if}

			<div class="mt-5">
				<Timeline
					events={visibleEvents}
					emptyText={branchFilter === 'ALL'
						? 'No events yet. Install the agent to start the timeline.'
						: 'No events on this branch in the recent timeline.'}
				/>
			</div>
		</section>

		<!-- Repositories -->
		<section class="card p-6">
			<div class="flex items-center justify-between">
				<div>
					<p class="eyebrow">Repositories</p>
					<h2 class="mt-1 text-base font-semibold text-text">Connected folders</h2>
				</div>
				<span class="text-xs text-muted">{project.repositories.length}</span>
			</div>
			<div class="mt-4 divide-y divide-border">
				{#each project.repositories as repo (repo.id)}
					<div class="flex items-center justify-between gap-3 py-3">
						<div class="flex min-w-0 items-center gap-3">
							<span class="grid h-8 w-8 shrink-0 place-items-center rounded-control border border-border bg-raised text-muted">
								<Icon name="folder" size={14} />
							</span>
							<div class="min-w-0">
								<p class="truncate text-sm font-medium text-text">{repo.name}</p>
								<p class="truncate font-mono text-[11px] text-muted" title={repo.local_identifier}>
									{repo.local_identifier}
								</p>
							</div>
						</div>
						{#if repo.remote_url}
							<a
								href={repo.remote_url}
								target="_blank"
								rel="noreferrer"
								class="inline-flex min-h-11 items-center gap-1 text-xs text-muted transition hover:text-accent"
							>
								Remote <Icon name="external" size={12} />
							</a>
						{/if}
					</div>
				{:else}
					<p class="py-6 text-center text-sm text-muted">No repositories linked.</p>
				{/each}
			</div>
		</section>
	{/if}
</div>
