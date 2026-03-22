<script lang="ts">
	import '../app.css';
	import { user } from '$lib/stores/auth';
	import { page } from '$app/state';
	import Nav from '$lib/components/ui/Nav.svelte';

	let { children } = $props();

	const isAuthPage = $derived(
		page.url.pathname === '/login' || page.url.pathname === '/register' || page.url.pathname === '/'
	);
	const showNav = $derived(!isAuthPage && $user);
</script>

<svelte:head>
	<title>Mirror</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
	<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet" />
	<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
</svelte:head>

<div class="h-screen flex overflow-hidden">
	{#if showNav}
		<Nav />
	{/if}
	<main class="flex-1 overflow-hidden {showNav ? 'pb-16 md:pb-0' : ''}">
		{@render children()}
	</main>
</div>

<!-- Background ambient glow -->
{#if showNav}
	<div class="fixed top-[-10%] right-[-5%] w-[40rem] h-[40rem] bg-[#6c5ce7]/5 rounded-full blur-[120px] pointer-events-none z-0"></div>
	<div class="fixed bottom-[-10%] left-[10%] w-[30rem] h-[30rem] bg-[#edbf7c]/5 rounded-full blur-[100px] pointer-events-none z-0"></div>
{/if}
