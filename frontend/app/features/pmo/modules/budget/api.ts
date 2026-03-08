import type { FeatureOverview } from '../../shared/types'

export const fetchBudgetOverview = async (): Promise<FeatureOverview[]> => {
  const api = useApiStore()
  const transactions = await api.authGet<FeatureOverview>('/api/pmo/budgets/transactions')
  return [transactions]
}
