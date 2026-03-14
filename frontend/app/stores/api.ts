import type { B24Frame } from '@bitrix24/b24jssdk'
import { withoutTrailingSlash } from 'ufo'
import type { FeatureOverview } from '~/features/pmo/shared/types'

type DemoResponse = FeatureOverview | FeatureOverview[] | string[] | { status: string; backend: string; timestamp: number } | Record<string, unknown> | { token: string }

const DEMO_RESPONSES: Record<string, DemoResponse> = {
  '/api/health': { status: 'healthy', backend: 'python-demo', timestamp: Date.now() },
  '/api/enum': ['demo-option-1', 'demo-option-2', 'demo-option-3'],
  '/api/list': ['demo-item-1', 'demo-item-2', 'demo-item-3'],
  '/api/pmo/installation-context': {
    message: 'Demo mode: mocked installation context (B24 frame unavailable).',
    status: 'installed',
    domain: 'demo.bitrix24.local',
    member_id: 'demo-member',
    scope: ['crm', 'user_brief', 'pull', 'placement', 'userfieldconfig'],
    installed_at: new Date().toISOString(),
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

    return await $api<T>(url, { headers: getAuthHeaders() })
  }

  async function authPost<T>(url: string, body: Record<string, unknown>): Promise<T> {
    if (!isInitTokenJWT.value) {
      const mock = getDemoResponse<T>(url)
      if (mock !== null) {
        return mock
      }
    }

    return await $api<T>(url, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    })
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
    postInstall,
    authGet,
    authPost
  }
})
