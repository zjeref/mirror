<script lang="ts">
	interface Props {
		options: string[];
		onSelect: (value: string) => void;
	}

	let { options, onSelect }: Props = $props();
</script>

<div class="flex flex-wrap gap-2 mb-2">
	{#each options as option}
		<button
			onclick={() => onSelect(option)}
			class="px-4 py-2 text-sm rounded-full border border-[var(--color-primary-container)]/40 text-[var(--color-primary)]
				hover:bg-[var(--color-primary-container)]/20 hover:border-[var(--color-primary)] transition-all duration-200"
		>
			{option}
		</button>
	{/each}
</div>
