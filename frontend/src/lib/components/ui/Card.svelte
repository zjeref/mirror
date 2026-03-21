<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		children: Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div class="bg-[var(--color-surface-light)] rounded-xl border border-[var(--color-border)] p-5 {className}">
	{@render children()}
</div>
