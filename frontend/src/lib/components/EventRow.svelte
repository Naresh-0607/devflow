<script lang="ts">
	import { eventMeta, shortHash } from '#lib/events';
	import { eventBranch, eventTitle, relativeTime } from '#lib/format';
	import type { GitEvent } from '#lib/types';
	import Icon from './Icon.svelte';

	let { event, showProject = false }: { event: GitEvent; showProject?: boolean } = $props();

	const meta = $derived(eventMeta(event.event_type));
	const branch = $derived(eventBranch(event.payload));
	const hash = $derived(shortHash(event.payload));
</script>

<div class="flex gap-3 py-3">
	<span
		class="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-[6px] border {meta.tone}"
	>
		<Icon name={meta.icon} size={13} />
	</span>
	<div class="min-w-0 flex-1">
		<div class="flex items-start justify-between gap-3">
			<p class="truncate text-sm text-text">{eventTitle(event.event_type, event.payload)}</p>
			<time class="shrink-0 text-xs text-muted" datetime={event.created_at}>
				{relativeTime(event.created_at)}
			</time>
		</div>
		<div class="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted">
			{#if showProject && event.project_name}
				<span class="truncate text-muted">{event.project_name}</span>
				<span aria-hidden="true">·</span>
			{/if}
			{#if branch}
				<span class="inline-flex items-center gap-1 font-mono text-[11px]">
					<Icon name="branch" size={10} />{branch}
				</span>
				<span aria-hidden="true">·</span>
			{/if}
			{#if hash}
				<span class="font-mono text-[11px]">{hash}</span>
				<span aria-hidden="true">·</span>
			{/if}
			<span class="truncate font-mono text-[11px] text-muted/80">
				{event.repository_name ?? 'repository'}
			</span>
		</div>
	</div>
</div>
