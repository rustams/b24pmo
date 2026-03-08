<script setup lang="ts">
import PmoOverviewPanel from '~/features/pmo/components/PmoOverviewPanel.vue'

const pmo = usePmoStore()
const loading = ref(true)

useHead({ title: 'PMO · RBAC' })
definePageMeta({ layout: 'default' })

onMounted(async () => {
  try {
    await pmo.loadRbac()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <B24Container class="py-8">
    <PmoOverviewPanel title="RBAC" :items="pmo.rbac" :loading="loading" />
  </B24Container>
</template>
