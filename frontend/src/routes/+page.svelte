<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	onMount(() => {
		if (browser) {
			const token = localStorage.getItem('access_token');
			goto(token ? '/chat' : '/login');
		}
	});
</script>

<div class="h-full flex items-center justify-center">
	<p class="text-slate-500">Loading...</p>
</div>
