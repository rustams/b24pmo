<script setup lang="ts">
import PmoOverviewPanel from '~/features/pmo/components/PmoOverviewPanel.vue'

const pmo = usePmoStore()
const loading = ref(true)

useHead({ title: 'PMO · Budget' })
definePageMeta({ layout: 'default' })

onMounted(async () => {
  try {
    await pmo.loadBudget()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <B24Container class="py-8">
    <PmoOverviewPanel title="Budget" :items="pmo.budget" :loading="loading" />
  </B24Container>
</template>
