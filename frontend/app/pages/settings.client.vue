<script setup lang="ts">
import type { B24Frame } from '@bitrix24/b24jssdk'

const { t, locales: localesI18n, setLocale } = useI18n()
useHead({ title: 'Настройки PMO Hub' })

const { $logger, initApp, processErrorGlobal } = useAppInit('SettingsPage')
const { $initializeB24Frame } = useNuxtApp()
const apiStore = useApiStore()

const isLoading = ref(true)
const payload = ref<Record<string, any> | null>(null)

onMounted(async () => {
  try {
    const $b24: B24Frame = await $initializeB24Frame()
    await initApp($b24, localesI18n, setLocale)
    await $b24.parent.setTitle('Настройки PMO Hub')

    payload.value = await apiStore.getInstallationContext()
    $logger.info('installation context loaded', payload.value)
  } catch (error) {
    processErrorGlobal(error)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="mx-3 my-4">
    <B24Card>
      <template #header>
        <ProseH2>Поздравляю, установка прошла успешно</ProseH2>
        <ProseP>Это страница настройки приложения.</ProseP>
      </template>

      <div v-if="isLoading" class="py-4">
        <B24Progress animation="swing" />
      </div>

      <div v-else>
        <ProseP v-if="payload?.message" accent="less">
          {{ payload?.message }}
        </ProseP>

        <ProseH4 class="mt-4">Данные установки из нашей БД</ProseH4>
        <ProsePre class="mt-2">{{ payload }}</ProsePre>
      </div>
    </B24Card>
  </div>
</template>
