import type { FeatureOverview } from '../../shared/types'

export const fetchSyncOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const status = await api.authGet<FeatureOverview>('/api/pmo/sync/status')
  return [status]
}

export const runInitialSync = async (): Promise<FeatureOverview> => {
  const api = useApiStore()
  return await api.authPost<FeatureOverview>('/api/pmo/sync/run-initial', {})
}
