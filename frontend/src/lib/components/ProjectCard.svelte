<script lang="ts">
	import { daysSince, relativeTime } from '#lib/format';
	import type { Project } from '#lib/types';
	import Icon from './Icon.svelte';
	import StatusBadge from './StatusBadge.svelte';

	let { project }: { project: Project } = $props();
</script>

<a
	href="/projects/{project.id}"
	class="panel panel-hover group block p-4 sm:p-5"
	aria-label="Open {project.name}"
>
	<div class="flex items-start justify-between gap-3">
		<div class="flex min-w-0 items-center gap-3">
			<div
				class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-iris-500/25 to-mint-400/15 text-iris-200 ring-1 ring-inset ring-white/10"
			>
				<Icon name="folder" size={18} />
			</div>
			<div class="min-w-0">
				<h3 class="truncate text-[15px] font-semibold text-zinc-100 group-hover:text-white">
					{project.name}
				</h3>
				<p class="mt-0.5 text-xs text-zinc-500">Started {daysSince(project.started_at)} days ago</p>
			</div>
		</div>
		<StatusBadge status={project.status} />
	</div>

	{#if project.description}
		<p class="mt-3 line-clamp-2 text-sm text-zinc-400">{project.description}</p>
	{/if}

	<div class="mt-4 flex items-center gap-4 border-t border-white/5 pt-3 text-[11px] text-zinc-500">
		<span class="inline-flex items-center gap-1.5">
			<Icon name="commit" size={12} />{project.event_count} events
		</span>
		<span class="inline-flex items-center gap-1.5">
			<Icon name="branch" size={12} />{project.repository_count} repos
		</span>
		<span class="ml-auto inline-flex items-center gap-1.5">
			<Icon name="clock" size={12} />{relativeTime(project.last_activity_at)}
		</span>
	</div>
</a>
