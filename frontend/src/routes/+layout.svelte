<script lang="ts">
	import '../app.css';
	import { user } from '$lib/stores/auth';
	import { page } from '$app/state';
	import Nav from '$lib/components/ui/Nav.svelte';

	let { children } = $props();

	const isAuthPage = $derived(
		page.url.pathname === '/login' || page.url.pathname === '/register'
	);
</script>

<svelte:head>
	<title>Mirror</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
</svelte:head>

<div class="h-screen flex flex-col">
	{#if !isAuthPage && $user}
		<Nav />
	{/if}
	<main class="flex-1 overflow-hidden">
		{@render children()}
	</main>
</div>
