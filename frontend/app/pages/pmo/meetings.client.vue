<script setup lang="ts">
import PmoOverviewPanel from '~/features/pmo/components/PmoOverviewPanel.vue'

const pmo = usePmoStore()
const loading = ref(true)

useHead({ title: 'PMO · Meetings' })
definePageMeta({ layout: 'default' })

onMounted(async () => {
  try {
    await pmo.loadMeetings()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <B24Container class="py-8">
    <PmoOverviewPanel title="Meetings" :items="pmo.meetings" :loading="loading" />
  </B24Container>
</template>
