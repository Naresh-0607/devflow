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
			<div class="flex items-start gap-2 rounded-control border border-danger/30 bg-danger/10 px-3 py-2.5 text-xs text-danger">
				<Icon name="alert" size={14} class="mt-0.5 shrink-0" />{error}
			</div>
		{/if}

		<button type="submit" class="btn-primary w-full" disabled={loading}>
			{#if loading}<span class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>{/if}
			{loading ? 'Creating account…' : 'Create account'}
		</button>
	</form>

	<p class="mt-6 text-center text-sm text-muted">
		Already have an account?
		<a href="/login" class="font-medium text-accent hover:text-accent-hover">Sign in</a>
	</p>
</AuthShell>
