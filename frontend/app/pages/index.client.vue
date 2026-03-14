<script setup lang="ts">
import type { B24Frame } from '@bitrix24/b24jssdk'
import { onMounted } from 'vue'
import { useDashboard } from '@bitrix24/b24ui-nuxt/utils/dashboard'

const { t, locales: localesI18n, setLocale } = useI18n()

useHead({
  title: t('page.index.seo.title')
})

const { $logger, initApp } = useAppInit('IndexPage')
const { $initializeB24Frame } = useNuxtApp()
let $b24: null | B24Frame = null

const apiStore = useApiStore()

const { contextId, isLoading: isLoadingState, load } = useDashboard({ isLoading: ref(false), load: () => {} })
const isLoading = computed({
  get: () => isLoadingState?.value === true,
  set: (value: boolean) => {
    $logger.info(load, value, contextId, isLoadingState?.value)
    load?.(value, contextId)
  }
})

const isInit = ref(false)
onMounted(async () => {
  $logger.info('Hi from index page')

  try {
    isLoading.value = true
    $b24 = await $initializeB24Frame()
    await initApp($b24, localesI18n, setLocale)

    await $b24.parent.setTitle(t('page.index.seo.title'))

    isInit.value = true
  } catch (error) {
    $logger.warn('Index page switched to demo mode due to init error', error)
    isInit.value = true
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-16 h-[calc(100vh-200px)]">
    <B24Card
      v-if="isInit"
      :b24ui="{
        footer: 'flex flex-row flex-wrap items-center justify-start gap-2'
      }"
    >
      <template #header>
        <ProseH2>{{ $t('page.index.message.title') }}</ProseH2>
        <ProseP>{{ $t('page.index.message.line1') }}</ProseP>
        <B24Badge v-if="apiStore.isDemoMode" label="Демо-режим" color="air-primary-warning" />
      </template>

      <ProseP accent="less">
        Для продолжения откройте мастер настройки приложения.
      </ProseP>

      <template #footer>
        <B24Button label="Настроить приложение" color="air-primary" to="/settings" />
      </template>
    </B24Card>
  </div>
</template>
