<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { user } from '$lib/stores/auth';
	import Button from '$lib/components/ui/Button.svelte';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;

		try {
			await api.login(email, password);
			user.login({ email, name: email.split('@')[0] });
			goto('/chat');
		} catch (err: any) {
			error = err.message || 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="h-full flex items-center justify-center px-4">
	<div class="w-full max-w-sm">
		<div class="text-center mb-8">
			<h1 class="text-3xl font-bold text-indigo-400 mb-2">Mirror</h1>
			<p class="text-slate-400 text-sm">Your personal growth companion</p>
		</div>

		<form onsubmit={handleSubmit} class="space-y-4">
			{#if error}
				<div class="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-2">
					{error}
				</div>
			{/if}

			<div>
				<label for="email" class="block text-sm text-slate-400 mb-1">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					required
					class="w-full bg-[var(--color-surface-light)] border border-[var(--color-border)]
						rounded-lg px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none"
					placeholder="you@example.com"
				/>
			</div>

			<div>
				<label for="password" class="block text-sm text-slate-400 mb-1">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					required
					class="w-full bg-[var(--color-surface-light)] border border-[var(--color-border)]
						rounded-lg px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none"
					placeholder="Your password"
				/>
			</div>

			<Button type="submit" variant="primary" size="lg" disabled={loading}>
				{loading ? 'Signing in...' : 'Sign in'}
			</Button>

			<p class="text-center text-sm text-slate-500">
				Don't have an account?
				<a href="/register" class="text-indigo-400 hover:text-indigo-300">Sign up</a>
			</p>
		</form>
	</div>
</div>
