<script setup lang="ts">
import PmoOverviewPanel from '~/features/pmo/components/PmoOverviewPanel.vue'

const pmo = usePmoStore()
const loading = ref(true)

useHead({ title: 'PMO · Strategy' })
definePageMeta({ layout: 'default' })

onMounted(async () => {
  try {
    await pmo.loadStrategy()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <B24Container class="py-8">
    <PmoOverviewPanel title="Strategy" :items="pmo.strategy" :loading="loading" />
  </B24Container>
</template>
