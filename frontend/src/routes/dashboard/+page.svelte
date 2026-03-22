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

<div class="h-full overflow-y-auto bg-gradient-to-b from-[var(--color-surface)] to-[#1a1a2e]">
	<div class="max-w-5xl mx-auto px-6 py-8">
		<!-- Header -->
		<div class="flex items-center justify-between mb-8">
			<div>
				<h1 class="text-2xl font-bold text-[var(--color-on-surface)] tracking-tight">Your week at a glance</h1>
				<p class="text-sm text-[var(--color-on-surface-variant)]/60 mt-1">Patterns Mirror has noticed</p>
			</div>
			{#if $data}
				<div class="flex items-center gap-2 px-4 py-2 rounded-full glass-card">
					<span class="material-symbols-outlined filled text-[var(--color-tertiary)] text-lg">local_fire_department</span>
					<span class="text-sm font-bold text-[var(--color-tertiary)]">{$data.days_active}</span>
					<span class="text-xs text-[var(--color-on-surface-variant)]">days active</span>
				</div>
			{/if}
		</div>

		{#if $loading}
			<div class="flex items-center justify-center h-48">
				<div class="flex gap-1.5">
					<div class="w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full animate-bounce"></div>
					<div class="w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
					<div class="w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
				</div>
			</div>
		{:else if $error}
			<div class="glass-card rounded-2xl p-5 border-[var(--color-error)]/20">
				<p class="text-[var(--color-error)] text-sm">{$error}</p>
			</div>
		{:else if $data}
			<!-- Quick stats -->
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
				<Card>
					<p class="text-[10px] text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Mood</p>
					<p class="text-3xl font-bold text-[var(--color-tertiary)]">
						{$data.current_mood ?? '—'}
						<span class="text-sm font-normal text-[var(--color-outline)]">/10</span>
					</p>
				</Card>
				<Card>
					<p class="text-[10px] text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Energy</p>
					<p class="text-3xl font-bold text-[var(--color-primary)]">
						{$data.current_energy ?? '—'}
						<span class="text-sm font-normal text-[var(--color-outline)]">/10</span>
					</p>
				</Card>
				<Card>
					<p class="text-[10px] text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Check-ins</p>
					<p class="text-3xl font-bold text-[var(--color-on-surface)]">{$data.total_check_ins}</p>
				</Card>
				<Card>
					<p class="text-[10px] text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-2">Days Active</p>
					<p class="text-3xl font-bold text-[var(--color-on-surface)]">{$data.days_active}</p>
				</Card>
			</div>

			<!-- Charts row -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
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
			<div class="flex flex-col items-center justify-center h-64 gap-4">
				<span class="material-symbols-outlined text-5xl text-[var(--color-primary)]/20">dashboard</span>
				<p class="text-[var(--color-on-surface-variant)]/60">No data yet</p>
				<a href="/chat" class="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--color-primary-container)]/20 text-[var(--color-primary)] hover:bg-[var(--color-primary-container)]/30 transition-colors text-sm">
					<span class="material-symbols-outlined text-base">chat_bubble</span>
					Start chatting to build your dashboard
				</a>
			</div>
		{/if}
	</div>
</div>
