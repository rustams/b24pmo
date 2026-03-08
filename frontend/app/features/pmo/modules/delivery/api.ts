import type { FeatureOverview } from '../../shared/types'

export const fetchDeliveryOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const [portfolios, programs, projects, milestones] = await Promise.all([
    api.authGet<FeatureOverview>('/api/pmo/portfolios'),
    api.authGet<FeatureOverview>('/api/pmo/programs'),
    api.authGet<FeatureOverview>('/api/pmo/projects'),
    api.authGet<FeatureOverview>('/api/pmo/milestones')
  ])
  return [portfolios, programs, projects, milestones]
}
