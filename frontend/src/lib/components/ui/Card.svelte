<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		children: Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div class="glass-card rounded-2xl p-5 transition-all duration-300 hover:border-[var(--color-outline-variant)]/25 {className}">
	{@render children()}
</div>
