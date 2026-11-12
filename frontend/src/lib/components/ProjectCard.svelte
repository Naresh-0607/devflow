<script lang="ts">
	import { daysSince, formatDate, relativeTime } from '#lib/format';
	import type { Project } from '#lib/types';
	import Icon from './Icon.svelte';
	import StatusBadge from './StatusBadge.svelte';

	let { project }: { project: Project } = $props();
</script>

<a
	href="/projects/{project.id}"
	class="card group block p-5 transition duration-150 hover:border-muted/60"
	aria-label="Open {project.name}"
>
	<div class="flex items-start justify-between gap-3">
		<div class="flex min-w-0 items-center gap-3">
			<span
				class="grid h-9 w-9 shrink-0 place-items-center rounded-control border border-border bg-raised text-muted transition group-hover:text-text"
			>
				<Icon name="folder" size={16} />
			</span>
			<div class="min-w-0">
				<h3 class="truncate text-sm font-semibold text-text">{project.name}</h3>
				<p class="mt-0.5 text-xs text-muted">
					Started {formatDate(project.started_at)} · {daysSince(project.started_at)} days
				</p>
			</div>
		</div>
		<StatusBadge status={project.status} />
	</div>

	{#if project.description}
		<p class="mt-3 line-clamp-2 text-sm leading-relaxed text-muted">{project.description}</p>
	{/if}

	<div class="mt-4 grid grid-cols-2 gap-2 border-t border-border pt-3 text-xs text-muted">
		<span class="inline-flex items-center gap-1.5">
			<Icon name="clock" size={12} />
			{relativeTime(project.last_activity_at)}
		</span>
		<span class="inline-flex items-center justify-end gap-1.5">
			<Icon name="folder" size={12} />
			{project.repository_count} {project.repository_count === 1 ? 'repo' : 'repos'}
		</span>
	</div>
</a>
