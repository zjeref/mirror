<script lang="ts">
	import { page } from '$app/state';
	import { user } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	function logout() {
		user.logout();
		goto('/login');
	}

	const links = [
		{ href: '/chat', icon: 'chat_bubble', label: 'Chat' },
		{ href: '/journal', icon: 'book_5', label: 'Journal' },
		{ href: '/dashboard', icon: 'dashboard', label: 'Dashboard' },
	];
</script>

<aside class="h-full w-20 flex flex-col items-center py-8 bg-gradient-to-b from-[#111125] to-[#0c0c1f] border-r border-[var(--color-outline-variant)]/10 z-40">
	<!-- Logo -->
	<div class="mb-10">
		<span class="material-symbols-outlined filled text-3xl text-[var(--color-primary)]">auto_awesome</span>
	</div>

	<!-- Nav links -->
	<nav class="flex flex-col gap-6 flex-1">
		{#each links as link}
			{@const isActive = page.url.pathname.startsWith(link.href)}
			<a
				href={link.href}
				class="group flex flex-col items-center gap-1 transition-all duration-300"
				title={link.label}
			>
				<div class="flex items-center justify-center w-12 h-12 rounded-2xl transition-all duration-300
					{isActive
						? 'bg-[var(--color-primary-container)]/20 text-[var(--color-tertiary)]'
						: 'text-[var(--color-outline)] hover:text-[var(--color-primary)] hover:scale-110'}"
				>
					<span class="material-symbols-outlined {isActive ? 'filled' : ''}">{link.icon}</span>
				</div>
				<span class="text-[10px] font-medium tracking-wide
					{isActive ? 'text-[var(--color-tertiary)]' : 'text-[var(--color-outline)] group-hover:text-[var(--color-primary)]'}">
					{link.label}
				</span>
			</a>
		{/each}
	</nav>

	<!-- User avatar / logout -->
	<div class="mt-auto flex flex-col items-center gap-3">
		<button
			onclick={logout}
			class="flex items-center justify-center w-10 h-10 rounded-full bg-[var(--color-surface-high)] text-[var(--color-outline)] hover:text-[var(--color-error)] transition-colors"
			title="Logout"
		>
			<span class="material-symbols-outlined text-xl">logout</span>
		</button>
	</div>
</aside>
