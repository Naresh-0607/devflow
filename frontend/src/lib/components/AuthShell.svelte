<script lang="ts">
	import Icon from './Icon.svelte';
	import Logo from './Logo.svelte';
	import type { Snippet } from 'svelte';

	let {
		title,
		subtitle,
		children
	}: { title: string; subtitle: string; children: Snippet } = $props();
</script>

<div class="grid min-h-dvh lg:grid-cols-2">
	<!-- Brand panel -->
	<div class="relative hidden overflow-hidden border-r border-white/6 bg-ink-900 lg:flex lg:flex-col lg:justify-between lg:p-12">
		<div class="pointer-events-none absolute -left-32 top-1/4 h-96 w-96 rounded-full bg-mint-400/8 blur-3xl"></div>
		<div class="pointer-events-none absolute -right-24 bottom-0 h-80 w-80 rounded-full bg-iris-500/10 blur-3xl"></div>

		<div class="relative"><Logo size={36} /></div>

		<div class="relative max-w-md">
			<p class="text-xs font-semibold uppercase tracking-[0.24em] text-mint-400/80">Developer memory</p>
			<h2 class="mt-4 text-4xl font-semibold leading-[1.15] tracking-tight text-zinc-50">
				You code.<br /><span class="text-mint-300">DevFlow remembers.</span>
			</h2>
			<p class="mt-4 text-sm leading-relaxed text-zinc-400">
				Your commits, branches and pushes become a searchable timeline — and a story you can
				read from anywhere.
			</p>

			<div class="mt-10 space-y-4">
				{#each [{ icon: 'commit', text: 'Captures commits automatically' }, { icon: 'branch', text: 'Tracks your focus across branches' }, { icon: 'sparkles', text: 'Turns activity into AI summaries' }] as item}
					<div class="flex items-center gap-3">
						<span class="grid h-8 w-8 place-items-center rounded-lg bg-white/5 text-mint-300 ring-1 ring-inset ring-white/10">
							<Icon name={item.icon} size={15} />
						</span>
						<span class="text-sm text-zinc-400">{item.text}</span>
					</div>
				{/each}
			</div>
		</div>

		<p class="relative text-[11px] text-zinc-600">
			No keyboard tracking. No screen time. Just Git events, remembered.
		</p>
	</div>

	<!-- Form panel -->
	<div class="relative flex flex-col justify-center px-5 py-10 sm:px-10">
		<div class="pointer-events-none absolute inset-x-0 top-0 h-64 bg-[radial-gradient(60%_100%_at_50%_0%,rgba(79,224,173,0.06),transparent_70%)] lg:hidden"></div>
		<div class="relative mx-auto w-full max-w-sm">
			<div class="mb-8 lg:hidden"><Logo size={32} /></div>
			<h1 class="text-2xl font-semibold tracking-tight text-zinc-50">{title}</h1>
			<p class="mt-1.5 text-sm text-zinc-500">{subtitle}</p>
			<div class="mt-8">{@render children()}</div>
		</div>
	</div>
</div>
