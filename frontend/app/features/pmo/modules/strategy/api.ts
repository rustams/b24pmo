import type { FeatureOverview } from '../../shared/types'

export const fetchStrategyOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const [goals, initiatives] = await Promise.all([
    api.authGet<FeatureOverview>('/api/pmo/goals'),
    api.authGet<FeatureOverview>('/api/pmo/initiatives')
  ])
  return [goals, initiatives]
}
