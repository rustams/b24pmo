import type { FeatureOverview } from '../../shared/types'

export const fetchRisksOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const risks = await api.authGet<FeatureOverview>('/api/pmo/risks')
  return [risks]
}
