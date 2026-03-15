import type { B24Frame } from '@bitrix24/b24jssdk'
import { withoutTrailingSlash } from 'ufo'
import type { FeatureOverview } from '~/features/pmo/shared/types'

type DemoResponse = FeatureOverview | FeatureOverview[] | string[] | { status: string; backend: string; timestamp: number } | Record<string, unknown> | { token: string }

const DEMO_RESPONSES: Record<string, DemoResponse> = {
  '/api/health': { status: 'healthy', backend: 'python-demo', timestamp: Date.now() },
  '/api/enum': ['demo-option-1', 'demo-option-2', 'demo-option-3'],
  '/api/list': ['demo-item-1', 'demo-item-2', 'demo-item-3'],
  '/api/pmo/installation-context': {
    message: 'Демо-режим: используется тестовый контекст установки (фрейм Bitrix24 недоступен).',
    status: 'installed',
    domain: 'demo.bitrix24.local',
    member_id: 'demo-member',
    scope: ['crm', 'user_brief', 'pull', 'placement', 'userfieldconfig'],
    installed_at: new Date().toISOString(),
  },
  '/api/pmo/installer/contract': {
    contract_version: '2026-03-15',
    required_scopes: ['crm', 'lists', 'tasks', 'user', 'placement', 'userfieldconfig']
  },
  '/api/pmo/installer/mapping': {
    contract_version: '2026-03-15',
    mapping: {
      smart_processes: {},
      lists: {},
      meta: { version: '1.0', state: 'not_configured', updated_at_utc: new Date().toISOString() }
    }
  },
  '/api/pmo/installer/mapping/save': {
    message: 'Маппинг успешно сохранен',
    contract_version: '2026-03-15',
    mapping: {
      smart_processes: {},
      lists: {},
      meta: { version: '1.0', state: 'configured', updated_at_utc: new Date().toISOString() }
    }
  },
  '/api/pmo/installer/scope-check': {
    contract_version: '2026-03-15',
    required_scopes: ['crm', 'lists', 'tasks', 'user', 'placement', 'userfieldconfig'],
    current_scopes: ['crm', 'user', 'placement'],
    missing_scopes: ['lists', 'tasks', 'userfieldconfig'],
    scope_recommendations: [
      { scope: 'lists', hint: 'Нужен для работы со списками (риски, вехи, бюджеты и т.д.).' },
      { scope: 'tasks', hint: 'Нужен для интеграции задач и синхронизации прогресса.' },
      { scope: 'userfieldconfig', hint: 'Нужен для создания и обновления пользовательских полей.' }
    ],
    is_admin: true,
    is_ready: false,
    next_steps: ['Выдайте приложению недостающие разрешения и переустановите приложение.']
  },
  '/api/pmo/installer/setup-state': {
    contract_version: '2026-03-15',
    setup_state: {
      version: '1.0',
      current_step: 'scope_check',
      workplace: { title: 'PMO Hub', id: null, link: '', status: 'pending' },
      goals_process: { entity_type_id: null, link: '', status: 'pending' },
      workgroup: { id: null, name: '', link: '', status: 'pending', tools_updated: false },
      reference_lists: { status: 'pending', group_id: null, lists: {}, field_bindings: {} },
      knowledge_base: { status: 'pending', site_id: null, link: '', binding_status: 'pending', changes_log: [] },
      goals_fields: { status: 'pending', created_fields: [], codes_added: [] },
      goals_card_configuration: { status: 'pending', common_scope_forced: false, details: {} },
      goals_verification: { status: 'pending', missing_codes: [], found_codes_count: 0, checked_at_utc: new Date().toISOString() },
      completed_steps: [],
      updated_at_utc: new Date().toISOString()
    }
  },
  '/api/pmo/installer/setup-state/save': {
    message: 'Состояние мастера сохранено',
    contract_version: '2026-03-15',
    setup_state: {
      version: '1.0',
      current_step: 'scope_check',
      workplace: { title: 'PMO Hub', id: null, link: '', status: 'pending' },
      goals_process: { entity_type_id: null, link: '', status: 'pending' },
      workgroup: { id: null, name: '', link: '', status: 'pending', tools_updated: false },
      reference_lists: { status: 'pending', group_id: null, lists: {}, field_bindings: {} },
      knowledge_base: { status: 'pending', site_id: null, link: '', binding_status: 'pending', changes_log: [] },
      goals_fields: { status: 'pending', created_fields: [], codes_added: [] },
      goals_card_configuration: { status: 'pending', common_scope_forced: false, details: {} },
      goals_verification: { status: 'pending', missing_codes: [], found_codes_count: 0, checked_at_utc: new Date().toISOString() },
      completed_steps: [],
      updated_at_utc: new Date().toISOString()
    }
  },
  '/api/pmo/goals': { module: 'strategy.goals', status: 'demo', next: 'Подтвердить KPI и OKR на квартал' },
  '/api/pmo/initiatives': { module: 'strategy.initiatives', status: 'demo', next: 'Приоритизировать инициативы в roadmap' },
  '/api/pmo/portfolios': { module: 'delivery.portfolios', status: 'demo', next: 'Согласовать рамки портфеля Q2' },
  '/api/pmo/programs': { module: 'delivery.programs', status: 'demo', next: 'Разложить программы по владельцам' },
  '/api/pmo/projects': { module: 'delivery.projects', status: 'demo', next: 'Проверить контрольные точки по проектам' },
  '/api/pmo/milestones': { module: 'delivery.milestones', status: 'demo', next: 'Добавить baseline milestone dates' },
  '/api/pmo/resources/allocations': { module: 'resources.allocations', status: 'demo', next: 'Сверить загрузку команды на 2 недели' },
  '/api/pmo/resources/capacity': { module: 'resources.capacity', status: 'demo', next: 'Согласовать найм и capacity forecast' },
  '/api/pmo/risks': { module: 'risks.register', status: 'demo', next: 'Обновить risk matrix и mitigation plan' },
  '/api/pmo/budgets/transactions': { module: 'budget.transactions', status: 'demo', next: 'Проверить план/факт бюджета за месяц' },
  '/api/pmo/meetings': { module: 'meetings.schedule', status: 'demo', next: 'Собрать повестку weekly steering' },
  '/api/pmo/sync/status': { module: 'sync.status', status: 'demo', next: 'Проверить интеграцию и очередь синхронизации' },
  '/api/pmo/sync/run-initial': { module: 'sync.run-initial', status: 'queued', next: 'Initial demo sync started' },
  '/api/pmo/rbac/roles': { module: 'rbac.roles', status: 'demo', next: 'Проверить матрицу ролей и прав доступа' },
  '/api/getToken': { token: 'demo-jwt-token' },
}

