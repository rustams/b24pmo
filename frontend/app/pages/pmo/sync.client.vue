<script setup lang="ts">
import PmoOverviewPanel from '~/features/pmo/components/PmoOverviewPanel.vue'

const pmo = usePmoStore()
const loading = ref(true)
const isRunning = ref(false)

useHead({ title: 'PMO · Sync' })
definePageMeta({ layout: 'default' })

async function runSync() {
  isRunning.value = true
  try {
    await pmo.triggerInitialSync()
    await pmo.loadSync()
  } finally {
    isRunning.value = false
  }
}

onMounted(async () => {
  try {
    await pmo.loadSync()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <B24Container class="py-8 space-y-4">
    <PmoOverviewPanel title="Sync" :items="pmo.sync" :loading="loading" />
    <B24Button color="air-primary" :loading="isRunning" @click="runSync">Run Initial Sync</B24Button>
  </B24Container>
</template>
