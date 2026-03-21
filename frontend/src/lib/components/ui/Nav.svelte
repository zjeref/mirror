<script lang="ts">
	import { page } from '$app/state';
	import { user } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	function logout() {
		user.logout();
		goto('/login');
	}

	const links = [
		{ href: '/chat', label: 'Chat' },
		{ href: '/dashboard', label: 'Dashboard' },
	];
</script>

<nav class="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
	<div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
		<div class="flex items-center gap-6">
			<a href="/chat" class="text-lg font-semibold text-indigo-400">Mirror</a>
			{#each links as link}
				<a
					href={link.href}
					class="text-sm transition-colors {page.url.pathname.startsWith(link.href)
						? 'text-white'
						: 'text-slate-400 hover:text-white'}"
				>
					{link.label}
				</a>
			{/each}
		</div>

		{#if $user}
			<div class="flex items-center gap-4">
				<span class="text-sm text-slate-400">{$user.name}</span>
				<button onclick={logout} class="text-sm text-slate-500 hover:text-slate-300 transition-colors">
					Logout
				</button>
			</div>
		{/if}
	</div>
</nav>