const cloneDemoResponse = <T>(data: DemoResponse): T => JSON.parse(JSON.stringify(data)) as T

export const useApiStore = defineStore('api', () => {
  let $b24: null | B24Frame = null
  const config = useRuntimeConfig()
  const apiUrl = withoutTrailingSlash(config.public.apiUrl)

  const tokenJWT = ref('')
  const isDemoMode = ref(false)

  const isInitTokenJWT = computed(() => tokenJWT.value.length > 2)

  const $api = $fetch.create({
    baseURL: apiUrl,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  const getAuthHeaders = () => ({
    Authorization: `Bearer ${tokenJWT.value}`
  })

  const getDemoResponse = <T>(url: string): T | null => {
    const mock = DEMO_RESPONSES[url]
    if (!mock) {
      return null
    }
    isDemoMode.value = true
    return cloneDemoResponse<T>(mock)
  }

  async function authGet<T>(url: string): Promise<T> {
    if (!isInitTokenJWT.value) {
      const mock = getDemoResponse<T>(url)
      if (mock !== null) {
        return mock
      }
    }
    try {
      return await $api<T>(url, { headers: getAuthHeaders() })
    } catch (error) {
      const mock = getDemoResponse<T>(url)
      if (mock !== null) {
        return mock
      }
      throw error
    }
  }

  async function authPost<T>(url: string, body: Record<string, unknown>): Promise<T> {
    if (!isInitTokenJWT.value) {
      const mock = getDemoResponse<T>(url)
      if (mock !== null) {
        return mock
      }
    }
    try {
      return await $api<T>(url, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(body)
      })
    } catch (error) {
      const mock = getDemoResponse<T>(url)
      if (mock !== null) {
        return mock
      }
      throw error
    }
  }

  const checkHealth = async (): Promise<{ status: string; backend: string; timestamp: number }> => {
    try {
      return await authGet('/api/health')
    } catch {
      throw new Error('Backend health check failed')
    }
  }

  const getEnum = async (): Promise<string[]> => {
    return await authGet('/api/enum')
  }

  const getList = async (): Promise<string[]> => {
    return await authGet('/api/list')
  }

  const getInstallationContext = async (): Promise<Record<string, unknown>> => {
    return await authGet('/api/pmo/installation-context')
  }

  const getInstallerContract = async (): Promise<Record<string, unknown>> => {
    return await authGet('/api/pmo/installer/contract')
  }

  const getInstallerMapping = async (): Promise<Record<string, unknown>> => {
    return await authGet('/api/pmo/installer/mapping')
  }

  const saveInstallerMapping = async (mapping: Record<string, unknown>): Promise<Record<string, unknown>> => {
    return await authPost('/api/pmo/installer/mapping/save', { mapping })
  }

  const getInstallerScopeCheck = async (): Promise<Record<string, unknown>> => {
    return await authGet('/api/pmo/installer/scope-check')
  }

  const getInstallerSetupState = async (): Promise<Record<string, unknown>> => {
    return await authGet('/api/pmo/installer/setup-state')
  }

  const saveInstallerSetupState = async (setupState: Record<string, unknown>): Promise<Record<string, unknown>> => {
    return await authPost('/api/pmo/installer/setup-state/save', { setup_state: setupState })
  }

  const postInstall = async (data: Record<string, unknown>): Promise<Record<string, unknown>> => {
    return await $api('/api/install', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  const getToken = async (data: Record<string, unknown>): Promise<{ token: string }> => {
    const mock = getDemoResponse<{ token: string }>('/api/getToken')
    if (mock !== null) {
      return mock
    }

    return await $api('/api/getToken', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  const init = async (b24: B24Frame) => {
    $b24 = b24
    await reinitToken()
  }

  const reinitToken = async () => {
    if ($b24 === null) {
      console.error('B24 non init. Use api.init()')
      return
    }

    const authData = $b24.auth.getAuthData()

    if (authData === false) {
      throw new Error('Some problem with auth. See App logic')
    }

    const user = useUserStore()
    const appSettings = useAppSettingsStore()

    const response = await getToken({
      DOMAIN: withoutTrailingSlash(authData.domain).replace('https://', '').replace('http://', ''),
      PROTOCOL: authData.domain.includes('https://') ? 1 : 0,
      LANG: $b24.getLang(),
      APP_SID: $b24.getAppSid(),
      AUTH_ID: authData.access_token,
      AUTH_EXPIRES: authData.expires_in,
      REFRESH_ID: authData.refresh_token,
      REFRESH_TOKEN: authData.refresh_token,
      member_id: authData.member_id,
      user_id: user.id,
      status: appSettings.status
    })

    tokenJWT.value = response.token
  }

  return {
    isInitTokenJWT,
    isDemoMode,
    checkHealth,
    init,
    getEnum,
    getList,
    getInstallationContext,
    getInstallerContract,
    getInstallerMapping,
    saveInstallerMapping,
    getInstallerScopeCheck,
    getInstallerSetupState,
    saveInstallerSetupState,
    postInstall,
    authGet,
    authPost
  }
})
