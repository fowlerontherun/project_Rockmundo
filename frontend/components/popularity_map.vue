<template>
  <canvas ref="canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps<{ songId: number }>()
const canvas = ref<HTMLCanvasElement | null>(null)

onMounted(async () => {
  const resp = await fetch(`/music/metrics/songs/${props.songId}/popularity`)
  const data = await resp.json()
  const breakdown = data.breakdown || {}
  const labels: string[] = []
  const platformSet = new Set<string>()

  // Collect all platforms across regions
  for (const platformData of Object.values(breakdown) as Record<string, number>[]) {
    for (const name of Object.keys(platformData || {})) {
      platformSet.add(name)
    }
  }
  const platforms = Array.from(platformSet)
  const datasetMap: Record<string, number[]> = {}
  platforms.forEach(p => (datasetMap[p] = []))

  // Populate data per region while handling missing platform values
  for (const [region, regionPlatforms] of Object.entries(breakdown)) {
    labels.push(region)
    const rec = regionPlatforms as Record<string, number> | undefined
    platforms.forEach(p => {
      const value = Number(rec?.[p] ?? 0)
      datasetMap[p].push(value)
    })
  }

  const datasets = platforms.map(p => ({ label: p, data: datasetMap[p] }))

  if (canvas.value) {
    new Chart(canvas.value, {
      type: 'bar',
      data: {
        labels,
        datasets,
      },
      options: {
        scales: {
          x: { stacked: true },
          y: { stacked: true },
        },
      },
    })
  }
})
</script>
