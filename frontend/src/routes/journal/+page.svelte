<script lang="ts">
	import { onMount } from 'svelte';
	import { journal } from '$lib/stores/journal';

	const currentEntry = journal.currentEntry;
	const entries = journal.entries;
	const loading = journal.loading;
	const saving = journal.saving;

	let content = $state('');
	let moodScore = $state<number | null>(null);
	let energyScore = $state<number | null>(null);
	let selectedTags = $state<string[]>([]);
	let wins = $state<string[]>([]);
	let newWin = $state('');
	let selectedDate = $state(journal.todayDate());
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let showPastEntries = $state(false);

	const allTags = ['Work', 'Family', 'Health', 'Social', 'Creative', 'Rest', 'Learning', 'Nature'];
	const moodEmojis = [
		{ score: 2, emoji: '😔', label: 'Low' },
		{ score: 4, emoji: '😕', label: 'Meh' },
		{ score: 6, emoji: '😐', label: 'Okay' },
		{ score: 8, emoji: '🙂', label: 'Good' },
		{ score: 10, emoji: '😊', label: 'Great' },
	];

	onMount(() => {
		journal.loadEntry(selectedDate);
		journal.loadEntries();
	});

	$effect(() => {
		if ($currentEntry) {
			content = $currentEntry.content || '';
			moodScore = $currentEntry.mood_score;
			energyScore = $currentEntry.energy_score;
			selectedTags = [...($currentEntry.tags || [])];
			wins = [...($currentEntry.wins || [])];
		}
	});

	function autoSave() {
		if (saveTimeout) clearTimeout(saveTimeout);
		saveTimeout = setTimeout(() => {
			journal.saveEntry({
				date: selectedDate,
				content,
				mood_score: moodScore,
				energy_score: energyScore,
				tags: selectedTags,
				wins,
				word_count: content.trim().split(/\s+/).filter(Boolean).length,
			});
		}, 2000);
	}

	function toggleTag(tag: string) {
		if (selectedTags.includes(tag)) {
			selectedTags = selectedTags.filter((t) => t !== tag);
		} else {
			selectedTags = [...selectedTags, tag];
		}
		autoSave();
	}

	function addWin() {
		if (!newWin.trim()) return;
		wins = [...wins, newWin.trim()];
		newWin = '';
		autoSave();
	}

	function removeWin(index: number) {
		wins = wins.filter((_, i) => i !== index);
		autoSave();
	}

	function selectDate(date: string) {
		if (content || moodScore || wins.length) {
			journal.saveEntry({
				date: selectedDate,
				content,
				mood_score: moodScore,
				energy_score: energyScore,
				tags: selectedTags,
				wins,
				word_count: content.trim().split(/\s+/).filter(Boolean).length,
			});
		}
		selectedDate = date;
		journal.loadEntry(date);
		showPastEntries = false;
	}

	function formatDisplayDate(dateStr: string): string {
		const d = new Date(dateStr + 'T12:00:00');
		return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
	}

	function formatShortDate(dateStr: string): string {
		const d = new Date(dateStr + 'T12:00:00');
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function getReflection() {
		journal.getReflection(selectedDate);
	}

	function getMoodEmoji(score: number | null | undefined): string {
		if (!score) return '📝';
		return moodEmojis.find(m => Math.abs(m.score - score) <= 1)?.emoji ?? '📝';
	}

	const wordCount = $derived(content.trim().split(/\s+/).filter(Boolean).length);
	const isToday = $derived(selectedDate === journal.todayDate());
</script>

<div class="h-full overflow-y-auto bg-gradient-to-b from-[var(--color-surface)] to-[#1a1a2e]">
	<div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8 flex flex-col lg:flex-row gap-5">

		<!-- Main journal area -->
		<div class="flex-1 min-w-0 order-2 lg:order-1">
			<!-- Date header -->
			<div class="flex items-center justify-between mb-5">
				<div class="min-w-0">
					<h1 class="text-xl md:text-2xl font-bold text-[var(--color-on-surface)] tracking-tight truncate">
						{formatDisplayDate(selectedDate)}
					</h1>
					<p class="text-sm text-[var(--color-on-surface-variant)]/60 mt-1">
						{#if isToday}Today's entry{:else}Past entry{/if}
						{#if $saving}
							<span class="text-[var(--color-tertiary)]"> · Saving...</span>
						{/if}
					</p>
				</div>
				<div class="flex items-center gap-2">
					<!-- Mobile: toggle past entries -->
					<button
						onclick={() => showPastEntries = !showPastEntries}
						class="lg:hidden flex items-center gap-1.5 px-3 py-2 rounded-full bg-[var(--color-surface-highest)]/30 text-[var(--color-on-surface-variant)] text-sm"
					>
						<span class="material-symbols-outlined text-base">history</span>
						Past
					</button>
					{#if content.length > 50}
						<button
							onclick={getReflection}
							class="flex items-center gap-1.5 px-3 md:px-4 py-2 rounded-full bg-[var(--color-primary-container)]/20 text-[var(--color-primary)] hover:bg-[var(--color-primary-container)]/30 transition-colors text-sm"
						>
							<span class="material-symbols-outlined text-base">auto_awesome</span>
							<span class="hidden sm:inline">Get reflection</span>
						</button>
					{/if}
				</div>
			</div>

			<!-- Mobile past entries drawer -->
			{#if showPastEntries}
				<div class="lg:hidden glass-card rounded-2xl p-4 mb-5">
					<div class="flex items-center justify-between mb-3">
						<p class="text-xs font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest">Past Entries</p>
						<button onclick={() => showPastEntries = false} class="text-[var(--color-outline)]">
							<span class="material-symbols-outlined text-lg">close</span>
						</button>
					</div>
					<div class="flex flex-col gap-1.5 max-h-60 overflow-y-auto">
						<!-- Today button -->
						<button
							onclick={() => selectDate(journal.todayDate())}
							class="flex items-center gap-3 p-2.5 rounded-xl text-left transition-colors
								{journal.todayDate() === selectedDate
									? 'bg-[var(--color-primary-container)]/20'
									: 'hover:bg-[var(--color-surface-highest)]/30'}"
						>
							<span class="text-lg">✨</span>
							<div>
								<p class="text-sm font-medium text-[var(--color-on-surface)]">Today</p>
								<p class="text-[11px] text-[var(--color-outline)]">{formatShortDate(journal.todayDate())}</p>
							</div>
						</button>
						{#each $entries as entry}
							<button
								onclick={() => selectDate(entry.date)}
								class="flex items-center gap-3 p-2.5 rounded-xl text-left transition-colors
									{entry.date === selectedDate
										? 'bg-[var(--color-primary-container)]/20'
										: 'hover:bg-[var(--color-surface-highest)]/30'}"
							>
								<span class="text-lg">{getMoodEmoji(entry.mood_score)}</span>
								<div class="min-w-0 flex-1">
									<p class="text-sm text-[var(--color-on-surface)]">
										{formatShortDate(entry.date)}
									</p>
									<p class="text-[11px] text-[var(--color-outline)] truncate">
										{entry.content?.slice(0, 50) || 'No entry'}
									</p>
								</div>
								{#if entry.wins?.length}
									<span class="text-[10px] text-[var(--color-tertiary)] bg-[var(--color-tertiary)]/10 px-1.5 py-0.5 rounded-full">
										{entry.wins.length} win{entry.wins.length > 1 ? 's' : ''}
									</span>
								{/if}
							</button>
						{/each}
						{#if $entries.length === 0}
							<p class="text-xs text-[var(--color-outline)] text-center py-4">No entries yet. Start writing!</p>
						{/if}
					</div>
				</div>
			{/if}

			<!-- Mood + Energy (mobile: inline, desktop: in sidebar) -->
			<div class="flex gap-3 mb-5 lg:hidden">
				<div class="glass-card rounded-2xl p-4 flex-1">
					<p class="text-[10px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-3">Mood</p>
					<div class="flex justify-between">
						{#each moodEmojis as mood}
							<button
								onclick={() => { moodScore = mood.score; autoSave(); }}
								class="transition-all duration-200
									{moodScore === mood.score ? 'scale-125' : 'opacity-40 hover:opacity-80'}"
							>
								<span class="text-xl">{mood.emoji}</span>
							</button>
						{/each}
					</div>
				</div>
				<div class="glass-card rounded-2xl p-4 w-32">
					<p class="text-[10px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-3">Energy</p>
					<input
						type="range" min="1" max="10" bind:value={energyScore} oninput={autoSave}
						class="w-full h-1.5 bg-[var(--color-surface-highest)] rounded-full appearance-none cursor-pointer
							[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
							[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--color-tertiary)]"
					/>
					<p class="text-center text-sm font-bold text-[var(--color-tertiary)] mt-1">{energyScore ?? '—'}</p>
				</div>
			</div>

			<!-- Paper writing area -->
			<div class="paper-texture rounded-2xl shadow-2xl shadow-black/30 overflow-hidden">
				<div class="px-5 md:px-8 pt-5 pb-2">
					<p class="text-[#8b7e6a] text-xs font-medium uppercase tracking-widest mb-2">
						{formatDisplayDate(selectedDate)}
					</p>
				</div>
				<div class="px-5 md:px-8 pb-6 md:pb-8">
					<textarea
						bind:value={content}
						oninput={autoSave}
						placeholder="How was your day? What did you do, feel, notice..."
						class="w-full min-h-[250px] md:min-h-[400px] bg-transparent border-none focus:ring-0 focus:outline-none
							journal-text text-[#3d3529] placeholder-[#c4b8a4] resize-none text-base"
					></textarea>
				</div>
				<div class="px-5 md:px-8 pb-3 flex justify-between items-center border-t border-[#e8e0d4]">
					<span class="text-[11px] text-[#b0a48e]">{wordCount} words</span>
					<span class="text-[11px] text-[#b0a48e]">Auto-saved</span>
				</div>
			</div>

			<!-- Tags (mobile) -->
			<div class="lg:hidden glass-card rounded-2xl p-4 mt-4">
				<p class="text-[10px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-3">What was today about?</p>
				<div class="flex flex-wrap gap-1.5">
					{#each allTags as tag}
						<button
							onclick={() => toggleTag(tag)}
							class="px-3 py-1 rounded-full text-xs font-medium transition-all duration-200
								{selectedTags.includes(tag)
									? 'bg-[var(--color-primary-container)] text-[var(--color-on-primary-container)]'
									: 'bg-[var(--color-surface-highest)]/50 text-[var(--color-on-surface-variant)]'}"
						>
							{tag}
						</button>
					{/each}
				</div>
			</div>

			<!-- Wins (mobile) -->
			<div class="lg:hidden glass-card rounded-2xl p-4 mt-3">
				<p class="text-[10px] font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-3">Wins today</p>
				{#each wins as win, i}
					<div class="flex items-center gap-2 mb-1.5">
						<span class="material-symbols-outlined filled text-[var(--color-tertiary)] text-sm">check_circle</span>
						<span class="text-sm text-[var(--color-on-surface)] flex-1">{win}</span>
						<button onclick={() => removeWin(i)} class="text-[var(--color-outline)]">
							<span class="material-symbols-outlined text-sm">close</span>
						</button>
					</div>
				{/each}
				<div class="flex gap-2 mt-2">
					<input
						bind:value={newWin}
						onkeydown={(e) => e.key === 'Enter' && addWin()}
						placeholder="Add a win..."
						class="flex-1 bg-[var(--color-surface-highest)]/50 border-none rounded-lg px-3 py-1.5 text-sm
							text-[var(--color-on-surface)] placeholder-[var(--color-outline)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/30 focus:outline-none"
					/>
					<button onclick={addWin} class="text-[var(--color-primary)]">
						<span class="material-symbols-outlined">add_circle</span>
					</button>
				</div>
			</div>

			<!-- AI Reflection -->
			{#if $currentEntry?.ai_reflection}
				<div class="mt-5 glass-card rounded-2xl p-5">
					<div class="flex items-center gap-2 mb-3">
						<span class="material-symbols-outlined filled text-[var(--color-tertiary)] text-lg">auto_awesome</span>
						<span class="text-sm font-semibold text-[var(--color-tertiary)]">Mirror's Reflection</span>
					</div>
					<p class="text-[var(--color-on-surface-variant)] text-sm leading-relaxed">
						{$currentEntry.ai_reflection}
					</p>
				</div>
			{/if}
		</div>

		<!-- Desktop right sidebar (hidden on mobile) -->
		<aside class="hidden lg:flex w-72 flex-shrink-0 flex-col gap-5 order-2">
			<!-- Mood -->
			<div class="glass-card rounded-2xl p-5">
				<p class="text-xs font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-4">How are you feeling?</p>
				<div class="flex justify-between">
					{#each moodEmojis as mood}
						<button
							onclick={() => { moodScore = mood.score; autoSave(); }}
							class="flex flex-col items-center gap-1 transition-all duration-200
								{moodScore === mood.score ? 'scale-125' : 'opacity-50 hover:opacity-80 hover:scale-110'}"
						>
							<span class="text-2xl">{mood.emoji}</span>
							<span class="text-[9px] text-[var(--color-on-surface-variant)]">{mood.label}</span>
						</button>
					{/each}
				</div>
			</div>

			<!-- Energy -->
			<div class="glass-card rounded-2xl p-5">
				<p class="text-xs font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-4">Energy level</p>
				<input
					type="range" min="1" max="10" bind:value={energyScore} oninput={autoSave}
					class="w-full h-2 bg-[var(--color-surface-highest)] rounded-full appearance-none cursor-pointer
						[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
						[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--color-tertiary)]
						[&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-[var(--color-tertiary)]/30"
				/>
				<div class="flex justify-between mt-2">
					<span class="text-[10px] text-[var(--color-outline)]">Drained</span>
					<span class="text-sm font-bold text-[var(--color-tertiary)]">{energyScore ?? '—'}</span>
					<span class="text-[10px] text-[var(--color-outline)]">Energized</span>
				</div>
			</div>

			<!-- Tags -->
			<div class="glass-card rounded-2xl p-5">
				<p class="text-xs font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-4">What was today about?</p>
				<div class="flex flex-wrap gap-2">
					{#each allTags as tag}
						<button
							onclick={() => toggleTag(tag)}
							class="px-3 py-1 rounded-full text-xs font-medium transition-all duration-200
								{selectedTags.includes(tag)
									? 'bg-[var(--color-primary-container)] text-[var(--color-on-primary-container)]'
									: 'bg-[var(--color-surface-highest)]/50 text-[var(--color-on-surface-variant)] hover:bg-[var(--color-surface-highest)]'}"
						>
							{tag}
						</button>
					{/each}
				</div>
			</div>

			<!-- Wins -->
			<div class="glass-card rounded-2xl p-5">
				<p class="text-xs font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-4">Wins today</p>
				<div class="flex flex-col gap-2 mb-3">
					{#each wins as win, i}
						<div class="flex items-center gap-2 group">
							<span class="material-symbols-outlined filled text-[var(--color-tertiary)] text-sm">check_circle</span>
							<span class="text-sm text-[var(--color-on-surface)] flex-1">{win}</span>
							<button
								onclick={() => removeWin(i)}
								class="text-[var(--color-outline)] hover:text-[var(--color-error)] opacity-0 group-hover:opacity-100 transition-opacity"
							>
								<span class="material-symbols-outlined text-sm">close</span>
							</button>
						</div>
					{/each}
				</div>
				<div class="flex gap-2">
					<input
						bind:value={newWin}
						onkeydown={(e) => e.key === 'Enter' && addWin()}
						placeholder="Add a win..."
						class="flex-1 bg-[var(--color-surface-highest)]/50 border-none rounded-lg px-3 py-1.5 text-sm
							text-[var(--color-on-surface)] placeholder-[var(--color-outline)]/50 focus:ring-1 focus:ring-[var(--color-primary)]/30 focus:outline-none"
					/>
					<button onclick={addWin} class="text-[var(--color-primary)] hover:text-[var(--color-tertiary)] transition-colors">
						<span class="material-symbols-outlined">add_circle</span>
					</button>
				</div>
			</div>

			<!-- Past entries -->
			<div class="glass-card rounded-2xl p-5">
				<p class="text-xs font-semibold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-4">Past entries</p>
				<div class="flex flex-col gap-1.5 max-h-64 overflow-y-auto">
					<!-- Today button -->
					{#if !isToday}
						<button
							onclick={() => selectDate(journal.todayDate())}
							class="flex items-center gap-3 p-2.5 rounded-xl text-left transition-colors hover:bg-[var(--color-surface-highest)]/30"
						>
							<span class="text-lg">✨</span>
							<div>
								<p class="text-sm font-medium text-[var(--color-primary)]">Back to today</p>
							</div>
						</button>
					{/if}
					{#each $entries as entry}
						<button
							onclick={() => selectDate(entry.date)}
							class="flex items-center gap-3 p-2.5 rounded-xl text-left transition-colors
								{entry.date === selectedDate
									? 'bg-[var(--color-primary-container)]/20'
									: 'hover:bg-[var(--color-surface-highest)]/30'}"
						>
							<span class="text-lg">{getMoodEmoji(entry.mood_score)}</span>
							<div class="min-w-0 flex-1">
								<p class="text-xs text-[var(--color-on-surface-variant)]">
									{formatShortDate(entry.date)}
								</p>
								<p class="text-[11px] text-[var(--color-outline)] truncate">
									{entry.content?.slice(0, 40) || 'No entry'}
									{entry.content && entry.content.length > 40 ? '...' : ''}
								</p>
							</div>
							{#if entry.wins?.length}
								<span class="text-[9px] text-[var(--color-tertiary)] bg-[var(--color-tertiary)]/10 px-1.5 py-0.5 rounded-full whitespace-nowrap">
									{entry.wins.length} win{entry.wins.length > 1 ? 's' : ''}
								</span>
							{/if}
						</button>
					{/each}
					{#if $entries.length === 0}
						<p class="text-xs text-[var(--color-outline)] text-center py-3">No entries yet. Start writing!</p>
					{/if}
				</div>
			</div>
		</aside>
	</div>
</div>
