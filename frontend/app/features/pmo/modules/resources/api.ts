import type { FeatureOverview } from '../../shared/types'

export const fetchResourcesOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const [allocations, capacity] = await Promise.all([
    api.authGet<FeatureOverview>('/api/pmo/resources/allocations'),
    api.authGet<FeatureOverview>('/api/pmo/resources/capacity')
  ])
  return [allocations, capacity]
}
