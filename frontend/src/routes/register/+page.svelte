<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '#lib/auth.svelte';
	import AuthShell from '#lib/components/AuthShell.svelte';
	import Icon from '#lib/components/Icon.svelte';

	let email = $state('');
	let password = $state('');
	let confirm = $state('');
	let error = $state('');
	let loading = $state(false);

	async function submit() {
		error = '';
		if (password.length < 8) {
			error = 'Password must be at least 8 characters.';
			return;
		}
		if (password !== confirm) {
			error = 'Passwords do not match.';
			return;
		}
		loading = true;
		try {
			await auth.register(email, password);
			await goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not create your account';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Create account — DevFlow</title></svelte:head>

<AuthShell title="Start remembering" subtitle="Create your account. Your future self will thank you.">
	<form class="space-y-4" onsubmit={(event) => { event.preventDefault(); submit(); }}>
		<div>
			<label class="label" for="email">Email</label>
			<input id="email" class="input" type="email" autocomplete="email" placeholder="you@example.com" bind:value={email} required />
		</div>
		<div>
			<label class="label" for="password">Password</label>
			<input id="password" class="input" type="password" autocomplete="new-password" placeholder="At least 8 characters" bind:value={password} required />
		</div>
		<div>
			<label class="label" for="confirm">Confirm password</label>
			<input id="confirm" class="input" type="password" autocomplete="new-password" placeholder="Repeat your password" bind:value={confirm} required />
		</div>

		{#if error}
			<div class="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/8 px-3 py-2.5 text-xs text-red-300">
				<Icon name="alert" size={14} class="mt-0.5 shrink-0" />{error}
			</div>
		{/if}

		<button type="submit" class="btn-primary w-full" disabled={loading}>
			{#if loading}<span class="h-4 w-4 animate-spin rounded-full border-2 border-ink-950/25 border-t-ink-950"></span>{/if}
			{loading ? 'Creating account…' : 'Create account'}
		</button>
	</form>

	<p class="mt-6 text-center text-sm text-zinc-500">
		Already have an account?
		<a href="/login" class="font-medium text-mint-300 hover:text-mint-200">Sign in</a>
	</p>
</AuthShell>
