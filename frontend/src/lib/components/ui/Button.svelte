<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'primary' | 'secondary' | 'ghost';
		size?: 'sm' | 'md' | 'lg';
		disabled?: boolean;
		type?: 'button' | 'submit';
		onclick?: () => void;
		children: Snippet;
	}

	let {
		variant = 'primary',
		size = 'md',
		disabled = false,
		type = 'button',
		onclick,
		children,
	}: Props = $props();

	const variants = {
		primary: 'bg-indigo-500 hover:bg-indigo-600 text-white',
		secondary: 'bg-slate-700 hover:bg-slate-600 text-slate-200',
		ghost: 'bg-transparent hover:bg-slate-700 text-slate-300',
	};

	const sizes = {
		sm: 'px-3 py-1.5 text-sm',
		md: 'px-4 py-2 text-sm',
		lg: 'px-6 py-3 text-base',
	};
</script>

<button
	{type}
	{disabled}
	{onclick}
	class="rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed {variants[variant]} {sizes[size]}"
>
	{@render children()}
</button>
