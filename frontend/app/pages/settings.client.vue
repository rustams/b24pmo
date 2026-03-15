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
const goalsFieldsCreated = ref<Array<{ title: string; code: string; field_id: number | null; status: string }>>([])
const goalsFieldCodesAdded = ref<string[]>([])
const isGoalsCardConfigured = ref(false)
const goalsVerification = ref<{ status: string; missingCodes: string[]; foundCodesCount: number }>({ status: 'pending', missingCodes: [], foundCodesCount: 0 })
const setupState = ref<Record<string, unknown> | null>(null)
const setupStateSaveError = ref('')

const workplaceProgress = ref(0)
const goalsProgress = ref(0)
const goalsFieldsProgress = ref(0)
const goalsCardProgress = ref(0)
const verificationProgress = ref(0)
const isCreatingWorkplace = ref(false)
const isCreatingGoals = ref(false)
const isCreatingGoalsFields = ref(false)
const isConfiguringGoalsCard = ref(false)
const isVerifyingGoalsSetup = ref(false)

const canCreateWorkplace = computed(() => workplaceTitle.value.trim().length > 1 && !isCreatingWorkplace.value)
const canCreateGoals = computed(() => workplaceId.value !== null && !isCreatingGoals.value)
const canCreateGoalsFields = computed(() => goalsTypeId.value !== null && !isCreatingGoalsFields.value)
const canConfigureGoalsCard = computed(() => goalsTypeId.value !== null && goalsFieldsCreated.value.length > 0 && !isConfiguringGoalsCard.value)
const canVerifyGoalsSetup = computed(() => goalsTypeId.value !== null && !isVerifyingGoalsSetup.value)
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

type GoalsFieldDefinition = {
  title: string
  codeTemplate: string
  userTypeId: string
  sort: number
  mandatory: boolean
  multiple: boolean
}

