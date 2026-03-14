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
const setupError = ref('')
const setupInfo = ref('')
const isDemoMode = computed(() => apiStore.isDemoMode)
const b24Frame = ref<B24Frame | null>(null)

const isScopeReady = computed(() => Boolean(scopeCheck.value?.is_ready))
const missingScopes = computed<string[]>(() => {
  const raw = scopeCheck.value?.missing_scopes
  return Array.isArray(raw) ? raw.map(scope => String(scope)) : []
})

const workplaceTitle = ref('PMO Hub')
const workplaceId = ref<number | null>(null)
const workplaceLink = ref('')
const goalsTypeId = ref<number | null>(null)
const goalsLink = ref('')

const workplaceProgress = ref(0)
const goalsProgress = ref(0)
const isCreatingWorkplace = ref(false)
const isCreatingGoals = ref(false)

const canCreateWorkplace = computed(() => workplaceTitle.value.trim().length > 1 && !isCreatingWorkplace.value)
const canCreateGoals = computed(() => workplaceId.value !== null && !isCreatingGoals.value)

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const toPlainObject = (value: unknown): Record<string, any> => {
  if (!value || typeof value !== 'object') {
    return {}
  }
  return value as Record<string, any>
}

const extractResultData = (raw: unknown): Record<string, any> => {
  const root = toPlainObject(raw)
  const result = toPlainObject(root.result)
  return Object.keys(result).length > 0 ? result : root
}

const normalizeDomain = (domain: string): string => {
  if (!domain) {
    return ''
  }
  if (domain.startsWith('http://') || domain.startsWith('https://')) {
    return domain.replace(/\/$/, '')
  }
  return `https://${domain}`.replace(/\/$/, '')
}

const resolvePortalBaseUrl = (): string => {
  const frame = b24Frame.value
  if (frame) {
    const authData = frame.auth.getAuthData()
    if (authData && authData !== false && typeof authData.domain === 'string') {
      return normalizeDomain(authData.domain)
    }
  }

  const account = toPlainObject(payload.value?.account)
  const domainFromPayload = String(account.domain_url || payload.value?.domain || '').trim()
  return normalizeDomain(domainFromPayload)
}

const buildWorkplaceLink = (id: number): string => {
  const base = resolvePortalBaseUrl()
  if (!base) {
    return ''
  }
  return `${base}/crm/type/list/${id}/`
}

const buildGoalsLink = (entityTypeId: number): string => {
  const base = resolvePortalBaseUrl()
  if (!base) {
    return ''
  }
  return `${base}/crm/type/${entityTypeId}/list/`
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

  void mappingResult
}

const createWorkplace = async () => {
  setupError.value = ''
  setupInfo.value = ''
  isCreatingWorkplace.value = true
  workplaceProgress.value = 10

  try {
    await sleep(250)
    workplaceProgress.value = 30

    if (!b24Frame.value) {
      await sleep(450)
      const demoId = Math.floor(Date.now() / 1000)
      workplaceId.value = demoId
      workplaceLink.value = buildWorkplaceLink(demoId)
      workplaceProgress.value = 100
      setupInfo.value = `Создано цифровое рабочее место "${workplaceTitle.value.trim()}"`
      return
    }

    const response = await b24Frame.value.callMethod('crm.automatedsolution.add', {
      fields: { title: workplaceTitle.value.trim() }
    })
    workplaceProgress.value = 75

    const data = extractResultData(response?.getData ? response.getData() : response)
    const automatedSolution = toPlainObject(data.automatedSolution)
    const createdId = Number(automatedSolution.id || data.id || 0)
    if (!createdId) {
      throw new Error('Не удалось получить ID цифрового рабочего места')
    }

    workplaceId.value = createdId
    workplaceLink.value = buildWorkplaceLink(createdId)
    workplaceProgress.value = 100
    setupInfo.value = `Создано цифровое рабочее место "${workplaceTitle.value.trim()}"`
  } catch (error) {
    workplaceProgress.value = 0
    setupError.value = 'Ошибка создания цифрового рабочего места. Проверьте права CRM и тариф портала.'
    $logger.error('Failed to create automated solution', error)
  } finally {
    isCreatingWorkplace.value = false
  }
}

