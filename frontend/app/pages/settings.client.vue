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
const requiredScopes = computed<string[]>(() => {
  const raw = scopeCheck.value?.required_scopes
  return Array.isArray(raw) ? raw.map(scope => String(scope)) : []
})
const currentScopes = computed<string[]>(() => {
  const raw = scopeCheck.value?.current_scopes
  return Array.isArray(raw) ? raw.map(scope => String(scope)) : []
})
const scopeRecommendations = computed<Array<{ scope: string; hint: string }>>(() => {
  const raw = scopeCheck.value?.scope_recommendations
  if (!Array.isArray(raw)) {
    return []
  }
  return raw
    .map(item => item as Record<string, unknown>)
    .map(item => ({
      scope: String(item.scope || ''),
      hint: String(item.hint || '')
    }))
    .filter(item => item.scope.length > 0)
})
const nextSteps = computed<string[]>(() => {
  const raw = scopeCheck.value?.next_steps
  return Array.isArray(raw) ? raw.map(step => String(step)) : []
})
const isPortalAdmin = computed(() => Boolean(scopeCheck.value?.is_admin))

const workplaceTitle = ref('PMO Hub')
const workplaceId = ref<number | null>(null)
const workplaceLink = ref('')
const goalsTypeId = ref<number | null>(null)
const goalsLink = ref('')
const workgroupName = ref('PMO Hub - рабочая группа')
const workgroupId = ref<number | null>(null)
const workgroupLink = ref('')
const isWorkgroupToolsUpdated = ref(false)
const referenceLists = ref<Record<string, { id: number; title: string; items: string[] }>>({})
const referenceFieldBindings = ref<Record<string, number>>({})
const knowledgeBaseId = ref<number | null>(null)
const knowledgeBaseLink = ref('')
const knowledgeBaseBindingStatus = ref<'pending' | 'bound' | 'failed'>('pending')
const knowledgeBaseChangesLog = ref<string[]>([])
const goalsFieldsCreated = ref<Array<{ title: string; code: string; field_id: number | null; status: string }>>([])
const goalsFieldCodesAdded = ref<string[]>([])
const isGoalsCardConfigured = ref(false)
const goalsVerification = ref<{ status: string; missingCodes: string[]; foundCodesCount: number }>({ status: 'pending', missingCodes: [], foundCodesCount: 0 })
const setupState = ref<Record<string, unknown> | null>(null)
const setupStateSaveError = ref('')
const setupStateFromBackend = ref<Record<string, unknown> | null>(null)
const setupStateSource = ref<'backend' | 'demo' | null>(null)
const setupStateLoadedAt = ref<string | null>(null)

const workplaceProgress = ref(0)
const goalsProgress = ref(0)
const workgroupProgress = ref(0)
const referenceListsProgress = ref(0)
const goalsFieldsProgress = ref(0)
const goalsCardProgress = ref(0)
const knowledgeBaseProgress = ref(0)
const verificationProgress = ref(0)
const isCreatingWorkplace = ref(false)
const isCreatingGoals = ref(false)
const isCreatingWorkgroup = ref(false)
const isCreatingReferenceLists = ref(false)
const isCreatingGoalsFields = ref(false)
const isConfiguringGoalsCard = ref(false)
const isCreatingKnowledgeBase = ref(false)
const isVerifyingGoalsSetup = ref(false)

const LISTS_CATALOG: Array<{ key: string; title: string; code: string; items: string[]; targetFieldCode: string }> = [
  { key: 'goal_type', title: 'Тип цели', code: 'goal_type', items: ['Стратегическая', 'Операционная', 'Финансовая'], targetFieldCode: 'GOAL_TYPE' },
  { key: 'goal_priority', title: 'Приоритет', code: 'goal_priority', items: ['Низкий', 'Средний', 'Высокий', 'Критический'], targetFieldCode: 'GOAL_PRIORITY' },
  { key: 'goal_status', title: 'Статус цели', code: 'goal_status', items: ['В работе', 'Достигнута', 'Не достигнута', 'Отменена'], targetFieldCode: 'GOAL_STATUS' },
  { key: 'goal_kpi_unit', title: 'Единица измерения', code: 'goal_kpi_unit', items: ['%', 'шт.', 'руб.', 'дни', 'часы', 'мин.', 'индексы', 'задачи', 'звонки', 'встречи', 'жалобы'], targetFieldCode: 'GOAL_KPI_UNIT' }
]

const canCreateWorkplace = computed(() => workplaceTitle.value.trim().length > 1 && !isCreatingWorkplace.value)
const canCreateGoals = computed(() => workplaceId.value !== null && !isCreatingGoals.value)
const canCreateWorkgroup = computed(() => goalsTypeId.value !== null && !isCreatingWorkgroup.value)
const canCreateReferenceLists = computed(() => workgroupId.value !== null && !isCreatingReferenceLists.value)
const canCreateGoalsFields = computed(() => goalsTypeId.value !== null && Object.keys(referenceLists.value).length >= LISTS_CATALOG.length && !isCreatingGoalsFields.value)
const canConfigureGoalsCard = computed(() => goalsTypeId.value !== null && goalsFieldsCreated.value.length > 0 && !isConfiguringGoalsCard.value)
const canCreateKnowledgeBase = computed(() => workgroupId.value !== null && !isCreatingKnowledgeBase.value)
const canVerifyGoalsSetup = computed(() => goalsTypeId.value !== null && knowledgeBaseBindingStatus.value === 'bound' && !isVerifyingGoalsSetup.value)
const isGoalsFieldsCreated = computed(() => goalsFieldsCreated.value.length > 0)
const isGoalsVerificationPassed = computed(() => goalsVerification.value.status === 'passed')

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
const scrollToStep = async (stepNumber: number) => {
  await nextTick()
  const element = document.getElementById(`installer-step-${stepNumber}`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

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
    try {
      const authData = frame.auth.getAuthData()
      if (authData && authData !== false && typeof authData.domain === 'string') {
        return normalizeDomain(authData.domain)
      }
    } catch (error) {
      $logger.warn('Unable to read auth data from B24 frame, fallback to payload domain', error)
    }
  }

  const account = toPlainObject(payload.value?.account)
  const domainFromPayload = String(account.domain_url || payload.value?.domain || '').trim()
  const normalizedFromPayload = normalizeDomain(domainFromPayload)
  if (normalizedFromPayload) {
    return normalizedFromPayload
  }

  if (typeof window !== 'undefined' && window.location?.origin) {
    return normalizeDomain(window.location.origin)
  }

  return ''
}

const getErrorMessage = (error: unknown): string => {
  if (!error) {
    return ''
  }
  if (typeof error === 'string') {
    return error
  }
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'object') {
    const record = error as Record<string, unknown>
    return String(record.description || record.error_description || record.error || record.message || '')
  }
  return ''
}

const scopeHint = computed(() => {
  if (missingScopes.value.length === 0) {
    return ''
  }
  return `Не хватает разрешений: ${missingScopes.value.join(', ')}`
})

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

