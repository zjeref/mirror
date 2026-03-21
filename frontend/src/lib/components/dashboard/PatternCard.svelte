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
		temporal: 'bg-blue-500/20 text-blue-400',
		behavior_chain: 'bg-purple-500/20 text-purple-400',
		energy_cycle: 'bg-amber-500/20 text-amber-400',
		strategy_effectiveness: 'bg-green-500/20 text-green-400',
		mood_trigger: 'bg-rose-500/20 text-rose-400',
	};
</script>

<div>
	<h3 class="text-sm font-medium text-slate-300 mb-3">Detected Patterns</h3>

	{#if patterns.length > 0}
		<div class="space-y-3">
			{#each patterns as pattern}
				<div class="bg-[var(--color-surface)] rounded-lg p-3">
					<div class="flex items-start justify-between gap-2 mb-1">
						<span class="text-xs px-2 py-0.5 rounded-full {typeColors[pattern.pattern_type] ?? 'bg-slate-500/20 text-slate-400'}">
							{typeLabels[pattern.pattern_type] ?? pattern.pattern_type}
						</span>
						<div class="flex items-center gap-1">
							<div class="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
								<div
									class="h-full bg-indigo-500 rounded-full"
									style="width: {pattern.confidence * 100}%"
								></div>
							</div>
							<span class="text-xs text-slate-500">{Math.round(pattern.confidence * 100)}%</span>
						</div>
					</div>
					<p class="text-sm text-slate-200 mb-1">{pattern.description}</p>
					{#if pattern.actionable_insight}
						<p class="text-xs text-slate-400 italic">{pattern.actionable_insight}</p>
					{/if}
				</div>
			{/each}
		</div>
	{:else}
		<p class="text-sm text-slate-500">Keep checking in — patterns emerge after 5+ data points.</p>
	{/if}
</div>