const createGoalsProcess = async () => {
  if (!workplaceId.value) {
    setupError.value = 'Сначала создайте цифровое рабочее место.'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isCreatingGoals.value = true
  goalsProgress.value = 10

  try {
    await sleep(250)
    goalsProgress.value = 35

    if (!b24Frame.value) {
      await sleep(450)
      const demoEntityTypeId = 1030
      goalsTypeId.value = demoEntityTypeId
      goalsLink.value = buildGoalsLink(demoEntityTypeId)
      goalsProgress.value = 100
      setupInfo.value = 'Смарт-процесс "Цели" создан'
      return
    }

    const response = await b24Frame.value.callMethod('crm.type.add', {
      fields: {
        title: 'Цели',
        customSectionId: workplaceId.value,
        customSections: [workplaceId.value],
        isAutomationEnabled: 'Y',
        isStagesEnabled: 'Y',
        isBizProcEnabled: 'Y'
      }
    })
    goalsProgress.value = 80

    const data = extractResultData(response?.getData ? response.getData() : response)
    const type = toPlainObject(data.type)
    const entityTypeId = Number(type.entityTypeId || type.ENTITY_TYPE_ID || 0)
    const fallbackTypeId = Number(type.id || data.id || 0)
    const resolvedTypeId = entityTypeId || fallbackTypeId
    if (!resolvedTypeId) {
      throw new Error('Не удалось получить ID смарт-процесса')
    }

    goalsTypeId.value = resolvedTypeId
    goalsLink.value = buildGoalsLink(resolvedTypeId)
    goalsProgress.value = 100
    setupInfo.value = 'Смарт-процесс "Цели" создан'
  } catch (error) {
    goalsProgress.value = 0
    setupError.value = 'Ошибка создания смарт-процесса "Цели". Проверьте права CRM и доступность метода crm.type.add.'
    $logger.error('Failed to create Goals smart process', error)
  } finally {
    isCreatingGoals.value = false
  }
}

onMounted(async () => {
  try {
    const $b24: B24Frame = await $initializeB24Frame()
    b24Frame.value = $b24
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
        <ProseP>Новый сценарий RD-102: создаем цифровое рабочее место и смарт-процесс "Цели".</ProseP>
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
          <ProseH4 class="!m-0">Шаг 2. Создать цифровое рабочее место (crm.automatedsolution.add)</ProseH4>
          <ProseP accent="less" class="mt-2">
            Введите название цифрового рабочего места и нажмите "Продолжить".
          </ProseP>
          <div class="mt-3 grid gap-2 md:grid-cols-[1fr_auto]">
            <input
              v-model="workplaceTitle"
              type="text"
              placeholder="Название цифрового рабочего места"
              class="rounded border border-(--ui-color-accent-soft-blue-2) px-3 py-2 text-sm"
            >
            <B24Button :loading="isCreatingWorkplace" :disabled="!canCreateWorkplace" color="air-primary" @click="createWorkplace">
              Продолжить
            </B24Button>
          </div>

          <div v-if="isCreatingWorkplace || workplaceProgress > 0" class="mt-3">
            <B24Progress v-model="workplaceProgress" animation="elastic" />
          </div>
          <ProseP v-if="workplaceId" class="mt-2" accent="less">
            Создано цифровое рабочее место "{{ workplaceTitle.trim() }}"
            <a
              v-if="workplaceLink"
              :href="workplaceLink"
              target="_blank"
              rel="noopener noreferrer"
              class="underline"
            >
              Перейти
            </a>
          </ProseP>
        </div>

        <div class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 3. Создать смарт-процесс "Цели" (crm.type.add)</ProseH4>
          <ProseP accent="less" class="mt-2">
            После создания цифрового рабочего места нажмите "Продолжить".
          </ProseP>
          <div class="mt-3">
            <B24Button :loading="isCreatingGoals" :disabled="!canCreateGoals" color="air-primary" @click="createGoalsProcess">
              Продолжить
            </B24Button>
          </div>
          <div v-if="isCreatingGoals || goalsProgress > 0" class="mt-3">
            <B24Progress v-model="goalsProgress" animation="elastic" />
          </div>
          <ProseP v-if="goalsTypeId" class="mt-2" accent="less">
            Смарт-процесс "Цели" создан
            <a
              v-if="goalsLink"
              :href="goalsLink"
              target="_blank"
              rel="noopener noreferrer"
              class="underline"
            >
              Перейти
            </a>
          </ProseP>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-2">
          <B24Button color="air-secondary-accent-1" @click="refreshInstallerData">
            Обновить данные
          </B24Button>
          <ProseP v-if="setupInfo" accent="less">{{ setupInfo }}</ProseP>
          <ProseP v-if="setupError" accent="warning">{{ setupError }}</ProseP>
        </div>

        <details class="mt-5">
          <summary class="cursor-pointer text-sm opacity-80">Технические данные (debug)</summary>
          <ProseH4 class="mt-3">Данные установки</ProseH4>
          <ProsePre class="mt-2">{{ payload }}</ProsePre>
          <ProseH4 class="mt-3">Scope check</ProseH4>
          <ProsePre class="mt-2">{{ scopeCheck }}</ProsePre>
          <ProseH4 class="mt-3">Contract snapshot</ProseH4>
          <ProsePre class="mt-2">{{ installerContract }}</ProsePre>
          <ProseH4 class="mt-3">Setup runtime</ProseH4>
          <ProsePre class="mt-2">{{ { workplaceId, workplaceLink, goalsTypeId, goalsLink, isDemoMode } }}</ProsePre>
        </details>
      </div>
    </B24Card>
  </div>
</template>
