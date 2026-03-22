<script lang="ts">
	interface Pattern {
		id: string;
		pattern_type: string;
		description: string;
		confidence: number;
		actionable_insight: string | null;
	}

	interface Props {
		patterns: Pattern[];
	}

	let { patterns }: Props = $props();

	const typeLabels: Record<string, string> = {
		temporal: 'Time Pattern',
		behavior_chain: 'Behavior Link',
		energy_cycle: 'Energy Cycle',
		strategy_effectiveness: 'What Works',
		mood_trigger: 'Mood Trigger',
	};

	const typeColors: Record<string, string> = {
		temporal: 'bg-[var(--color-primary)]/15 text-[var(--color-primary)]',
		behavior_chain: 'bg-[var(--color-primary-container)]/20 text-[var(--color-primary)]',
		energy_cycle: 'bg-[var(--color-tertiary)]/15 text-[var(--color-tertiary)]',
		strategy_effectiveness: 'bg-emerald-500/15 text-emerald-400',
		mood_trigger: 'bg-[var(--color-error)]/15 text-[var(--color-error)]',
	};
</script>

<div>
	<h3 class="text-sm font-semibold text-[var(--color-on-surface)] mb-3">Patterns Noticed</h3>

	{#if patterns.length > 0}
		<div class="space-y-3">
			{#each patterns as pattern}
				<div class="bg-[var(--color-surface-low)]/50 rounded-xl p-4">
					<div class="flex items-start justify-between gap-2 mb-2">
						<span class="text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider {typeColors[pattern.pattern_type] ?? 'bg-[var(--color-surface-highest)]/50 text-[var(--color-outline)]'}">
							{typeLabels[pattern.pattern_type] ?? pattern.pattern_type}
						</span>
						<div class="flex items-center gap-1.5">
							<div class="w-12 h-1.5 bg-[var(--color-surface-highest)] rounded-full overflow-hidden">
								<div
									class="h-full bg-[var(--color-tertiary)] rounded-full"
									style="width: {pattern.confidence * 100}%"
								></div>
							</div>
							<span class="text-[10px] text-[var(--color-outline)]">{Math.round(pattern.confidence * 100)}%</span>
						</div>
					</div>
					<p class="text-sm text-[var(--color-on-surface)] mb-1">{pattern.description}</p>
					{#if pattern.actionable_insight}
						<p class="text-xs text-[var(--color-on-surface-variant)] italic">{pattern.actionable_insight}</p>
					{/if}
				</div>
			{/each}
		</div>
	{:else}
		<div class="flex flex-col items-center gap-2 py-4">
			<span class="material-symbols-outlined text-2xl text-[var(--color-outline)]/30">pattern</span>
			<p class="text-sm text-[var(--color-outline)]">Patterns emerge after 5+ conversations</p>
		</div>
	{/if}
</div>
