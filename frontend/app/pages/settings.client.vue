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
const smartProcessRows = ref<Array<{ key: string; entityTypeId: string }>>([])
const listRows = ref<Array<{ key: string; iblockId: string }>>([])
const isSavingMapping = ref(false)
const mappingSaveError = ref('')
const mappingSaveSuccess = ref('')
const isDemoMode = computed(() => apiStore.isDemoMode)

const isScopeReady = computed(() => Boolean(scopeCheck.value?.is_ready))
const missingScopes = computed<string[]>(() => {
  const raw = scopeCheck.value?.missing_scopes
  return Array.isArray(raw) ? raw.map(scope => String(scope)) : []
})

const parseSmartProcessRows = (mapping: Record<string, unknown>) => {
  const raw = mapping.smart_processes
  if (!raw || typeof raw !== 'object') {
    return []
  }
  return Object.entries(raw as Record<string, any>).map(([key, value]) => ({
    key,
    entityTypeId: String(value?.entityTypeId ?? '')
  }))
}

const parseListRows = (mapping: Record<string, unknown>) => {
  const raw = mapping.lists
  if (!raw || typeof raw !== 'object') {
    return []
  }
  return Object.entries(raw as Record<string, any>).map(([key, value]) => ({
    key,
    iblockId: String(value?.iblockId ?? '')
  }))
}

const applyMappingToForm = (mapping: Record<string, unknown> | null) => {
  const safeMapping = mapping ?? {}
  smartProcessRows.value = parseSmartProcessRows(safeMapping)
  listRows.value = parseListRows(safeMapping)

  if (smartProcessRows.value.length === 0) {
    smartProcessRows.value = [{ key: 'goals', entityTypeId: '' }]
  }
  if (listRows.value.length === 0) {
    listRows.value = [{ key: 'risks', iblockId: '' }]
  }
}

const serializeMappingFromForm = () => {
  const smart_processes: Record<string, { entityTypeId: number }> = {}
  const lists: Record<string, { iblockId: number }> = {}

  for (const row of smartProcessRows.value) {
    const key = row.key.trim()
    if (!key || !row.entityTypeId.trim()) {
      continue
    }
    smart_processes[key] = { entityTypeId: Number(row.entityTypeId) }
  }

  for (const row of listRows.value) {
    const key = row.key.trim()
    if (!key || !row.iblockId.trim()) {
      continue
    }
    lists[key] = { iblockId: Number(row.iblockId) }
  }

  return { smart_processes, lists }
}

const validateRows = (): string | null => {
  const invalidSmart = smartProcessRows.value.find(
    row => row.entityTypeId.trim() !== '' && !/^\d+$/.test(row.entityTypeId.trim())
  )
  if (invalidSmart) {
    return `Поле Entity Type ID должно быть числом (строка: ${invalidSmart.key || 'без имени'})`
  }

  const invalidList = listRows.value.find(
    row => row.iblockId.trim() !== '' && !/^\d+$/.test(row.iblockId.trim())
  )
  if (invalidList) {
    return `Поле IBlock ID должно быть числом (строка: ${invalidList.key || 'без имени'})`
  }

  return null
}

const addSmartProcessRow = () => {
  smartProcessRows.value.push({ key: '', entityTypeId: '' })
}

const addListRow = () => {
  listRows.value.push({ key: '', iblockId: '' })
}

const removeSmartProcessRow = (index: number) => {
  smartProcessRows.value.splice(index, 1)
  if (smartProcessRows.value.length === 0) {
    addSmartProcessRow()
  }
}

const removeListRow = (index: number) => {
  listRows.value.splice(index, 1)
  if (listRows.value.length === 0) {
    addListRow()
  }
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
  applyMappingToForm(mappingPayload.value)
}

