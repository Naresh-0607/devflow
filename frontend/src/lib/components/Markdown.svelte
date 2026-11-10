<script lang="ts">
	let { source }: { source: string } = $props();

	let html = $state('');

	// The renderer is a separate chunk; it only loads once a message finishes.
	$effect(() => {
		const text = source;
		let active = true;
		import('#lib/markdown')
			.then(({ renderMarkdown }) => {
				if (active) html = renderMarkdown(text);
			})
			.catch(() => {
				/* fall back to plain text below */
			});
		return () => {
			active = false;
		};
	});
</script>

{#if html}
	<div class="chat-markdown">{@html html}</div>
{:else}
	<p class="whitespace-pre-wrap text-sm leading-relaxed text-text">{source}</p>
{/if}
