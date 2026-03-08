<script setup lang="ts">
import PmoOverviewPanel from '~/features/pmo/components/PmoOverviewPanel.vue'

const pmo = usePmoStore()
const loading = ref(true)

useHead({ title: 'PMO · Risks' })
definePageMeta({ layout: 'default' })

onMounted(async () => {
  try {
    await pmo.loadRisks()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <B24Container class="py-8">
    <PmoOverviewPanel title="Risks" :items="pmo.risks" :loading="loading" />
  </B24Container>
</template>
