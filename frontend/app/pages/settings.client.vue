<script setup lang="ts">
import type { B24Frame } from '@bitrix24/b24jssdk'

const { t, locales: localesI18n, setLocale } = useI18n()
useHead({ title: 'Настройки PMO Hub' })

const { $logger, initApp } = useAppInit('SettingsPage')
const { $initializeB24Frame } = useNuxtApp()
const apiStore = useApiStore()

const isLoading = ref(true)
const payload = ref<Record<string, unknown> | null>(null)
const installerContract = ref<Record<string, unknown> | null>(null)
const scopeCheck = ref<Record<string, unknown> | null>(null)
const mappingPayload = ref<Record<string, unknown> | null>(null)
const smartProcessesInput = ref('{}')
const listsInput = ref('{}')
const isSavingMapping = ref(false)
const mappingSaveError = ref('')
const mappingSaveSuccess = ref('')
const isDemoMode = computed(() => apiStore.isDemoMode)

const applyMappingToInputs = (mapping: Record<string, unknown> | null) => {
  const safeMapping = mapping ?? {}
  const smartProcesses = (safeMapping.smart_processes as Record<string, unknown> | undefined) ?? {}
  const lists = (safeMapping.lists as Record<string, unknown> | undefined) ?? {}
  smartProcessesInput.value = JSON.stringify(smartProcesses, null, 2)
  listsInput.value = JSON.stringify(lists, null, 2)
}

const refreshInstallerData = async () => {
  const [installationResult, contractResult, scopeResult, mappingResult] = await Promise.allSettled([
    apiStore.getInstallationContext(),
    apiStore.getInstallerContract(),
    apiStore.getInstallerScopeCheck(),
    apiStore.getInstallerMapping()
  ])

  payload.value = installationResult.status === 'fulfilled'
    ? installationResult.value
    : { message: 'Не удалось загрузить данные установки. Используйте demo mode для продолжения.' }

  installerContract.value = contractResult.status === 'fulfilled'
    ? contractResult.value
    : { contract_version: 'unknown', note: 'Контракт временно недоступен' }

  scopeCheck.value = scopeResult.status === 'fulfilled'
    ? scopeResult.value
    : { is_ready: false, note: 'Проверка прав временно недоступна' }

  const mappingResponse = mappingResult.status === 'fulfilled'
    ? mappingResult.value
    : { mapping: {} }
  mappingPayload.value = (mappingResponse.mapping as Record<string, unknown> | undefined) ?? {}
  applyMappingToInputs(mappingPayload.value)
}

const saveMapping = async () => {
  mappingSaveError.value = ''
  mappingSaveSuccess.value = ''
  isSavingMapping.value = true
  try {
    const smartProcesses = JSON.parse(smartProcessesInput.value || '{}') as Record<string, unknown>
    const lists = JSON.parse(listsInput.value || '{}') as Record<string, unknown>
    const response = await apiStore.saveInstallerMapping({
      smart_processes: smartProcesses,
      lists
    })
    mappingPayload.value = (response.mapping as Record<string, unknown> | undefined) ?? {}
    applyMappingToInputs(mappingPayload.value)
    mappingSaveSuccess.value = String(response.message ?? 'Сохранено')
  } catch (error) {
    mappingSaveError.value = 'Не удалось сохранить маппинг. Проверьте JSON и доступы.'
    $logger.warn('Failed to save installer mapping', error)
  } finally {
    isSavingMapping.value = false
  }
}

onMounted(async () => {
  try {
    const $b24: B24Frame = await $initializeB24Frame()
    await initApp($b24, localesI18n, setLocale)
    await $b24.parent.setTitle('Настройки PMO Hub')
    await refreshInstallerData()
    $logger.info('installer settings loaded', {
      installation: payload.value,
      contract: installerContract.value,
      scopeCheck: scopeCheck.value
    })
  } catch (error) {
    $logger.warn('Settings page switched to demo mode due to init error', error)
    await refreshInstallerData()
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="mx-3 my-4">
    <B24Card>
      <template #header>
        <ProseH2>Настроить приложение</ProseH2>
        <ProseP>Эта страница используется для проверки прав и настройки маппинга (RD-102).</ProseP>
      </template>

      <div v-if="isLoading" class="py-4">
        <B24Progress animation="swing" />
      </div>

      <div v-else>
        <ProseP v-if="payload?.message" accent="less">
          {{ payload?.message }}
        </ProseP>
        <B24Badge v-if="isDemoMode" class="mt-2" label="Demo mode" color="air-primary-warning" />

        <ProseH4 class="mt-4">Данные установки из нашей БД</ProseH4>
        <ProsePre class="mt-2">{{ payload }}</ProsePre>

        <ProseH4 class="mt-6">RD-103: Проверка прав и scope</ProseH4>
        <ProsePre class="mt-2">{{ scopeCheck }}</ProsePre>

        <ProseH4 class="mt-6">RD-101 Contract Snapshot</ProseH4>
        <ProsePre class="mt-2">{{ installerContract }}</ProsePre>

        <ProseH4 class="mt-6">RD-102: Маппинг Smart Processes и Lists</ProseH4>
        <ProseP accent="less">Укажите JSON-объекты и сохраните их в backend-хранилище маппингов.</ProseP>

        <div class="mt-2 grid gap-3">
          <label class="flex flex-col gap-1">
            <span class="text-sm opacity-80">Smart Processes (JSON)</span>
            <textarea
              v-model="smartProcessesInput"
              class="min-h-[120px] rounded border border-(--ui-color-accent-soft-blue-2) p-2 text-xs font-mono"
            />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-sm opacity-80">Lists (JSON)</span>
            <textarea
              v-model="listsInput"
              class="min-h-[120px] rounded border border-(--ui-color-accent-soft-blue-2) p-2 text-xs font-mono"
            />
          </label>
          <div class="flex items-center gap-2">
            <B24Button :loading="isSavingMapping" color="air-primary" @click="saveMapping">
              Сохранить маппинг
            </B24Button>
            <ProseP v-if="mappingSaveSuccess" accent="less">{{ mappingSaveSuccess }}</ProseP>
            <ProseP v-if="mappingSaveError" accent="warning">{{ mappingSaveError }}</ProseP>
          </div>
        </div>
        <ProsePre class="mt-2">{{ mappingPayload }}</ProsePre>
      </div>
    </B24Card>
  </div>
</template>