const buildWorkgroupLink = (groupId: number): string => {
  const base = resolvePortalBaseUrl()
  if (!base) {
    return ''
  }
  return `${base}/workgroups/group/${groupId}/`
}

const buildKnowledgeBaseLink = (siteId: number): string => {
  const base = resolvePortalBaseUrl()
  if (!base) {
    return ''
  }
  return `${base}/kb/site/${siteId}/`
}

type GoalsFieldDefinition = {
  title: string
  codeTemplate: string
  userTypeId: string
  sort: number
  mandatory: boolean
  multiple: boolean
  listBindingKey?: string
  settings?: Record<string, unknown>
}

const GOALS_FIELD_DEFINITIONS: GoalsFieldDefinition[] = [
  { title: 'Название цели', codeTemplate: 'UF_CRM_XXX_GOAL_TITLE', userTypeId: 'string', sort: 10, mandatory: true, multiple: false },
  { title: 'Описание цели', codeTemplate: 'UF_CRM_XXX_GOAL_DESCRIPTION', userTypeId: 'string', sort: 20, mandatory: false, multiple: false, settings: { rows: 6 } },
  { title: 'Тип цели', codeTemplate: 'UF_CRM_XXX_GOAL_TYPE', userTypeId: 'iblock_element', sort: 30, mandatory: true, multiple: false, listBindingKey: 'goal_type' },
  { title: 'Приоритет', codeTemplate: 'UF_CRM_XXX_GOAL_PRIORITY', userTypeId: 'iblock_element', sort: 40, mandatory: false, multiple: false, listBindingKey: 'goal_priority' },
  { title: 'Статус цели', codeTemplate: 'UF_CRM_XXX_GOAL_STATUS', userTypeId: 'iblock_element', sort: 50, mandatory: true, multiple: false, listBindingKey: 'goal_status' },
  { title: 'Ключевой показатель (KPI)', codeTemplate: 'UF_CRM_XXX_GOAL_KPI', userTypeId: 'string', sort: 60, mandatory: false, multiple: true },
  { title: 'Единица измерения', codeTemplate: 'UF_CRM_XXX_GOAL_KPI_UNIT', userTypeId: 'iblock_element', sort: 70, mandatory: true, multiple: false, listBindingKey: 'goal_kpi_unit' },
  { title: 'Базовое значение', codeTemplate: 'UF_CRM_XXX_GOAL_BASE_VALUE', userTypeId: 'string', sort: 80, mandatory: false, multiple: false },
  { title: 'Целевое значение', codeTemplate: 'UF_CRM_XXX_GOAL_TARGET_VALUE', userTypeId: 'string', sort: 90, mandatory: false, multiple: false },
  { title: 'Фактическое значение KPI', codeTemplate: 'UF_CRM_XXX_GOAL_FACT_VALUE', userTypeId: 'string', sort: 100, mandatory: false, multiple: false },
  { title: 'Прогресс выполнения', codeTemplate: 'UF_CRM_XXX_GOAL_PROGRESS', userTypeId: 'double', sort: 110, mandatory: false, multiple: false },
  { title: 'Владелец цели', codeTemplate: 'UF_CRM_XXX_GOAL_OWNER', userTypeId: 'employee', sort: 120, mandatory: true, multiple: false },
  { title: 'Крайний срок', codeTemplate: 'UF_CRM_XXX_GOAL_DEADLINE', userTypeId: 'date', sort: 130, mandatory: false, multiple: false },
  { title: 'Дата фактического достижения', codeTemplate: 'UF_CRM_XXX_GOAL_ACHIEVE_DATE', userTypeId: 'date', sort: 140, mandatory: false, multiple: false },
  { title: 'Ключевые риски', codeTemplate: 'UF_CRM_XXX_GOAL_KEY_RISKS', userTypeId: 'string', sort: 150, mandatory: true, multiple: false },
  { title: 'Меры минимизации', codeTemplate: 'UF_CRM_XXX_GOAL_RISK_MITIGATION', userTypeId: 'string', sort: 160, mandatory: true, multiple: false },
  { title: 'Связанные инициативы', codeTemplate: 'UF_CRM_XXX_GOAL_LINKED_INITIATIVES', userTypeId: 'string', sort: 170, mandatory: false, multiple: true },
  { title: 'Связанные проекты', codeTemplate: 'UF_CRM_XXX_GOAL_LINKED_PROJECTS', userTypeId: 'string', sort: 180, mandatory: false, multiple: true }
]

const extractGoalCode = (codeTemplate: string): string => {
  const match = codeTemplate.match(/(GAOL|GOAL)[A-Z0-9_]+/)
  return match ? match[0] : codeTemplate.replace(/^UF_CRM_[A-Z0-9]+_/, '')
}

const buildGoalFieldPayload = (field: GoalsFieldDefinition, entityId: string, listBindings: Record<string, number>) => {
  const fieldCode = extractGoalCode(field.codeTemplate).toUpperCase()
  const fullFieldName = `UF_${entityId}_${fieldCode}`.slice(0, 50)
  const settings: Record<string, unknown> = { ...(field.settings || {}) }
  if (field.listBindingKey) {
    const iblockId = listBindings[field.listBindingKey]
    if (iblockId) {
      settings.IBLOCK_ID = iblockId
      settings.LIST_HEIGHT = 1
      settings.DISPLAY = 'LIST'
    }
  }
  return {
    title: field.title,
    fieldName: fullFieldName,
    shortCode: fieldCode,
    userTypeId: field.userTypeId,
    sort: field.sort,
    mandatory: field.mandatory ? 'Y' : 'N',
    multiple: field.multiple ? 'Y' : 'N',
    editFormLabel: { ru: field.title },
    listColumnLabel: { ru: field.title },
    listFilterLabel: { ru: field.title },
    settings
  }
}

const callMethodWithFallback = async (method: string, payloadVariants: Array<Record<string, unknown>>) => {
  if (!b24Frame.value) {
    throw new Error('Фрейм Bitrix24 недоступен')
  }

  let lastError: unknown = null
  for (const params of payloadVariants) {
    try {
      const response = await b24Frame.value.callMethod(method, params)
      return extractResultData(response?.getData ? response.getData() : response)
    } catch (error) {
      lastError = error
    }
  }

  throw lastError ?? new Error(`Не удалось вызвать метод ${method}`)
}

