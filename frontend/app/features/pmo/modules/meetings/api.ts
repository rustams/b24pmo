import type { FeatureOverview } from '../../shared/types'

export const fetchMeetingsOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const meetings = await api.authGet<FeatureOverview>('/api/pmo/meetings')
  return [meetings]
}
