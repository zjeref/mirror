<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import Card from '$lib/components/ui/Card.svelte';
	import HabitStreak from '$lib/components/dashboard/HabitStreak.svelte';

	let habits = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			habits = await api.getHabits();
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
			<h1 class="text-xl font-semibold text-white">Habits</h1>
			<a href="/dashboard" class="text-sm text-slate-400 hover:text-white">&larr; Dashboard</a>
		</div>

		{#if loading}
			<p class="text-slate-500">Loading habits...</p>
		{:else}
			<Card>
				<HabitStreak {habits} />
			</Card>

			<div class="mt-4 text-center">
				<a href="/chat" class="text-sm text-indigo-400 hover:text-indigo-300">
					Go to Chat to create a new habit
				</a>
			</div>
		{/if}
	</div>
</div>
