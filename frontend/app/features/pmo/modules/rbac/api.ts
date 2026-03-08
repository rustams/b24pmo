import type { FeatureOverview } from '../../shared/types'

export const fetchRbacOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const roles = await api.authGet<FeatureOverview>('/api/pmo/rbac/roles')
  return [roles]
}
