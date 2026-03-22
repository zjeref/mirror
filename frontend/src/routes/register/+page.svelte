<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client';
	import { user } from '$lib/stores/auth';

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;

		try {
			await api.register(email, name, password);
			user.login({ email, name });
			goto('/chat');
		} catch (err: any) {
			error = err.message || 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="h-full flex items-center justify-center px-4 bg-gradient-to-b from-[var(--color-surface)] to-[#0c0c1f]">
	<!-- Ambient glow -->
	<div class="fixed top-[20%] left-[40%] w-[30rem] h-[30rem] bg-[#6c5ce7]/8 rounded-full blur-[120px] pointer-events-none"></div>
	<div class="fixed bottom-[20%] right-[30%] w-[20rem] h-[20rem] bg-[#edbf7c]/5 rounded-full blur-[100px] pointer-events-none"></div>

	<div class="w-full max-w-sm relative z-10">
		<div class="text-center mb-10">
			<span class="material-symbols-outlined filled text-4xl text-[var(--color-primary)] mb-3 block">auto_awesome</span>
			<h1 class="text-3xl font-bold bg-gradient-to-br from-indigo-300 to-indigo-500 bg-clip-text text-transparent mb-2">Mirror</h1>
			<p class="text-[var(--color-on-surface-variant)]/60 text-sm">Start your growth journey</p>
		</div>

		<form onsubmit={handleSubmit} class="space-y-4">
			{#if error}
				<div class="glass-card rounded-xl p-3 border-[var(--color-error)]/20">
					<p class="text-[var(--color-error)] text-sm">{error}</p>
				</div>
			{/if}

			<div>
				<label for="name" class="block text-xs text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Name</label>
				<input
					id="name"
					type="text"
					bind:value={name}
					required
					class="w-full bg-[var(--color-surface-low)] border border-[var(--color-outline-variant)]/20
						rounded-xl px-4 py-3 text-sm text-[var(--color-on-surface)] focus:border-[var(--color-primary)]/50 focus:outline-none
						placeholder-[var(--color-outline)]/50 transition-colors"
					placeholder="What should Mirror call you?"
				/>
			</div>

			<div>
				<label for="email" class="block text-xs text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					required
					class="w-full bg-[var(--color-surface-low)] border border-[var(--color-outline-variant)]/20
						rounded-xl px-4 py-3 text-sm text-[var(--color-on-surface)] focus:border-[var(--color-primary)]/50 focus:outline-none
						placeholder-[var(--color-outline)]/50 transition-colors"
					placeholder="you@example.com"
				/>
			</div>

			<div>
				<label for="password" class="block text-xs text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					required
					minlength={6}
					class="w-full bg-[var(--color-surface-low)] border border-[var(--color-outline-variant)]/20
						rounded-xl px-4 py-3 text-sm text-[var(--color-on-surface)] focus:border-[var(--color-primary)]/50 focus:outline-none
						placeholder-[var(--color-outline)]/50 transition-colors"
					placeholder="At least 6 characters"
				/>
			</div>

			<button
				type="submit"
				disabled={loading}
				class="w-full bg-[var(--color-tertiary)] text-[#442c00] font-semibold rounded-full py-3 text-sm
					hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-[var(--color-tertiary)]/20
					disabled:opacity-50 disabled:cursor-not-allowed mt-6"
			>
				{loading ? 'Creating account...' : 'Begin your journey'}
			</button>

			<p class="text-center text-sm text-[var(--color-outline)]">
				Already have an account?
				<a href="/login" class="text-[var(--color-primary)] hover:text-[var(--color-tertiary)] transition-colors">Sign in</a>
			</p>

			<p class="text-center text-[10px] text-[var(--color-outline)]/40 mt-6">
				Mirror is a companion, not a therapist. For crisis support, call 988.
			</p>
		</form>
	</div>
</div>