const saveMapping = async () => {
  mappingSaveError.value = ''
  mappingSaveSuccess.value = ''

  const validationError = validateRows()
  if (validationError) {
    mappingSaveError.value = validationError
    return
  }

  isSavingMapping.value = true
  try {
    const response = await apiStore.saveInstallerMapping(serializeMappingFromForm())
    mappingPayload.value = (response.mapping as Record<string, unknown> | undefined) ?? {}
    applyMappingToForm(mappingPayload.value)
    mappingSaveSuccess.value = String(response.message ?? 'Сохранено')
  } catch (error) {
    mappingSaveError.value = 'Не удалось сохранить маппинг. Проверьте соединение и доступы.'
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
        <ProseP>Проверьте права портала и заполните маппинг сущностей для запуска PMO Hub.</ProseP>
      </template>

      <div v-if="isLoading" class="py-4">
        <B24Progress animation="swing" />
      </div>

      <div v-else>
        <ProseP v-if="payload?.message" accent="less">
          {{ payload?.message }}
        </ProseP>
        <B24Badge v-if="isDemoMode" class="mt-2" label="Demo mode" color="air-primary-warning" />

        <div class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <div class="flex flex-wrap items-center gap-2">
            <ProseH4 class="!m-0">Шаг 1. Проверка прав (RD-103)</ProseH4>
            <B24Badge v-if="isScopeReady" label="Готово" color="air-primary-success" />
            <B24Badge v-else label="Требует действий" color="air-primary-alert" />
          </div>
          <ProseP v-if="!isScopeReady" accent="warning" class="mt-2">
            Не хватает scope: {{ missingScopes.join(', ') || 'неизвестно' }}
          </ProseP>
          <ProseP v-else accent="less" class="mt-2">
            Все необходимые права присутствуют.
          </ProseP>
        </div>

        <div class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <div class="flex items-center justify-between gap-2">
            <ProseH4 class="!m-0">Шаг 2. Маппинг Smart Processes (RD-102)</ProseH4>
            <B24Button size="sm" color="air-secondary-accent-1" @click="addSmartProcessRow">
              + Добавить строку
            </B24Button>
          </div>
          <div class="mt-3 grid gap-2">
            <div
              v-for="(row, index) in smartProcessRows"
              :key="`sp-${index}`"
              class="grid gap-2 md:grid-cols-[1fr_180px_auto]"
            >
              <input
                v-model="row.key"
                type="text"
                placeholder="Ключ (например goals)"
                class="rounded border border-(--ui-color-accent-soft-blue-2) px-3 py-2 text-sm"
              >
              <input
                v-model="row.entityTypeId"
                type="text"
                placeholder="Entity Type ID"
                class="rounded border border-(--ui-color-accent-soft-blue-2) px-3 py-2 text-sm"
              >
              <B24Button size="sm" color="air-primary-alert" @click="removeSmartProcessRow(index)">
                Удалить
              </B24Button>
            </div>
          </div>
        </div>

        <div class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <div class="flex items-center justify-between gap-2">
            <ProseH4 class="!m-0">Шаг 3. Маппинг Lists (RD-102)</ProseH4>
            <B24Button size="sm" color="air-secondary-accent-1" @click="addListRow">
              + Добавить строку
            </B24Button>
          </div>
          <div class="mt-3 grid gap-2">
            <div
              v-for="(row, index) in listRows"
              :key="`list-${index}`"
              class="grid gap-2 md:grid-cols-[1fr_180px_auto]"
            >
              <input
                v-model="row.key"
                type="text"
                placeholder="Ключ (например risks)"
                class="rounded border border-(--ui-color-accent-soft-blue-2) px-3 py-2 text-sm"
              >
              <input
                v-model="row.iblockId"
                type="text"
                placeholder="IBlock ID"
                class="rounded border border-(--ui-color-accent-soft-blue-2) px-3 py-2 text-sm"
              >
              <B24Button size="sm" color="air-primary-alert" @click="removeListRow(index)">
                Удалить
              </B24Button>
            </div>
          </div>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-2">
          <B24Button :loading="isSavingMapping" color="air-primary" @click="saveMapping">
            Сохранить настройки
          </B24Button>
          <B24Button color="air-secondary-accent-1" @click="refreshInstallerData">
            Обновить данные
          </B24Button>
          <ProseP v-if="mappingSaveSuccess" accent="less">{{ mappingSaveSuccess }}</ProseP>
          <ProseP v-if="mappingSaveError" accent="warning">{{ mappingSaveError }}</ProseP>
        </div>

        <details class="mt-5">
          <summary class="cursor-pointer text-sm opacity-80">Технические данные (debug)</summary>
          <ProseH4 class="mt-3">Данные установки</ProseH4>
          <ProsePre class="mt-2">{{ payload }}</ProsePre>
          <ProseH4 class="mt-3">Scope check</ProseH4>
          <ProsePre class="mt-2">{{ scopeCheck }}</ProsePre>
          <ProseH4 class="mt-3">Contract snapshot</ProseH4>
          <ProsePre class="mt-2">{{ installerContract }}</ProsePre>
          <ProseH4 class="mt-3">Mapping payload</ProseH4>
          <ProsePre class="mt-2">{{ mappingPayload }}</ProsePre>
        </details>
      </div>
    </B24Card>
  </div>
</template>
