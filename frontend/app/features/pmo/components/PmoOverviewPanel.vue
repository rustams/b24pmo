<script setup lang="ts">
import type { FeatureOverview } from '../shared/types'

defineProps<{
  title: string
  items: FeatureOverview[]
  loading: boolean
}>()
</script>

<template>
  <B24Card>
    <template #header>
      <h2 class="text-xl font-semibold">{{ title }}</h2>
    </template>

    <div class="space-y-3 p-4">
      <template v-if="loading">
        <B24Alert color="air-secondary" description="Loading module status..." />
      </template>
      <template v-else>
        <B24Alert
          v-for="item in items"
          :key="item.module"
          color="air-secondary"
          :title="item.module"
          :description="`${item.status} · ${item.next}`"
        />
      </template>
    </div>
  </B24Card>
</template>
