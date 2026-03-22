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

<!-- Desktop sidebar (hidden on mobile) -->
<aside class="hidden md:flex h-full w-20 flex-col items-center py-8 bg-gradient-to-b from-[#111125] to-[#0c0c1f] border-r border-[var(--color-outline-variant)]/10 z-40">
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

	<!-- Logout -->
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

<!-- Mobile bottom bar (hidden on desktop) -->
<nav class="md:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around
	bg-[#111125]/95 backdrop-blur-xl border-t border-[var(--color-outline-variant)]/10
	px-4 py-2 safe-area-bottom">
	{#each links as link}
		{@const isActive = page.url.pathname.startsWith(link.href)}
		<a
			href={link.href}
			class="flex flex-col items-center gap-0.5 py-1 px-3 transition-all duration-200"
		>
			<div class="flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200
				{isActive
					? 'bg-[var(--color-primary-container)]/20 text-[var(--color-tertiary)]'
					: 'text-[var(--color-outline)]'}"
			>
				<span class="material-symbols-outlined text-[22px] {isActive ? 'filled' : ''}">{link.icon}</span>
			</div>
			<span class="text-[10px] font-medium
				{isActive ? 'text-[var(--color-tertiary)]' : 'text-[var(--color-outline)]'}">
				{link.label}
			</span>
		</a>
	{/each}
	<button
		onclick={logout}
		class="flex flex-col items-center gap-0.5 py-1 px-3"
	>
		<div class="flex items-center justify-center w-10 h-10 rounded-xl text-[var(--color-outline)]">
			<span class="material-symbols-outlined text-[22px]">logout</span>
		</div>
		<span class="text-[10px] font-medium text-[var(--color-outline)]">Logout</span>
	</button>
</nav>
