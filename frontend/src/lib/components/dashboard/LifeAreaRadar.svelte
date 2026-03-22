<script lang="ts">
	interface Props {
		areas: { area: string; score: number; trend: string }[];
	}

	let { areas }: Props = $props();

	const size = 260;
	const center = size / 2;
	const maxRadius = 70;
	const levels = 5;

	const areaLabels: Record<string, string> = {
		physical: 'Physical',
		mental: 'Mental',
		career: 'Career',
		habits: 'Habits',
	};

	const trendColors: Record<string, string> = {
		improving: '#34d399',
		stable: '#c8c4d7',
		declining: '#ffb4ab',
	};

	function getPoint(index: number, radius: number): { x: number; y: number } {
		const angle = (Math.PI * 2 * index) / areas.length - Math.PI / 2;
		return {
			x: center + Math.cos(angle) * radius,
			y: center + Math.sin(angle) * radius,
		};
	}

	const dataPoints = $derived(
		areas.map((area, i) => getPoint(i, (area.score / 10) * maxRadius))
	);

	const dataPath = $derived(
		dataPoints.length > 0
			? `M ${dataPoints.map((p) => `${p.x},${p.y}`).join(' L ')} Z`
			: ''
	);
</script>

<div>
	<h3 class="text-sm font-semibold text-[var(--color-on-surface)] mb-3">Life Areas</h3>

	{#if areas.length > 0}
		<svg viewBox="0 0 {size} {size}" class="w-full max-w-[260px] mx-auto">
			<!-- Grid levels -->
			{#each Array(levels) as _, level}
				{@const r = ((level + 1) / levels) * maxRadius}
				<polygon
					points={areas.map((_, i) => {
						const p = getPoint(i, r);
						return `${p.x},${p.y}`;
					}).join(' ')}
					fill="none"
					stroke="var(--color-outline-variant)"
					stroke-width="0.5"
					opacity="0.3"
				/>
			{/each}

			<!-- Axis lines -->
			{#each areas as _, i}
				{@const p = getPoint(i, maxRadius)}
				<line x1={center} y1={center} x2={p.x} y2={p.y}
					stroke="var(--color-outline-variant)" stroke-width="0.5" opacity="0.3" />
			{/each}

			<!-- Data polygon -->
			<polygon
				points={dataPoints.map((p) => `${p.x},${p.y}`).join(' ')}
				fill="rgba(108, 92, 231, 0.15)"
				stroke="#c6bfff"
				stroke-width="2"
				stroke-linejoin="round"
			/>

			<!-- Data dots + labels -->
			{#each areas as area, i}
				{@const dp = dataPoints[i]}
				{@const labelPoint = getPoint(i, maxRadius + 30)}
				<!-- Outer glow -->
				<circle cx={dp.x} cy={dp.y} r="7" fill={trendColors[area.trend]} opacity="0.15" />
				<!-- Dot -->
				<circle cx={dp.x} cy={dp.y} r="3.5" fill={trendColors[area.trend]} />
				<!-- Label -->
				<text
					x={labelPoint.x}
					y={labelPoint.y}
					text-anchor="middle"
					dominant-baseline="middle"
					fill="#c8c4d7"
					font-size="11"
					font-family="Plus Jakarta Sans, sans-serif"
				>
					{areaLabels[area.area] ?? area.area}
				</text>
				<!-- Score -->
				<text
					x={dp.x}
					y={dp.y - 12}
					text-anchor="middle"
					fill="#e2e0fc"
					font-size="10"
					font-weight="600"
					font-family="Plus Jakarta Sans, sans-serif"
				>
					{area.score.toFixed(1)}
				</text>
			{/each}
		</svg>
	{:else}
		<div class="h-40 flex flex-col items-center justify-center gap-2">
			<span class="material-symbols-outlined text-3xl text-[var(--color-outline)]/30">radar</span>
			<p class="text-sm text-[var(--color-outline)]">Chat with Mirror to see your life areas</p>
		</div>
	{/if}
</div>
