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
		1: 'Almost nothing',
		2: 'Very low',
		3: 'Low',
		4: 'Below average',
		5: 'Moderate',
		6: 'Decent',
		7: 'Good',
		8: 'Great',
		9: 'Very high',
		10: 'Peak',
	};

	const colors: Record<number, string> = {
		1: 'text-rose-400',
		2: 'text-rose-400',
		3: 'text-amber-400',
		4: 'text-amber-400',
		5: 'text-yellow-300',
		6: 'text-lime-400',
		7: 'text-green-400',
		8: 'text-green-400',
		9: 'text-emerald-400',
		10: 'text-emerald-400',
	};
</script>

<div class="bg-[var(--color-surface-lighter)] rounded-xl p-4 mb-3 mx-2">
	<p class="text-sm text-slate-300 mb-3">{prompt}</p>

	<div class="flex items-center gap-4 mb-2">
		<input
			type="range"
			{min}
			{max}
			bind:value
			class="flex-1 accent-indigo-500"
		/>
		<span class="text-2xl font-bold {colors[value]} min-w-[2ch] text-center">{value}</span>
	</div>

	<div class="flex items-center justify-between">
		<span class="text-xs text-slate-500">{labels[value]}</span>
		<button
			onclick={() => onSubmit(value)}
			class="px-4 py-1.5 text-sm bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition-colors"
		>
			Submit
		</button>
	</div>
</div>
