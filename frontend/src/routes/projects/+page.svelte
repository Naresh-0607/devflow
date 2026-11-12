<script lang="ts">
	import { createProject, fetchProjects, writeCache } from '#lib/api';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import ProjectCard from '#lib/components/ProjectCard.svelte';
	import type { SwrResult } from '#lib/load';
	import type { Project, ProjectStatus } from '#lib/types';

	let { data }: { data: SwrResult<Project[]> } = $props();

	// svelte-ignore state_referenced_locally
	let projects = $state<Project[]>(data.cached ?? []);
	// svelte-ignore state_referenced_locally
	let loading = $state(!data.cached);
	let error = $state('');
	let query = $state('');
	let statusFilter = $state<'ALL' | ProjectStatus>('ALL');

	let showCreate = $state(false);
	let newName = $state('');
	let newDescription = $state('');
	let creating = $state(false);
	let createError = $state('');

	const filters: Array<'ALL' | ProjectStatus> = ['ALL', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED'];

	const visible = $derived(
		projects.filter((project) => {
			const matchesQuery =
				!query.trim() ||
				project.name.toLowerCase().includes(query.toLowerCase()) ||
				(project.description ?? '').toLowerCase().includes(query.toLowerCase());
			const matchesStatus = statusFilter === 'ALL' || project.status === statusFilter;
			return matchesQuery && matchesStatus;
		})
	);

	$effect(() => {
		let active = true;
		data.fresh.then((result) => {
			if (!active) return;
			if (result.data) {
				projects = result.data;
				error = '';
			} else {
				error = result.error ?? 'Could not load projects';
			}
			loading = false;
		});
		return () => {
			active = false;
		};
	});

	async function load() {
		loading = !projects.length;
		error = '';
		try {
			projects = await fetchProjects();
			writeCache('/projects', projects);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load projects';
		} finally {
			loading = false;
		}
	}

	async function submitCreate() {
		if (!newName.trim()) return;
		creating = true;
		createError = '';
		try {
			const project = await createProject({
				name: newName.trim(),
				description: newDescription.trim() || undefined
			});
			projects = [project, ...projects];
			writeCache('/projects', projects);
			showCreate = false;
			newName = '';
			newDescription = '';
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Could not create project';
		} finally {
			creating = false;
		}
	}

	function filterLabel(filter: 'ALL' | ProjectStatus) {
		return filter === 'ALL' ? 'All' : filter.charAt(0) + filter.slice(1).toLowerCase();
	}
</script>

<svelte:head><title>Projects — DevFlow</title></svelte:head>

<div class="flex flex-col gap-8">
	<PageHeader
		title="Projects"
		subtitle="All tracked projects."
	>
		<button class="btn-primary" onclick={() => (showCreate = true)}>
			<Icon name="plus" size={16} /> New project
		</button>
	</PageHeader>

	<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
		<div class="relative flex-1">
			<Icon
				name="search"
				size={16}
				class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
			/>
			<label class="sr-only" for="project-search">Search projects</label>
			<input
				id="project-search"
				class="input pl-9"
				placeholder="Search projects…"
				bind:value={query}
			/>
		</div>
		<div class="flex gap-1.5 overflow-x-auto pb-1">
			{#each filters as filter}
				<button
					class="chip shrink-0 {statusFilter === filter ? 'chip-active' : ''}"
					aria-pressed={statusFilter === filter}
					onclick={() => (statusFilter = filter)}
				>
					{filterLabel(filter)}
				</button>
			{/each}
		</div>
	</div>

	{#if loading}
		<div class="grid gap-3 sm:grid-cols-2">
			{#each Array(4) as _}
				<div class="card h-36 p-5">
					<div class="flex items-center gap-3">
						<div class="skeleton h-9 w-9"></div>
						<div class="flex-1">
							<div class="skeleton h-3.5 w-1/2"></div>
							<div class="skeleton mt-2 h-3 w-2/3"></div>
						</div>
					</div>
					<div class="skeleton mt-5 h-3 w-full"></div>
				</div>
			{/each}
		</div>
	{:else if error}
		<div class="card flex flex-col items-center gap-3 p-10 text-center">
			<Icon name="alert" size={24} class="text-warning" />
			<p class="text-sm text-muted">{error}</p>
			<button class="btn-secondary" onclick={load}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if projects.length === 0}
		<EmptyState
			icon="folder-plus"
			title="No projects yet"
			description="Projects appear automatically when your agent reports its first Git event. Connect your laptop to start the timeline."
		>
			<a href="/settings" class="btn-primary"><Icon name="key" size={15} /> Connect your laptop</a>
			<button class="btn-secondary" onclick={() => (showCreate = true)}>
				<Icon name="plus" size={15} /> New project
			</button>
		</EmptyState>
	{:else if visible.length === 0}
		<div class="card px-6 py-14 text-center">
			<p class="text-sm text-muted">No projects match “{query || filterLabel(statusFilter)}”.</p>
			<button
				class="btn-ghost mt-3 text-xs"
				onclick={() => {
					query = '';
					statusFilter = 'ALL';
				}}
			>
				Clear filters
			</button>
		</div>
	{:else}
		<div class="grid gap-3 sm:grid-cols-2">
			{#each visible as project (project.id)}
				<ProjectCard {project} />
			{/each}
		</div>
	{/if}
</div>

{#if showCreate}
	<div
		class="fixed inset-0 z-50 grid place-items-center bg-black/50 px-4 backdrop-blur-sm"
		role="presentation"
		onclick={(event) => {
			if (event.target === event.currentTarget) showCreate = false;
		}}
	>
		<div
			class="card w-full max-w-md p-6"
			role="dialog"
			aria-modal="true"
			aria-labelledby="new-project-title"
		>
			<div class="flex items-start justify-between gap-3">
				<div>
					<h2 id="new-project-title" class="text-xl font-semibold text-text">New project</h2>
					<p class="mt-1 text-sm text-muted">Repositories can be linked later.</p>
				</div>
				<button
					class="btn-icon -mr-2 -mt-1"
					onclick={() => (showCreate = false)}
					aria-label="Close"
				>
					<Icon name="x" size={17} />
				</button>
			</div>
			<form
				class="mt-6 space-y-4"
				onsubmit={(event) => {
					event.preventDefault();
					submitCreate();
				}}
			>
				<div>
					<label class="label" for="project-name">Name</label>
					<input
						id="project-name"
						class="input"
						placeholder="e.g. Jarvis"
						bind:value={newName}
						required
						maxlength="160"
					/>
				</div>
				<div>
					<label class="label" for="project-description">
						Description <span class="text-muted">(optional)</span>
					</label>
					<textarea
						id="project-description"
						class="input min-h-24 resize-y"
						placeholder="What is this project about?"
						bind:value={newDescription}
					></textarea>
				</div>
				{#if createError}
					<p class="text-xs text-danger">{createError}</p>
				{/if}
				<div class="flex justify-end gap-2 pt-1">
					<button type="button" class="btn-ghost" onclick={() => (showCreate = false)}>
						Cancel
					</button>
					<button type="submit" class="btn-primary" disabled={creating}>
						{creating ? 'Creating…' : 'Create project'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
