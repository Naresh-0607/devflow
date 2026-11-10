<script lang="ts">
	import { createProject, fetchProjects, writeCache } from '#lib/api';
	import Icon from '#lib/components/Icon.svelte';
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

</script>

<svelte:head><title>Projects — DevFlow</title></svelte:head>

<div class="flex flex-col gap-6">
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div>
			<p class="text-xs font-medium uppercase tracking-[0.2em] text-mint-400/80">Memory index</p>
			<h1 class="mt-1.5 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">Projects</h1>
			<p class="mt-1.5 text-sm text-zinc-500">Every repository DevFlow remembers, in one place.</p>
		</div>
		<button class="btn-primary" onclick={() => (showCreate = true)}>
			<Icon name="plus" size={16} /> New project
		</button>
	</div>

	<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
		<div class="relative flex-1">
			<Icon name="search" size={16} class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
			<input class="input pl-9" placeholder="Search projects…" bind:value={query} />
		</div>
		<div class="flex gap-1.5 overflow-x-auto pb-1">
			{#each filters as filter}
				<button
					class="whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition {statusFilter === filter
						? 'bg-white/10 text-zinc-100'
						: 'text-zinc-500 hover:bg-white/5 hover:text-zinc-300'}"
					onclick={() => (statusFilter = filter)}
				>
					{filter === 'ALL' ? 'All' : filter.charAt(0) + filter.slice(1).toLowerCase()}
				</button>
			{/each}
		</div>
	</div>

	{#if loading}
		<div class="grid gap-4 sm:grid-cols-2">
			{#each Array(4) as _}
				<div class="panel h-40 p-5"><div class="skeleton h-10 w-10"></div><div class="skeleton mt-4 h-4 w-1/2"></div><div class="skeleton mt-3 h-3 w-2/3"></div></div>
			{/each}
		</div>
	{:else if error}
		<div class="panel flex flex-col items-center gap-3 p-10 text-center">
			<Icon name="alert" size={26} class="text-amber-300" />
			<p class="text-sm text-zinc-400">{error}</p>
			<button class="btn-secondary" onclick={load}><Icon name="refresh" size={15} /> Retry</button>
		</div>
	{:else if projects.length === 0}
		<div class="panel flex flex-col items-center px-6 py-16 text-center">
			<div class="grid h-12 w-12 place-items-center rounded-2xl bg-mint-400/10 text-mint-300 ring-1 ring-inset ring-mint-400/20">
				<Icon name="folder" size={22} />
			</div>
			<h2 class="mt-4 text-lg font-semibold text-zinc-100">No projects yet</h2>
			<p class="mt-1.5 max-w-sm text-sm text-zinc-500">
				Projects appear automatically when your agent reports its first Git event. You can also
				create one manually.
			</p>
			<div class="mt-5 flex gap-3">
				<button class="btn-primary" onclick={() => (showCreate = true)}><Icon name="plus" size={15} /> New project</button>
				<a href="/settings" class="btn-secondary">Connect agent</a>
			</div>
		</div>
	{:else if visible.length === 0}
		<div class="panel px-6 py-14 text-center">
			<p class="text-sm text-zinc-400">No projects match “{query || statusFilter.toLowerCase()}”.</p>
			<button class="btn-ghost mt-3 text-xs" onclick={() => { query = ''; statusFilter = 'ALL'; }}>Clear filters</button>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2">
			{#each visible as project (project.id)}
				<ProjectCard {project} />
			{/each}
		</div>
	{/if}
</div>

{#if showCreate}
	<div class="fixed inset-0 z-50 grid place-items-center bg-ink-950/80 px-4 backdrop-blur-sm" role="presentation" onclick={(event) => { if (event.target === event.currentTarget) showCreate = false; }}>
		<div class="panel w-full max-w-md p-6" role="dialog" aria-modal="true" aria-labelledby="new-project-title">
			<div class="flex items-center justify-between">
				<h2 id="new-project-title" class="text-lg font-semibold text-zinc-50">New project</h2>
				<button class="rounded-lg p-1.5 text-zinc-500 hover:bg-white/5 hover:text-zinc-200" onclick={() => (showCreate = false)} aria-label="Close">
					<Icon name="x" size={17} />
				</button>
			</div>
			<p class="mt-1 text-sm text-zinc-500">Create a memory space. Repositories can be linked later.</p>
			<form class="mt-5 space-y-4" onsubmit={(event) => { event.preventDefault(); submitCreate(); }}>
				<div>
					<label class="label" for="project-name">Name</label>
					<input id="project-name" class="input" placeholder="e.g. Jarvis" bind:value={newName} required maxlength="160" />
				</div>
				<div>
					<label class="label" for="project-description">Description <span class="normal-case text-zinc-600">(optional)</span></label>
					<textarea id="project-description" class="input min-h-24 resize-y" placeholder="What is this project about?" bind:value={newDescription}></textarea>
				</div>
				{#if createError}
					<p class="text-xs text-red-300">{createError}</p>
				{/if}
				<div class="flex justify-end gap-2 pt-1">
					<button type="button" class="btn-ghost" onclick={() => (showCreate = false)}>Cancel</button>
					<button type="submit" class="btn-primary" disabled={creating}>{creating ? 'Creating…' : 'Create project'}</button>
				</div>
			</form>
		</div>
	</div>
{/if}
