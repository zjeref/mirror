<script lang="ts">
	interface Props {
		options: string[];
		onSelect: (value: string) => void;
	}

	let { options, onSelect }: Props = $props();
</script>

<div class="flex flex-wrap gap-2 mb-3 px-2">
	{#each options as option}
		<button
			onclick={() => onSelect(option)}
			class="px-3 py-1.5 text-sm rounded-full border border-indigo-500/50 text-indigo-300
				hover:bg-indigo-500/20 hover:border-indigo-400 transition-colors"
		>
			{option}
		</button>
	{/each}
</div>
