<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import Card from '$lib/components/ui/Card.svelte';
	import PatternCard from '$lib/components/dashboard/PatternCard.svelte';

	let patterns = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			patterns = await api.getPatterns();
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
		}
	});
</script>

<div class="h-full overflow-y-auto">
	<div class="max-w-3xl mx-auto px-4 py-6">
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-xl font-semibold text-white">Patterns</h1>
			<a href="/dashboard" class="text-sm text-slate-400 hover:text-white">&larr; Dashboard</a>
		</div>

		{#if loading}
			<p class="text-slate-500">Loading patterns...</p>
		{:else}
			<Card>
				<PatternCard {patterns} />
			</Card>
		{/if}
	</div>
</div>
