<script lang="ts">
	import { onMount } from 'svelte';
	import { dashboard } from '$lib/stores/dashboard';
	import Card from '$lib/components/ui/Card.svelte';
	import MoodTrend from '$lib/components/dashboard/MoodTrend.svelte';
	import LifeAreaRadar from '$lib/components/dashboard/LifeAreaRadar.svelte';
	import HabitStreak from '$lib/components/dashboard/HabitStreak.svelte';
	import PatternCard from '$lib/components/dashboard/PatternCard.svelte';

	const data = dashboard.data;
	const loading = dashboard.loading;
	const error = dashboard.error;

	onMount(() => {
		dashboard.load();
	});
</script>

<div class="h-full overflow-y-auto">
	<div class="max-w-5xl mx-auto px-4 py-6">
		<h1 class="text-xl font-semibold text-white mb-6">Dashboard</h1>

		{#if $loading}
			<div class="flex items-center justify-center h-48">
				<p class="text-slate-500">Loading your data...</p>
			</div>
		{:else if $error}
			<div class="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-lg px-4 py-3">
				{$error}
			</div>
		{:else if $data}
			<!-- Quick stats -->
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
				<Card>
					<p class="text-xs text-slate-500 uppercase tracking-wide">Mood</p>
					<p class="text-2xl font-bold {($data.current_mood ?? 0) >= 6 ? 'text-green-400' : ($data.current_mood ?? 0) >= 4 ? 'text-amber-400' : 'text-rose-400'}">
						{$data.current_mood ?? '—'}
						<span class="text-sm font-normal text-slate-500">/10</span>
					</p>
				</Card>
				<Card>
					<p class="text-xs text-slate-500 uppercase tracking-wide">Energy</p>
					<p class="text-2xl font-bold {($data.current_energy ?? 0) >= 6 ? 'text-green-400' : ($data.current_energy ?? 0) >= 4 ? 'text-amber-400' : 'text-rose-400'}">
						{$data.current_energy ?? '—'}
						<span class="text-sm font-normal text-slate-500">/10</span>
					</p>
				</Card>
				<Card>
					<p class="text-xs text-slate-500 uppercase tracking-wide">Check-ins</p>
					<p class="text-2xl font-bold text-indigo-400">{$data.total_check_ins}</p>
				</Card>
				<Card>
					<p class="text-xs text-slate-500 uppercase tracking-wide">Days Active</p>
					<p class="text-2xl font-bold text-indigo-400">{$data.days_active}</p>
				</Card>
			</div>

			<!-- Charts row -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
				<Card>
					<MoodTrend dataPoints={$data.mood_data_points} trend={$data.mood_trend} />
				</Card>
				<Card>
					<LifeAreaRadar areas={$data.life_area_scores} />
				</Card>
			</div>

			<!-- Habits + Patterns -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<Card>
					<HabitStreak habits={$data.active_habits} />
				</Card>
				<Card>
					<PatternCard patterns={$data.recent_patterns} />
				</Card>
			</div>
		{:else}
			<div class="flex items-center justify-center h-48">
				<div class="text-center">
					<p class="text-slate-400 mb-2">No data yet</p>
					<p class="text-sm text-slate-500">Start by <a href="/chat" class="text-indigo-400 hover:underline">chatting with Mirror</a> and doing a check-in.</p>
				</div>
			</div>
		{/if}
	</div>
</div>
