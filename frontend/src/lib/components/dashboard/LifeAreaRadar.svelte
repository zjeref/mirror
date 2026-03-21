<script lang="ts">
	interface Props {
		areas: { area: string; score: number; trend: string }[];
	}

	let { areas }: Props = $props();

	const size = 200;
	const center = size / 2;
	const maxRadius = 80;
	const levels = 5;

	const areaLabels: Record<string, string> = {
		physical: 'Physical',
		mental: 'Mental',
		career: 'Career',
		habits: 'Habits',
	};

	const trendColors: Record<string, string> = {
		improving: '#22c55e',
		stable: '#94a3b8',
		declining: '#f43f5e',
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
	<h3 class="text-sm font-medium text-slate-300 mb-3">Life Areas</h3>

	{#if areas.length > 0}
		<svg viewBox="0 0 {size} {size}" class="w-full max-w-[250px] mx-auto">
			<!-- Grid levels -->
			{#each Array(levels) as _, level}
				{@const r = ((level + 1) / levels) * maxRadius}
				<polygon
					points={areas.map((_, i) => {
						const p = getPoint(i, r);
						return `${p.x},${p.y}`;
					}).join(' ')}
					fill="none"
					stroke="var(--color-border)"
					stroke-width="0.5"
				/>
			{/each}

			<!-- Axis lines -->
			{#each areas as _, i}
				{@const p = getPoint(i, maxRadius)}
				<line x1={center} y1={center} x2={p.x} y2={p.y} stroke="var(--color-border)" stroke-width="0.5" />
			{/each}

			<!-- Data polygon -->
			<polygon
				points={dataPoints.map((p) => `${p.x},${p.y}`).join(' ')}
				fill="rgba(99, 102, 241, 0.2)"
				stroke="#6366f1"
				stroke-width="2"
			/>

			<!-- Data dots + labels -->
			{#each areas as area, i}
				{@const dp = dataPoints[i]}
				{@const labelPoint = getPoint(i, maxRadius + 20)}
				<circle cx={dp.x} cy={dp.y} r="4" fill={trendColors[area.trend]} />
				<text
					x={labelPoint.x}
					y={labelPoint.y}
					text-anchor="middle"
					dominant-baseline="middle"
					class="text-[10px] fill-slate-400"
				>
					{areaLabels[area.area] ?? area.area}
				</text>
				<text
					x={dp.x}
					y={dp.y - 10}
					text-anchor="middle"
					class="text-[9px] fill-slate-300 font-medium"
				>
					{area.score.toFixed(1)}
				</text>
			{/each}
		</svg>
	{:else}
		<div class="h-40 flex items-center justify-center text-sm text-slate-500">
			Check in to see your life area scores.
		</div>
	{/if}
</div>
