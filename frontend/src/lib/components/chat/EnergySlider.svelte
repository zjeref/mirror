<script lang="ts">
	interface Props {
		min?: number;
		max?: number;
		prompt: string;
		onSubmit: (value: number) => void;
	}

	let { min = 1, max = 10, prompt, onSubmit }: Props = $props();

	let value = $state(5);

	const labels: Record<number, string> = {
		1: 'Almost nothing', 2: 'Very low', 3: 'Low', 4: 'Below average',
		5: 'Moderate', 6: 'Decent', 7: 'Good', 8: 'Great', 9: 'Very high', 10: 'Peak',
	};
</script>

<div class="glass-card rounded-2xl p-5 mb-2">
	<p class="text-sm text-[var(--color-on-surface-variant)] mb-4">{prompt}</p>

	<div class="flex items-center gap-4 mb-3">
		<input
			type="range"
			{min}
			{max}
			bind:value
			class="flex-1 h-2 bg-[var(--color-surface-highest)] rounded-full appearance-none cursor-pointer
				[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
				[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--color-tertiary)]
				[&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-[var(--color-tertiary)]/30"
		/>
		<span class="text-2xl font-bold text-[var(--color-tertiary)] min-w-[2ch] text-center">{value}</span>
	</div>

	<div class="flex items-center justify-between">
		<span class="text-xs text-[var(--color-outline)]">{labels[value]}</span>
		<button
			onclick={() => onSubmit(value)}
			class="px-5 py-2 text-sm bg-[var(--color-tertiary)] text-[#442c00] rounded-full font-medium
				hover:scale-105 active:scale-95 transition-all shadow-lg shadow-[var(--color-tertiary)]/20"
		>
			Submit
		</button>
	</div>
</div>
