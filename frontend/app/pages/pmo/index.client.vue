<script setup lang="ts">
import PmoModuleCard from '~/features/pmo/components/PmoModuleCard.vue'
import { PMO_MODULE_CARDS } from '~/features/pmo/shared/module-cards'

definePageMeta({
  layout: 'default'
})

useHead({ title: 'PMO Hub' })
</script>

<template>
  <B24Container class="py-8 space-y-6">
    <div>
      <h1 class="text-3xl font-bold">PMO Hub</h1>
      <p class="text-(--ui-color-base-60)">Feature modules aligned with backend PMO domains</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <PmoModuleCard v-for="card in PMO_MODULE_CARDS" :key="card.key" :card="card" />
    </div>
  </B24Container>
</template>
