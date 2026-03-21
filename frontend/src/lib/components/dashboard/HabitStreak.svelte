<script lang="ts">
	import { api } from '$lib/api/client';

	interface Habit {
		id: string;
		name: string;
		streak: number;
		total_completions: number;
	}

	interface Props {
		habits: Habit[];
	}

	let { habits }: Props = $props();

	async function logCompletion(habitId: string) {
		await api.logHabit(habitId, true, 'tiny');
		// TODO: refresh dashboard data
	}
</script>

<div>
	<h3 class="text-sm font-medium text-slate-300 mb-3">Habits</h3>

	{#if habits.length > 0}
		<div class="space-y-2">
			{#each habits as habit}
				<div class="flex items-center justify-between bg-[var(--color-surface)] rounded-lg px-3 py-2">
					<div>
						<p class="text-sm text-slate-200">{habit.name}</p>
						<p class="text-xs text-slate-500">{habit.total_completions} total</p>
					</div>
					<div class="flex items-center gap-3">
						<div class="text-right">
							<span class="text-lg font-bold text-indigo-400">{habit.streak}</span>
							<span class="text-xs text-slate-500 block">streak</span>
						</div>
						<button
							onclick={() => logCompletion(habit.id)}
							class="w-8 h-8 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30
								flex items-center justify-center text-lg transition-colors"
							title="Log completion"
						>
							+
						</button>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<p class="text-sm text-slate-500">No habits yet. Start one in chat by saying "build a habit".</p>
	{/if}
</div>