const GOALS_FIELD_DEFINITIONS: GoalsFieldDefinition[] = [
  { title: 'Название цели', codeTemplate: 'UF_CRM_XXX_GOAL_TITLE', userTypeId: 'string', sort: 10, mandatory: true, multiple: false },
  { title: 'Описание цели', codeTemplate: 'UF_CRM_XXX_GOAL_DESCRIPTION', userTypeId: 'string', sort: 20, mandatory: false, multiple: false },
  { title: 'Тип цели', codeTemplate: 'UF_CRM_XXX_GOAL_TYPE', userTypeId: 'string', sort: 30, mandatory: true, multiple: false },
  { title: 'Приоритет', codeTemplate: 'UF_CRM_XXX_GOAL_PRIORITY', userTypeId: 'string', sort: 40, mandatory: false, multiple: false },
  { title: 'Статус цели', codeTemplate: 'UF_CRM_XXX_GOAL_STATUS', userTypeId: 'string', sort: 50, mandatory: true, multiple: false },
  { title: 'Ключевой показатель (KPI)', codeTemplate: 'UF_CRM_XXX_GOAL_KPI', userTypeId: 'string', sort: 60, mandatory: false, multiple: true },
  { title: 'Единица измерения', codeTemplate: 'UF_CRM_XXX_GOAL_KPI_UNIT', userTypeId: 'string', sort: 70, mandatory: true, multiple: false },
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

const buildGoalFieldPayload = (field: GoalsFieldDefinition) => ({
  title: field.title,
  fieldName: extractGoalCode(field.codeTemplate),
  type: field.userTypeId,
  sort: field.sort,
  isRequired: field.mandatory ? 'Y' : 'N',
  isMultiple: field.multiple ? 'Y' : 'N',
  formLabel: field.title,
  listLabel: field.title,
  filterLabel: field.title
})

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
      const workplace = (persistedState.workplace as Record<string, unknown> | undefined) ?? {}
      const goalsProcess = (persistedState.goals_process as Record<string, unknown> | undefined) ?? {}
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

const persistSetupState = async (partialState: Record<string, unknown>) => {
  setupStateSaveError.value = ''
  const current = (setupState.value ?? {}) as Record<string, unknown>
  const currentWorkplace = (current.workplace as Record<string, unknown> | undefined) ?? {}
  const currentGoals = (current.goals_process as Record<string, unknown> | undefined) ?? {}
  const currentGoalsFields = (current.goals_fields as Record<string, unknown> | undefined) ?? {}
  const currentGoalsCard = (current.goals_card_configuration as Record<string, unknown> | undefined) ?? {}
  const partialWorkplace = (partialState.workplace as Record<string, unknown> | undefined) ?? {}
  const partialGoals = (partialState.goals_process as Record<string, unknown> | undefined) ?? {}
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
    setupState.value = (response.setup_state as Record<string, unknown> | undefined) ?? mergedState
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

const createGoalsFields = async () => {
  if (!goalsTypeId.value) {
    setupError.value = 'Сначала создайте смарт-процесс "Цели".'
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
        const fieldPayload = buildGoalFieldPayload(definition)
        const data = await callMethodWithFallback('crm.item.userfield.add', [
          { entityTypeId: goalsTypeId.value, field: fieldPayload },
          { entityTypeId: goalsTypeId.value, fields: fieldPayload },
          { entityTypeId: goalsTypeId.value, FIELD: fieldPayload },
          {
            entityTypeId: goalsTypeId.value,
            fields: {
              FIELD_NAME: fieldPayload.fieldName,
              USER_TYPE_ID: definition.userTypeId,
              EDIT_FORM_LABEL: fieldPayload.formLabel,
              LIST_COLUMN_LABEL: fieldPayload.listLabel,
              LIST_FILTER_LABEL: fieldPayload.filterLabel,
              MANDATORY: definition.mandatory ? 'Y' : 'N',
              MULTIPLE: definition.multiple ? 'Y' : 'N',
              SORT: definition.sort
            }
          }
        ])

        const fieldId = Number(data.id || data.fieldId || data.field_id || 0) || null
        createdFields.push({
          title: definition.title,
          code: String(fieldPayload.fieldName),
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
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'goals_fields_created']
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
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'goals_fields_created', 'goals_card_configured']
    })
    await scrollToStep(6)
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

const toRecordArray = (value: unknown): Array<Record<string, unknown>> => {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter(item => item && typeof item === 'object').map(item => item as Record<string, unknown>)
}

const extractFieldCode = (item: Record<string, unknown>): string => {
  const raw = item.fieldName || item.FIELD_NAME || item.name || item.code || ''
  return String(raw).trim().toUpperCase()
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
      const listData = await callMethodWithFallback('crm.item.userfield.list', [
        { entityTypeId: goalsTypeId.value },
        { entityTypeId: goalsTypeId.value, order: { sort: 'ASC' } },
        { entityTypeId: goalsTypeId.value, filter: {} }
      ])

      const records = [
        ...toRecordArray(listData.items),
        ...toRecordArray(listData.userFields),
        ...toRecordArray(listData.fields),
        ...toRecordArray(listData.result)
      ]
      actualCodes = records.map(extractFieldCode).filter(code => code.length > 0)
      verificationProgress.value = 80
    }

    const actualCodeSet = new Set(actualCodes)
    const missingCodes = expectedCodes.filter(code => !actualCodeSet.has(code))
    const status = missingCodes.length === 0 && isGoalsCardConfigured.value ? 'passed' : 'failed'
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
      completed_steps: ['scope_check', 'workplace_created', 'goals_created', 'goals_fields_created', 'goals_card_configured', 'goals_verification_done']
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
          <ProseH4 class="!m-0">Шаг 4. Создать поля смарт-процесса "Цели"</ProseH4>
          <ProseP accent="less" class="mt-2">
            После создания смарт-процесса будут автоматически созданы поля по документу GOALS.md.
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

        <div id="installer-step-5" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 5. Настройка карточки цели (общий вид для всех)</ProseH4>
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

        <div id="installer-step-6" class="mt-5 rounded border border-(--ui-color-accent-soft-blue-2) p-3">
          <ProseH4 class="!m-0">Шаг 6. Проверить, что всё создано</ProseH4>
          <ProseP accent="less" class="mt-2">
            Проверяем наличие полей из GOALS.md и факт применения общего вида карточки.
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
          <ProseH4 class="mt-3">Данные установки</ProseH4>
          <ProsePre class="mt-2">{{ payload }}</ProsePre>
          <ProseH4 class="mt-3">Проверка разрешений</ProseH4>
          <ProsePre class="mt-2">{{ scopeCheck }}</ProsePre>
          <ProseH4 class="mt-3">Снимок контракта</ProseH4>
          <ProsePre class="mt-2">{{ installerContract }}</ProsePre>
          <ProseH4 class="mt-3">Технический статус сценария</ProseH4>
          <ProsePre class="mt-2">{{ { workplaceId, workplaceLink, goalsTypeId, goalsLink, goalsFieldsCreated, goalsFieldCodesAdded, isGoalsCardConfigured, goalsVerification, isDemoMode, setupState } }}</ProsePre>
        </details>
      </div>
    </B24Card>
  </div>
</template>
