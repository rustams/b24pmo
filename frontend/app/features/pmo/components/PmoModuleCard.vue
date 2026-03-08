<script setup lang="ts">
import type { ModuleCard } from '../shared/types'

defineProps<{
  card: ModuleCard
}>()
</script>

<template>
  <B24Card>
    <template #header>
      <div class="flex items-start justify-between gap-4">
        <div>
          <h3 class="text-lg font-semibold">{{ card.title }}</h3>
          <p class="text-sm text-(--ui-color-base-60)">{{ card.description }}</p>
        </div>
        <B24Button
          color="air-primary"
          size="sm"
          :to="card.route"
          label="Open"
        />
      </div>
    </template>
  </B24Card>
</template>
