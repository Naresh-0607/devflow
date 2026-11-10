<script lang="ts">
	import { eventMeta, shortHash } from '#lib/events';
	import { eventBranch, eventTitle, formatDateTime, relativeTime } from '#lib/format';
	import type { GitEvent } from '#lib/types';
	import Icon from './Icon.svelte';

	let {
		events,
		showProject = false,
		emptyText = 'No events yet. Install the agent to start the timeline.'
	}: { events: GitEvent[]; showProject?: boolean; emptyText?: string } = $props();

	function dayLabel(date: Date): string {
		const today = new Date();
		const midnight = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
		const target = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
		const days = Math.round((midnight - target) / 86400000);
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		const weekday = date.toLocaleDateString(undefined, { weekday: 'short' });
		const month = date.toLocaleDateString(undefined, { month: 'short' });
		return `${weekday} ${date.getDate()} ${month}`;
	}

	const groups = $derived.by(() => {
		const map = new Map<string, { label: string; events: GitEvent[] }>();
		for (const event of events) {
			const date = new Date(event.created_at);
			const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
			const group = map.get(key) ?? { label: dayLabel(date), events: [] };
			group.events.push(event);
			map.set(key, group);
		}
		return [...map.values()];
	});
</script>

{#if events.length === 0}
	<div class="rounded-control border border-dashed border-border px-4 py-10 text-center">
		<p class="text-sm text-muted">{emptyText}</p>
	</div>
{:else}
	<div class="space-y-7">
		{#each groups as group}
			<section>
				<div class="mb-3 flex items-center gap-3">
					<h3 class="eyebrow">{group.label}</h3>
					<span class="h-px flex-1 bg-border"></span>
					<span class="text-xs text-muted">{group.events.length}</span>
				</div>
				<ol>
					{#each group.events as event, index (event.id)}
						{@const meta = eventMeta(event.event_type)}
						{@const branch = eventBranch(event.payload)}
						{@const hash = shortHash(event.payload)}
						<li class="relative flex gap-3 pb-5 last:pb-0">
							{#if index < group.events.length - 1}
								<span
									class="absolute bottom-0 left-[13px] top-8 w-px bg-border"
									aria-hidden="true"
								></span>
							{/if}
							<span
								class="relative z-10 grid h-7 w-7 shrink-0 place-items-center rounded-[6px] border {meta.tone}"
							>
								<Icon name={meta.icon} size={13} />
							</span>
							<div class="min-w-0 flex-1 pt-0.5">
								<div class="flex items-start justify-between gap-3">
									<div class="flex min-w-0 items-start gap-2">
										<span
											class="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full {meta.dot}"
											aria-hidden="true"
										></span>
										<p class="min-w-0 text-sm font-medium leading-snug text-text">
											{eventTitle(event.event_type, event.payload)}
										</p>
									</div>
									<time
										class="shrink-0 text-xs text-muted"
										datetime={event.created_at}
										title={formatDateTime(event.created_at)}
									>
										{relativeTime(event.created_at)}
									</time>
								</div>
								<div class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 pl-3.5 text-xs text-muted">
									{#if showProject && event.project_name}
										<span class="text-muted">{event.project_name}</span>
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
						</li>
					{/each}
				</ol>
			</section>
		{/each}
	</div>
{/if}