const refreshInstallerData = async () => {
  const [installationResult, contractResult, scopeResult, mappingResult, setupStateResult] = await Promise.allSettled([
    apiStore.getInstallationContext(),
    apiStore.getInstallerContract(),
    apiStore.getInstallerScopeCheck(),
    apiStore.getInstallerMapping(),
    apiStore.getInstallerSetupState()
  ])

  payload.value = installationResult.status === 'fulfilled'
    ? installationResult.value
    : { message: 'Не удалось загрузить данные установки. Используйте демо-режим для продолжения.' }

  installerContract.value = contractResult.status === 'fulfilled'
    ? contractResult.value
    : { contract_version: 'unknown', note: 'Контракт временно недоступен' }

  scopeCheck.value = scopeResult.status === 'fulfilled'
    ? scopeResult.value
    : { is_ready: false, note: 'Проверка прав временно недоступна' }

  void mappingResult

  if (setupStateResult.status === 'fulfilled') {
    const persistedState = setupStateResult.value.setup_state as Record<string, unknown> | undefined
    if (persistedState) {
      setupState.value = persistedState
      setupStateFromBackend.value = persistedState
      setupStateSource.value = apiStore.isDemoMode ? 'demo' : 'backend'
      setupStateLoadedAt.value = new Date().toISOString()
      const workplace = (persistedState.workplace as Record<string, unknown> | undefined) ?? {}
      const goalsProcess = (persistedState.goals_process as Record<string, unknown> | undefined) ?? {}
      const workgroup = (persistedState.workgroup as Record<string, unknown> | undefined) ?? {}
      const referenceListsState = (persistedState.reference_lists as Record<string, unknown> | undefined) ?? {}
      const knowledgeBaseState = (persistedState.knowledge_base as Record<string, unknown> | undefined) ?? {}
      const goalsFieldsState = (persistedState.goals_fields as Record<string, unknown> | undefined) ?? {}
      const goalsCardState = (persistedState.goals_card_configuration as Record<string, unknown> | undefined) ?? {}
      const goalsVerificationState = (persistedState.goals_verification as Record<string, unknown> | undefined) ?? {}

      workplaceTitle.value = String(workplace.title || workplaceTitle.value)
      workplaceId.value = workplace.id === null || workplace.id === undefined ? null : Number(workplace.id)
      workplaceLink.value = String(workplace.link || '')
      goalsTypeId.value = goalsProcess.entity_type_id === null || goalsProcess.entity_type_id === undefined
        ? null
        : Number(goalsProcess.entity_type_id)
      goalsLink.value = String(goalsProcess.link || '')
      workgroupName.value = String(workgroup.name || workgroupName.value)
      workgroupId.value = workgroup.id === null || workgroup.id === undefined ? null : Number(workgroup.id)
      workgroupLink.value = String(workgroup.link || '')
      isWorkgroupToolsUpdated.value = Boolean(workgroup.tools_updated)
      referenceLists.value = (referenceListsState.lists && typeof referenceListsState.lists === 'object')
        ? referenceListsState.lists as Record<string, { id: number; title: string; items: string[] }>
        : {}
      referenceFieldBindings.value = (referenceListsState.field_bindings && typeof referenceListsState.field_bindings === 'object')
        ? Object.fromEntries(
            Object.entries(referenceListsState.field_bindings as Record<string, unknown>)
              .map(([key, value]) => [key, Number(value || 0)])
              .filter(([, value]) => Number.isFinite(value) && value > 0)
          )
        : {}
      knowledgeBaseId.value = knowledgeBaseState.site_id === null || knowledgeBaseState.site_id === undefined
        ? null
        : Number(knowledgeBaseState.site_id)
      knowledgeBaseLink.value = String(knowledgeBaseState.link || '')
      knowledgeBaseBindingStatus.value = String(knowledgeBaseState.binding_status || 'pending') as 'pending' | 'bound' | 'failed'
      knowledgeBaseChangesLog.value = Array.isArray(knowledgeBaseState.changes_log)
        ? knowledgeBaseState.changes_log.map(item => String(item))
        : []
      goalsFieldsCreated.value = Array.isArray(goalsFieldsState.created_fields)
        ? goalsFieldsState.created_fields.map(item => item as { title: string; code: string; field_id: number | null; status: string })
        : []
      goalsFieldCodesAdded.value = Array.isArray(goalsFieldsState.codes_added)
        ? goalsFieldsState.codes_added.map(code => String(code))
        : []
      isGoalsCardConfigured.value = Boolean(goalsCardState.status === 'configured')
      goalsVerification.value = {
        status: String(goalsVerificationState.status || 'pending'),
        missingCodes: Array.isArray(goalsVerificationState.missing_codes) ? goalsVerificationState.missing_codes.map(code => String(code)) : [],
        foundCodesCount: Number(goalsVerificationState.found_codes_count || 0)
      }
    }
  }
}

const refreshSetupStateFromBackend = async () => {
  try {
    const response = await apiStore.getInstallerSetupState()
    const persisted = (response.setup_state as Record<string, unknown> | undefined) ?? null
    setupStateFromBackend.value = persisted
    setupStateSource.value = apiStore.isDemoMode ? 'demo' : 'backend'
    setupStateLoadedAt.value = new Date().toISOString()
  } catch {
    setupStateFromBackend.value = null
    setupStateSource.value = null
    setupStateLoadedAt.value = null
  }
}

const persistSetupState = async (partialState: Record<string, unknown>) => {
  setupStateSaveError.value = ''
  const current = (setupState.value ?? {}) as Record<string, unknown>
  const currentWorkplace = (current.workplace as Record<string, unknown> | undefined) ?? {}
  const currentGoals = (current.goals_process as Record<string, unknown> | undefined) ?? {}
  const currentWorkgroup = (current.workgroup as Record<string, unknown> | undefined) ?? {}
  const currentReferenceLists = (current.reference_lists as Record<string, unknown> | undefined) ?? {}
  const currentKnowledgeBase = (current.knowledge_base as Record<string, unknown> | undefined) ?? {}
  const currentGoalsFields = (current.goals_fields as Record<string, unknown> | undefined) ?? {}
  const currentGoalsCard = (current.goals_card_configuration as Record<string, unknown> | undefined) ?? {}
  const partialWorkplace = (partialState.workplace as Record<string, unknown> | undefined) ?? {}
  const partialGoals = (partialState.goals_process as Record<string, unknown> | undefined) ?? {}
  const partialWorkgroup = (partialState.workgroup as Record<string, unknown> | undefined) ?? {}
  const partialReferenceLists = (partialState.reference_lists as Record<string, unknown> | undefined) ?? {}
  const partialKnowledgeBase = (partialState.knowledge_base as Record<string, unknown> | undefined) ?? {}
  const partialGoalsFields = (partialState.goals_fields as Record<string, unknown> | undefined) ?? {}
  const partialGoalsCard = (partialState.goals_card_configuration as Record<string, unknown> | undefined) ?? {}
  const partialCompleted = partialState.completed_steps
  const currentCompleted = Array.isArray(current.completed_steps) ? current.completed_steps.map(step => String(step)) : []
  const mergedCompleted = Array.isArray(partialCompleted)
    ? Array.from(new Set([...currentCompleted, ...partialCompleted.map(step => String(step))]))
    : currentCompleted

  const mergedState = {
    ...current,
    ...partialState,
    workplace: {
      ...currentWorkplace,
      ...partialWorkplace
    },
    goals_process: {
      ...currentGoals,
      ...partialGoals
    },
    workgroup: {
      ...currentWorkgroup,
      ...partialWorkgroup
    },
    reference_lists: {
      ...currentReferenceLists,
      ...partialReferenceLists
    },
    knowledge_base: {
      ...currentKnowledgeBase,
      ...partialKnowledgeBase
    },
    goals_fields: {
      ...currentGoalsFields,
      ...partialGoalsFields
    },
    goals_card_configuration: {
      ...currentGoalsCard,
      ...partialGoalsCard
    },
    completed_steps: mergedCompleted
  }

  try {
    const response = await apiStore.saveInstallerSetupState(mergedState)
    const saved = (response.setup_state as Record<string, unknown> | undefined) ?? mergedState
    setupState.value = saved
    setupStateFromBackend.value = saved
    setupStateSource.value = apiStore.isDemoMode ? 'demo' : 'backend'
    setupStateLoadedAt.value = new Date().toISOString()
  } catch (error) {
    setupStateSaveError.value = 'Не удалось сохранить состояние мастера настройки.'
    $logger.warn('Failed to persist installer setup state', error)
  }
}

