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
	}
</script>

<div>
	<h3 class="text-sm font-semibold text-[var(--color-on-surface)] mb-3">Habits</h3>

	{#if habits.length > 0}
		<div class="space-y-2">
			{#each habits as habit}
				<div class="flex items-center justify-between bg-[var(--color-surface-low)]/50 rounded-xl px-4 py-3">
					<div>
						<p class="text-sm text-[var(--color-on-surface)]">{habit.name}</p>
						<p class="text-[11px] text-[var(--color-outline)]">{habit.total_completions} total</p>
					</div>
					<div class="flex items-center gap-3">
						<div class="text-right">
							<span class="text-lg font-bold text-[var(--color-tertiary)]">{habit.streak}</span>
							<span class="text-[10px] text-[var(--color-outline)] block">streak</span>
						</div>
						<button
							onclick={() => logCompletion(habit.id)}
							class="w-8 h-8 rounded-xl bg-[var(--color-tertiary)]/10 text-[var(--color-tertiary)]
								hover:bg-[var(--color-tertiary)]/20 flex items-center justify-center transition-colors"
							title="Log completion"
						>
							<span class="material-symbols-outlined text-lg">check</span>
						</button>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="flex flex-col items-center gap-2 py-4">
			<span class="material-symbols-outlined text-2xl text-[var(--color-outline)]/30">rocket_launch</span>
			<p class="text-sm text-[var(--color-outline)]">Say "build a habit" in chat to start</p>
		</div>
	{/if}
</div>
