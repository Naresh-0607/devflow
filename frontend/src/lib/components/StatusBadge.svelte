<script lang="ts">
	import { statusStyle } from '#lib/format';

	let { status }: { status: string } = $props();
</script>

<span class="pill {statusStyle(status)}">
	<span class="h-1.5 w-1.5 rounded-full bg-current"></span>
	{status.charAt(0) + status.slice(1).toLowerCase()}
</span>