const createWorkplace = async () => {
  setupError.value = ''
  setupInfo.value = ''
  isCreatingWorkplace.value = true
  workplaceProgress.value = 10

  try {
    await sleep(250)
    workplaceProgress.value = 30

    if (isDemoMode.value || !b24Frame.value) {
      await sleep(450)
      const demoId = Math.floor(Date.now() / 1000)
      workplaceId.value = demoId
      workplaceLink.value = buildWorkplaceLink(demoId)
      workplaceProgress.value = 100
      setupInfo.value = `Создано цифровое рабочее место "${workplaceTitle.value.trim()}" (демо-режим)`
      await persistSetupState({
        current_step: 'workplace_created',
        workplace: {
          title: workplaceTitle.value.trim(),
          id: demoId,
          link: workplaceLink.value,
          status: 'created'
        },
        completed_steps: ['scope_check', 'workplace_created']
      })
      await scrollToStep(3)
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
    await persistSetupState({
      current_step: 'workplace_created',
      workplace: {
        title: workplaceTitle.value.trim(),
        id: createdId,
        link: workplaceLink.value,
        status: 'created'
      },
      completed_steps: ['scope_check', 'workplace_created']
    })
    await scrollToStep(3)
  } catch (error) {
    workplaceProgress.value = 0
    const details = getErrorMessage(error)
    const hint = scopeHint.value ? ` ${scopeHint.value}.` : ''
    setupError.value = `Ошибка создания цифрового рабочего места.${hint}${details ? ` Детали: ${details}` : ''}`
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

    if (isDemoMode.value || !b24Frame.value) {
      await sleep(450)
      const demoEntityTypeId = 1030
      goalsTypeId.value = demoEntityTypeId
      goalsLink.value = buildGoalsLink(demoEntityTypeId)
      goalsProgress.value = 100
      setupInfo.value = 'Смарт-процесс "Цели" создан (демо-режим)'
      await persistSetupState({
        current_step: 'goals_created',
        goals_process: {
          entity_type_id: demoEntityTypeId,
          link: goalsLink.value,
          status: 'created'
        },
        completed_steps: ['scope_check', 'workplace_created', 'goals_created']
      })
      await scrollToStep(4)
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
    await persistSetupState({
      current_step: 'goals_created',
      goals_process: {
        entity_type_id: resolvedTypeId,
        link: goalsLink.value,
        status: 'created'
      },
      completed_steps: ['scope_check', 'workplace_created', 'goals_created']
    })
    await scrollToStep(4)
  } catch (error) {
    goalsProgress.value = 0
    const details = getErrorMessage(error)
    const hint = scopeHint.value ? ` ${scopeHint.value}.` : ''
    setupError.value = `Ошибка создания смарт-процесса "Цели".${hint}${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to create Goals smart process', error)
  } finally {
    isCreatingGoals.value = false
  }
}

const createWorkgroup = async () => {
  if (!goalsTypeId.value) {
    setupError.value = 'Сначала создайте смарт-процесс "Цели".'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isCreatingWorkgroup.value = true
  workgroupProgress.value = 10

  try {
    await sleep(250)
    workgroupProgress.value = 35

    if (isDemoMode.value || !b24Frame.value) {
      await sleep(500)
      const demoGroupId = Math.floor(Date.now() / 1000) + 200
      workgroupId.value = demoGroupId
      workgroupLink.value = buildWorkgroupLink(demoGroupId)
      isWorkgroupToolsUpdated.value = true
      workgroupProgress.value = 100
      setupInfo.value = `Рабочая группа "${workgroupName.value}" создана (демо-режим)`
      await persistSetupState({
        current_step: 'workgroup_created',
        workgroup: {
          id: demoGroupId,
          name: workgroupName.value,
          link: workgroupLink.value,
          status: 'created',
          tools_updated: true
        },
        completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'workgroup_created']
      })
      await scrollToStep(7)
      return
    }

    const createData = await callMethodWithFallback('sonet_group.create', [
      {
        arFields: {
          NAME: workgroupName.value,
          DESCRIPTION: 'Рабочая группа PMO Hub для списков и базы знаний',
          VISIBLE: 'Y',
          OPENED: 'N',
          INITIATE_PERMS: 'E',
          SPAM_PERMS: 'E',
          PROJECT: 'Y'
        }
      },
      {
        NAME: workgroupName.value,
        DESCRIPTION: 'Рабочая группа PMO Hub для списков и базы знаний',
        VISIBLE: 'Y',
        OPENED: 'N',
        INITIATE_PERMS: 'E',
        SPAM_PERMS: 'E',
        PROJECT: 'Y'
      }
    ])
    workgroupProgress.value = 60

    const createdGroupId = Number(createData.result || createData.id || createData.groupId || 0)
    if (!createdGroupId) {
      throw new Error('Не удалось получить ID рабочей группы')
    }

    await callMethodWithFallback('sonet_group.update', [
      { GROUP_ID: createdGroupId, NAME: workgroupName.value },
      {
        GROUP_ID: createdGroupId,
        NAME: workgroupName.value,
        FEATURES: {
          tasks: 'Y',
          files: 'Y',
          chat: 'Y',
          lists: 'Y',
          wiki: 'Y'
        }
      }
    ])
    workgroupProgress.value = 100

    workgroupId.value = createdGroupId
    workgroupLink.value = buildWorkgroupLink(createdGroupId)
    isWorkgroupToolsUpdated.value = true
    setupInfo.value = `Рабочая группа "${workgroupName.value}" создана и обновлена`
    await persistSetupState({
      current_step: 'workgroup_created',
      workgroup: {
        id: createdGroupId,
        name: workgroupName.value,
        link: workgroupLink.value,
        status: 'created',
        tools_updated: true
      },
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'workgroup_created']
    })
    await scrollToStep(7)
  } catch (error) {
    workgroupProgress.value = 0
    const details = getErrorMessage(error)
    setupError.value = `Ошибка создания рабочей группы.${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to create workgroup', error)
  } finally {
    isCreatingWorkgroup.value = false
  }
}

const createReferenceLists = async () => {
  if (!workgroupId.value) {
    setupError.value = 'Сначала создайте рабочую группу.'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isCreatingReferenceLists.value = true
  referenceListsProgress.value = 10

  try {
    await sleep(250)
    referenceListsProgress.value = 20

    const listsState: Record<string, { id: number; title: string; items: string[] }> = {}
    const fieldBindings: Record<string, number> = {}

    if (isDemoMode.value || !b24Frame.value) {
      await sleep(800)
      LISTS_CATALOG.forEach((listItem, index) => {
        const listId = 7000 + index
        listsState[listItem.key] = {
          id: listId,
          title: listItem.title,
          items: listItem.items
        }
        fieldBindings[listItem.key] = listId
      })
      referenceListsProgress.value = 100
    } else {
      for (let index = 0; index < LISTS_CATALOG.length; index += 1) {
        const listItem = LISTS_CATALOG[index]
        const addData = await callMethodWithFallback('lists.add', [
          {
            IBLOCK_TYPE_ID: 'lists_socnet',
            IBLOCK_CODE: `${listItem.code}_${workgroupId.value}`,
            SOCNET_GROUP_ID: workgroupId.value,
            FIELDS: {
              NAME: listItem.title,
              DESCRIPTION: `Справочник PMO Hub: ${listItem.title}`,
              SORT: 500 + index * 10,
              BIZPROC: 'N'
            }
          }
        ])
        const iblockId = Number(addData.result || addData.id || 0)
        if (!iblockId) {
          throw new Error(`Не удалось получить ID списка "${listItem.title}"`)
        }

        for (let itemIndex = 0; itemIndex < listItem.items.length; itemIndex += 1) {
          const itemTitle = listItem.items[itemIndex]
          await callMethodWithFallback('lists.element.add', [
            {
              IBLOCK_TYPE_ID: 'lists_socnet',
              IBLOCK_ID: iblockId,
              ELEMENT_CODE: `${listItem.code}_${itemIndex + 1}`,
              FIELDS: {
                NAME: itemTitle
              }
            }
          ])
        }

        listsState[listItem.key] = {
          id: iblockId,
          title: listItem.title,
          items: listItem.items
        }
        fieldBindings[listItem.key] = iblockId
        referenceListsProgress.value = Math.min(95, 20 + Math.floor(((index + 1) / LISTS_CATALOG.length) * 75))
      }
      referenceListsProgress.value = 100
    }

    referenceLists.value = listsState
    referenceFieldBindings.value = fieldBindings
    setupInfo.value = 'Справочники рабочей группы созданы'
    await persistSetupState({
      current_step: 'reference_lists_created',
      reference_lists: {
        status: 'created',
        group_id: workgroupId.value,
        lists: listsState,
        field_bindings: fieldBindings
      },
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'workgroup_created', 'reference_lists_created']
    })
    await scrollToStep(8)
  } catch (error) {
    referenceListsProgress.value = 0
    const details = getErrorMessage(error)
    setupError.value = `Ошибка создания списков рабочей группы.${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to create reference lists', error)
  } finally {
    isCreatingReferenceLists.value = false
  }
}

const createGoalsFields = async () => {
  if (!goalsTypeId.value) {
    setupError.value = 'Сначала создайте смарт-процесс "Цели".'
    return
  }
  if (!workgroupId.value) {
    setupError.value = 'Сначала создайте рабочую группу и справочники.'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isCreatingGoalsFields.value = true
  goalsFieldsProgress.value = 10

  try {
    await sleep(250)
    goalsFieldsProgress.value = 25

    const createdFields: Array<{ title: string; code: string; field_id: number | null; status: string }> = []
    const entityId = `CRM_${goalsTypeId.value}`
    const listBindings = referenceFieldBindings.value
    if (isDemoMode.value || !b24Frame.value) {
      await sleep(600)
      GOALS_FIELD_DEFINITIONS.forEach((field, index) => {
        createdFields.push({
          title: field.title,
          code: extractGoalCode(field.codeTemplate),
          field_id: 5000 + index,
          status: 'created'
        })
      })
      goalsFieldsProgress.value = 100
    } else {
      for (let index = 0; index < GOALS_FIELD_DEFINITIONS.length; index += 1) {
        const definition = GOALS_FIELD_DEFINITIONS[index]
        const fieldPayload = buildGoalFieldPayload(definition, entityId, listBindings)
        const data = await callMethodWithFallback('userfieldconfig.add', [
          {
            moduleId: 'crm',
            field: {
              entityId,
              fieldName: fieldPayload.fieldName,
              userTypeId: fieldPayload.userTypeId,
              sort: fieldPayload.sort,
              mandatory: fieldPayload.mandatory,
              multiple: fieldPayload.multiple,
              editFormLabel: fieldPayload.editFormLabel,
              listColumnLabel: fieldPayload.listColumnLabel,
              listFilterLabel: fieldPayload.listFilterLabel,
              settings: fieldPayload.settings
            }
          }
        ])

        const fieldId = Number(data.id || data.fieldId || data.field_id || data.result || 0) || null
        createdFields.push({
          title: definition.title,
          code: String(fieldPayload.shortCode),
          field_id: fieldId,
          status: 'created'
        })
        goalsFieldsProgress.value = Math.min(95, 25 + Math.floor(((index + 1) / GOALS_FIELD_DEFINITIONS.length) * 70))
      }
      goalsFieldsProgress.value = 100
    }

    goalsFieldsCreated.value = createdFields
    goalsFieldCodesAdded.value = createdFields.map(field => field.code)
    setupInfo.value = 'Поля для смарт-процесса "Цели" созданы'
    await persistSetupState({
      current_step: 'goals_fields_created',
      goals_fields: {
        status: 'created',
        created_fields: createdFields,
        codes_added: goalsFieldCodesAdded.value
      },
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'workgroup_created', 'reference_lists_created', 'goals_fields_created']
    })
    await scrollToStep(5)
  } catch (error) {
    goalsFieldsProgress.value = 0
    const details = getErrorMessage(error)
    const hint = scopeHint.value ? ` ${scopeHint.value}.` : ''
    setupError.value = `Ошибка создания полей смарт-процесса "Цели".${hint}${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to create Goals fields', error)
  } finally {
    isCreatingGoalsFields.value = false
  }
}

const configureGoalsCard = async () => {
  if (!goalsTypeId.value) {
    setupError.value = 'Сначала создайте смарт-процесс "Цели".'
    return
  }
  if (goalsFieldCodesAdded.value.length === 0) {
    setupError.value = 'Сначала создайте поля смарт-процесса "Цели".'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isConfiguringGoalsCard.value = true
  goalsCardProgress.value = 10

  try {
    await sleep(250)
    goalsCardProgress.value = 30

    const details: Record<string, unknown> = {
      field_codes: goalsFieldCodesAdded.value
    }

    if (isDemoMode.value || !b24Frame.value) {
      await sleep(700)
      details.mode = 'demo'
      goalsCardProgress.value = 100
    } else {
      await callMethodWithFallback('crm.item.details.configuration.reset', [
        { entityTypeId: goalsTypeId.value, scope: 'common' },
        { entityTypeId: goalsTypeId.value }
      ])
      goalsCardProgress.value = 45

      const currentConfiguration = await callMethodWithFallback('crm.item.details.configuration.get', [
        { entityTypeId: goalsTypeId.value, scope: 'common' },
        { entityTypeId: goalsTypeId.value }
      ])
      details.before = currentConfiguration

      const preparedConfiguration = {
        view: 'common',
        sections: [
          {
            id: 'main',
            title: 'Общий вид карточки',
            elements: goalsFieldCodesAdded.value
          }
        ]
      }

      const setResult = await callMethodWithFallback('crm.item.details.configuration.set', [
        { entityTypeId: goalsTypeId.value, scope: 'common', configuration: preparedConfiguration },
        { entityTypeId: goalsTypeId.value, scope: 'common', config: preparedConfiguration },
        { entityTypeId: goalsTypeId.value, configuration: preparedConfiguration }
      ])
      details.after_set = setResult
      goalsCardProgress.value = 80

      const forceResult = await callMethodWithFallback('crm.item.details.configuration.forceCommonScopeForAll', [
        { entityTypeId: goalsTypeId.value },
        { entityTypeId: goalsTypeId.value, value: true },
        {}
      ])
      details.after_force_common_scope = forceResult
      goalsCardProgress.value = 100
    }

    isGoalsCardConfigured.value = true
    setupInfo.value = 'Настройка карточки цели завершена'
    await persistSetupState({
      current_step: 'goals_card_configured',
      goals_card_configuration: {
        status: 'configured',
        common_scope_forced: true,
        details
      },
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'workgroup_created', 'reference_lists_created', 'goals_fields_created', 'goals_card_configured']
    })
    await scrollToStep(8)
  } catch (error) {
    goalsCardProgress.value = 0
    const details = getErrorMessage(error)
    const hint = scopeHint.value ? ` ${scopeHint.value}.` : ''
    setupError.value = `Ошибка настройки карточки цели.${hint}${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to configure Goals card', error)
  } finally {
    isConfiguringGoalsCard.value = false
  }
}

const createKnowledgeBase = async () => {
  if (!workgroupId.value) {
    setupError.value = 'Сначала создайте рабочую группу.'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isCreatingKnowledgeBase.value = true
  knowledgeBaseProgress.value = 10

  try {
    await sleep(250)
    knowledgeBaseProgress.value = 30

    const changesLog = [
      `Цифровое рабочее место: ${workplaceTitle.value} (ID: ${workplaceId.value || 'n/a'})`,
      `Смарт-процесс Цели: ${goalsTypeId.value || 'n/a'}`,
      `Рабочая группа: ${workgroupName.value} (ID: ${workgroupId.value})`,
      `Справочников создано: ${Object.keys(referenceLists.value).length}`,
      `Полей создано: ${goalsFieldsCreated.value.length}`
    ]

    if (isDemoMode.value || !b24Frame.value) {
      await sleep(500)
      const demoSiteId = Math.floor(Date.now() / 1000) + 300
      knowledgeBaseId.value = demoSiteId
      knowledgeBaseLink.value = buildKnowledgeBaseLink(demoSiteId)
      knowledgeBaseBindingStatus.value = 'bound'
      knowledgeBaseChangesLog.value = changesLog
      knowledgeBaseProgress.value = 100
      setupInfo.value = 'База знаний создана и привязана к рабочей группе (демо-режим)'
      await persistSetupState({
        current_step: 'knowledge_base_created',
        knowledge_base: {
          status: 'created',
          site_id: demoSiteId,
          link: knowledgeBaseLink.value,
          binding_status: 'bound',
          changes_log: changesLog
        },
        completed_steps: [
          'scope_check',
          'workplace_created',
          'goals_created',
          'workgroup_created',
          'reference_lists_created',
          'goals_fields_created',
          'goals_card_configured',
          'knowledge_base_created'
        ]
      })
      await scrollToStep(9)
      return
    }

    const siteData = await callMethodWithFallback('landing.site.add', [
      {
        scope: 'KNOWLEDGE',
        fields: {
          TITLE: `PMO Hub KB (${workgroupName.value})`,
          CODE: '',
          TYPE: 'KNOWLEDGE',
          DESCRIPTION: 'База знаний PMO Hub'
        }
      }
    ])
    knowledgeBaseProgress.value = 65

    const siteId = Number(siteData.result || siteData.id || siteData.siteId || 0)
    if (!siteId) {
      throw new Error('Не удалось получить ID базы знаний')
    }

    await callMethodWithFallback('landing.site.bindingToGroup', [
      { id: siteId, groupId: workgroupId.value }
    ])
    knowledgeBaseProgress.value = 100

    knowledgeBaseId.value = siteId
    knowledgeBaseLink.value = buildKnowledgeBaseLink(siteId)
    knowledgeBaseBindingStatus.value = 'bound'
    knowledgeBaseChangesLog.value = changesLog
    setupInfo.value = 'База знаний создана и привязана к рабочей группе'
    await persistSetupState({
      current_step: 'knowledge_base_created',
      knowledge_base: {
        status: 'created',
        site_id: siteId,
        link: knowledgeBaseLink.value,
        binding_status: 'bound',
        changes_log: changesLog
      },
      completed_steps: [
        'scope_check',
        'workplace_created',
        'goals_created',
        'workgroup_created',
        'reference_lists_created',
        'goals_fields_created',
        'goals_card_configured',
        'knowledge_base_created'
      ]
    })
    await scrollToStep(9)
  } catch (error) {
    knowledgeBaseProgress.value = 0
    knowledgeBaseBindingStatus.value = 'failed'
    const details = getErrorMessage(error)
    setupError.value = `Ошибка создания базы знаний.${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to create knowledge base', error)
  } finally {
    isCreatingKnowledgeBase.value = false
  }
}

const toRecordArray = (value: unknown): Array<Record<string, unknown>> => {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter(item => item && typeof item === 'object').map(item => item as Record<string, unknown>)
}

const extractFieldCode = (item: Record<string, unknown>): string => {
  const raw = item.fieldName || item.FIELD_NAME || item.name || item.code || ''
  const normalized = String(raw).trim().toUpperCase()
  return normalized.replace(/^UF_[A-Z0-9]+_/, '')
}

const verifyGoalsSetup = async () => {
  if (!goalsTypeId.value) {
    setupError.value = 'Сначала создайте смарт-процесс "Цели".'
    return
  }

  setupError.value = ''
  setupInfo.value = ''
  isVerifyingGoalsSetup.value = true
  verificationProgress.value = 10

  try {
    const expectedCodes = GOALS_FIELD_DEFINITIONS.map(field => extractGoalCode(field.codeTemplate).toUpperCase())
    await sleep(250)
    verificationProgress.value = 35

    let actualCodes: string[] = []
    if (isDemoMode.value || !b24Frame.value) {
      await sleep(550)
      actualCodes = expectedCodes
      verificationProgress.value = 80
    } else {
      const listData = await callMethodWithFallback('userfieldconfig.list', [
        {
          moduleId: 'crm',
          select: { 0: '*', language: 'ru' },
          filter: { entityId: `CRM_${goalsTypeId.value}` },
          order: { id: 'ASC' }
        }
      ])

      const records = [
        ...toRecordArray(listData.fields),
        ...toRecordArray(listData.items),
        ...toRecordArray(listData.userFields),
        ...toRecordArray(listData.result)
      ]
      actualCodes = records.map(extractFieldCode).filter(code => code.length > 0)
      verificationProgress.value = 80
    }

    const actualCodeSet = new Set(actualCodes)
    const missingCodes = expectedCodes.filter(code => !actualCodeSet.has(code))
    const listsReady = Object.keys(referenceLists.value).length >= LISTS_CATALOG.length
    const kbReady = knowledgeBaseBindingStatus.value === 'bound'
    const status = (missingCodes.length === 0 && isGoalsCardConfigured.value && listsReady && kbReady) ? 'passed' : 'failed'
    goalsVerification.value = {
      status,
      missingCodes,
      foundCodesCount: actualCodes.length
    }

    verificationProgress.value = 100
    if (status === 'passed') {
      setupInfo.value = 'Проверка завершена: все поля и настройка карточки применены.'
    } else {
      setupError.value = `Проверка завершена с замечаниями. Не найдены поля: ${missingCodes.join(', ') || 'нет'}.`
    }

    await persistSetupState({
      current_step: 'goals_verification_done',
      goals_verification: {
        status,
        missing_codes: missingCodes,
        found_codes_count: actualCodes.length,
        checked_at_utc: new Date().toISOString()
      },
      completed_steps: [
        'scope_check',
        'workplace_created',
        'goals_created',
        'workgroup_created',
        'reference_lists_created',
        'goals_fields_created',
        'goals_card_configured',
        'knowledge_base_created',
        'goals_verification_done'
      ]
    })
  } catch (error) {
    verificationProgress.value = 0
    const details = getErrorMessage(error)
    setupError.value = `Ошибка проверки созданных полей и карточки.${details ? ` Детали: ${details}` : ''}`
    $logger.error('Failed to verify Goals setup', error)
  } finally {
    isVerifyingGoalsSetup.value = false
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
        <B24Badge v-if="isDemoMode" class="mt-2" label="Демо-режим" color="air-primary-warning" />

        <div id="installer-step-1" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <div class="flex flex-wrap items-center gap-2">
            <ProseH4 class="!m-0">Шаг 1. Проверка прав (RD-103)</ProseH4>
            <B24Badge v-if="isScopeReady" label="Готово" color="air-primary-success" />
            <B24Badge v-else label="Требует действий" color="air-primary-alert" />
          </div>
          <div class="mt-3 grid gap-2">
            <ProseP accent="less">Текущий пользователь: {{ isPortalAdmin ? 'Администратор' : 'Не администратор' }}</ProseP>
            <ProseP accent="less">Обязательные разрешения: {{ requiredScopes.join(', ') || 'не определены' }}</ProseP>
            <ProseP accent="less">Текущие разрешения: {{ currentScopes.join(', ') || 'не определены' }}</ProseP>
            <ProseP v-if="!isScopeReady" accent="warning">
              Не хватает разрешений: {{ missingScopes.join(', ') || 'неизвестно' }}
            </ProseP>
            <ProseP v-else accent="less">Все необходимые права присутствуют.</ProseP>
          </div>

          <div v-if="scopeRecommendations.length > 0" class="mt-3">
            <ProseH4 class="!m-0">Что нужно исправить</ProseH4>
            <ul class="mt-2 list-disc pl-5 text-sm">
              <li v-for="item in scopeRecommendations" :key="item.scope">
                <span class="font-semibold">{{ item.scope }}:</span> {{ item.hint }}
              </li>
            </ul>
          </div>

          <div v-if="nextSteps.length > 0" class="mt-3">
            <ProseH4 class="!m-0">Дальнейшие действия</ProseH4>
            <ol class="mt-2 list-decimal pl-5 text-sm">
              <li v-for="(step, index) in nextSteps" :key="`next-step-${index}`">
                {{ step }}
              </li>
            </ol>
          </div>
        </div>

        <div id="installer-step-2" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
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

        <div id="installer-step-3" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
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

        <div id="installer-step-4" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 4. Создать рабочую группу (sonet_group.create)</ProseH4>
          <ProseP accent="less" class="mt-2">
            Создаем рабочую группу "PMO Hub - рабочая группа" и включаем необходимые инструменты.
          </ProseP>
          <div class="mt-3 grid gap-2 md:grid-cols-[1fr_auto]">
            <input
              v-model="workgroupName"
              type="text"
              class="rounded border border-(--ui-color-accent-soft-blue-2) px-3 py-2 text-sm"
            >
            <B24Button :loading="isCreatingWorkgroup" :disabled="!canCreateWorkgroup" color="air-primary" @click="createWorkgroup">
              Продолжить
            </B24Button>
          </div>
          <div v-if="isCreatingWorkgroup || workgroupProgress > 0" class="mt-3">
            <B24Progress v-model="workgroupProgress" animation="elastic" />
          </div>
          <ProseP v-if="workgroupId" class="mt-2" accent="less">
            Рабочая группа создана (ID: {{ workgroupId }}), инструменты обновлены: {{ isWorkgroupToolsUpdated ? 'да' : 'нет' }}.
            <a
              v-if="workgroupLink"
              :href="workgroupLink"
              target="_blank"
              rel="noopener noreferrer"
              class="underline"
            >
              Перейти
            </a>
          </ProseP>
        </div>

        <div id="installer-step-5" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 5. Создать списки рабочей группы (lists.add / lists.element.add)</ProseH4>
          <ProseP accent="less" class="mt-2">
            Создаем справочники: Тип цели, Приоритет, Статус цели, Единица измерения, и сохраняем ID списков.
          </ProseP>
          <div class="mt-3">
            <B24Button :loading="isCreatingReferenceLists" :disabled="!canCreateReferenceLists" color="air-primary" @click="createReferenceLists">
              Продолжить
            </B24Button>
          </div>
          <div v-if="isCreatingReferenceLists || referenceListsProgress > 0" class="mt-3">
            <B24Progress v-model="referenceListsProgress" animation="elastic" />
          </div>
          <ProseP v-if="Object.keys(referenceLists).length > 0" class="mt-2" accent="less">
            Списки созданы: {{ Object.values(referenceLists).map(item => `${item.title} (#${item.id})`).join(', ') }}
          </ProseP>
        </div>

        <div id="installer-step-6" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 6. Создать поля смарт-процесса "Цели"</ProseH4>
          <ProseP accent="less" class="mt-2">
            Создаем поля из GOALS.md. Для полей типа "Привязка к элементам инф. блоков" используем ID списков рабочей группы.
          </ProseP>
          <div class="mt-3">
            <B24Button :loading="isCreatingGoalsFields" :disabled="!canCreateGoalsFields" color="air-primary" @click="createGoalsFields">
              Продолжить
            </B24Button>
          </div>
          <div v-if="isCreatingGoalsFields || goalsFieldsProgress > 0" class="mt-3">
            <B24Progress v-model="goalsFieldsProgress" animation="elastic" />
          </div>
          <ProseP v-if="isGoalsFieldsCreated" class="mt-2" accent="less">
            Поля для смарт-процесса "Цели" созданы
          </ProseP>
        </div>

        <div id="installer-step-7" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 7. Настройка карточки цели (общий вид для всех)</ProseH4>
          <ProseP accent="less" class="mt-2">
            Выполняется настройка отображения карточки через crm.item.details.configuration.get/set/reset и применение общего вида для всех пользователей.
          </ProseP>
          <div class="mt-3">
            <B24Button :loading="isConfiguringGoalsCard" :disabled="!canConfigureGoalsCard" color="air-primary" @click="configureGoalsCard">
              Продолжить
            </B24Button>
          </div>
          <div v-if="isConfiguringGoalsCard || goalsCardProgress > 0" class="mt-3">
            <B24Progress v-model="goalsCardProgress" animation="elastic" />
          </div>
          <ProseP v-if="isGoalsCardConfigured" class="mt-2" accent="less">
            Настройка карточки цели завершена. Режим "Общий вид карточки" применен ко всем пользователям.
          </ProseP>
        </div>

        <div id="installer-step-8" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 8. Создать и привязать базу знаний (landing.site.*)</ProseH4>
          <ProseP accent="less" class="mt-2">
            Создаем базу знаний и привязываем ее к рабочей группе.
          </ProseP>
          <div class="mt-3">
            <B24Button :loading="isCreatingKnowledgeBase" :disabled="!canCreateKnowledgeBase" color="air-primary" @click="createKnowledgeBase">
              Продолжить
            </B24Button>
          </div>
          <div v-if="isCreatingKnowledgeBase || knowledgeBaseProgress > 0" class="mt-3">
            <B24Progress v-model="knowledgeBaseProgress" animation="elastic" />
          </div>
          <ProseP v-if="knowledgeBaseId" class="mt-2" accent="less">
            База знаний создана (ID: {{ knowledgeBaseId }}), статус привязки: {{ knowledgeBaseBindingStatus }}.
            <a
              v-if="knowledgeBaseLink"
              :href="knowledgeBaseLink"
              target="_blank"
              rel="noopener noreferrer"
              class="underline"
            >
              Перейти
            </a>
          </ProseP>
        </div>

        <div id="installer-step-9" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 9. Проверить, что всё создано</ProseH4>
          <ProseP accent="less" class="mt-2">
            Проверяем наличие полей из GOALS.md, справочников, базы знаний и факт применения общего вида карточки.
          </ProseP>
          <div class="mt-3">
            <B24Button :loading="isVerifyingGoalsSetup" :disabled="!canVerifyGoalsSetup" color="air-primary" @click="verifyGoalsSetup">
              Проверить
            </B24Button>
          </div>
          <div v-if="isVerifyingGoalsSetup || verificationProgress > 0" class="mt-3">
            <B24Progress v-model="verificationProgress" animation="elastic" />
          </div>
          <ProseP v-if="goalsVerification.status !== 'pending'" class="mt-2" :accent="isGoalsVerificationPassed ? 'less' : 'warning'">
            Статус проверки: {{ isGoalsVerificationPassed ? 'успешно' : 'есть замечания' }}.
            Найдено кодов: {{ goalsVerification.foundCodesCount }}.
            <span v-if="goalsVerification.missingCodes.length > 0">
              Не найдены: {{ goalsVerification.missingCodes.join(', ') }}.
            </span>
          </ProseP>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-2">
          <B24Button color="air-secondary-accent-1" @click="refreshInstallerData">
            Обновить данные
          </B24Button>
          <ProseP v-if="setupInfo" accent="less">{{ setupInfo }}</ProseP>
          <ProseP v-if="setupError" accent="warning">{{ setupError }}</ProseP>
          <ProseP v-if="setupStateSaveError" accent="warning">{{ setupStateSaveError }}</ProseP>
        </div>

        <details class="mt-5">
          <summary class="cursor-pointer text-sm opacity-80">Технические данные</summary>

          <ProseH4 class="mt-3">Хранится в настройках приложения (RD-107)</ProseH4>
          <ProseP v-if="setupStateSource" accent="less">
            Источник: {{ setupStateSource === 'backend' ? 'БД (реальная запись)' : 'демо (не сохраняется в БД)' }}.
            Загружено: {{ setupStateLoadedAt || '—' }}
          </ProseP>
          <ProseP v-else accent="less">Состояние ещё не загружено. Выполните шаг настройки или нажмите «Обновить из БД».</ProseP>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <B24Button size="small" color="air-secondary-accent-1" @click="refreshSetupStateFromBackend">
              Обновить из БД
            </B24Button>
          </div>
          <ProsePre v-if="setupStateFromBackend" class="mt-2 text-xs">{{ setupStateFromBackend }}</ProsePre>
          <ProseP v-else class="mt-2 text-sm opacity-70">— пусто —</ProseP>

          <ProseH4 class="mt-3">Данные установки</ProseH4>
          <ProsePre class="mt-2">{{ payload }}</ProsePre>
          <ProseH4 class="mt-3">Проверка разрешений</ProseH4>
          <ProsePre class="mt-2">{{ scopeCheck }}</ProsePre>
          <ProseH4 class="mt-3">Снимок контракта</ProseH4>
          <ProsePre class="mt-2">{{ installerContract }}</ProsePre>
          <ProseH4 class="mt-3">Технический статус сценария</ProseH4>
          <ProsePre class="mt-2">{{ { workplaceId, workplaceLink, goalsTypeId, goalsLink, workgroupId, workgroupLink, isWorkgroupToolsUpdated, referenceLists, referenceFieldBindings, knowledgeBaseId, knowledgeBaseLink, knowledgeBaseBindingStatus, goalsFieldsCreated, goalsFieldCodesAdded, isGoalsCardConfigured, goalsVerification, isDemoMode, setupState } }}</ProsePre>
        </details>
      </div>
    </B24Card>
  </div>
</template>
