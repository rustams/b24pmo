import type { FeatureOverview } from '~/features/pmo/shared/types'
import { fetchStrategyOverview } from '~/features/pmo/modules/strategy/api'
import { fetchDeliveryOverview } from '~/features/pmo/modules/delivery/api'
import { fetchResourcesOverview } from '~/features/pmo/modules/resources/api'
import { fetchRisksOverview } from '~/features/pmo/modules/risks/api'
import { fetchBudgetOverview } from '~/features/pmo/modules/budget/api'
import { fetchMeetingsOverview } from '~/features/pmo/modules/meetings/api'
import { fetchSyncOverview, runInitialSync } from '~/features/pmo/modules/sync/api'
import { fetchRbacOverview } from '~/features/pmo/modules/rbac/api'

export const usePmoStore = defineStore('pmo', () => {
  const strategy = ref<FeatureOverview[]>([])
  const delivery = ref<FeatureOverview[]>([])
  const resources = ref<FeatureOverview[]>([])
  const risks = ref<FeatureOverview[]>([])
  const budget = ref<FeatureOverview[]>([])
  const meetings = ref<FeatureOverview[]>([])
  const sync = ref<FeatureOverview[]>([])
  const rbac = ref<FeatureOverview[]>([])

  async function loadStrategy() { strategy.value = await fetchStrategyOverview() }
  async function loadDelivery() { delivery.value = await fetchDeliveryOverview() }
  async function loadResources() { resources.value = await fetchResourcesOverview() }
  async function loadRisks() { risks.value = await fetchRisksOverview() }
  async function loadBudget() { budget.value = await fetchBudgetOverview() }
  async function loadMeetings() { meetings.value = await fetchMeetingsOverview() }
  async function loadSync() { sync.value = await fetchSyncOverview() }
  async function loadRbac() { rbac.value = await fetchRbacOverview() }
  async function triggerInitialSync() { return await runInitialSync() }

  return {
    strategy,
    delivery,
    resources,
    risks,
    budget,
    meetings,
    sync,
    rbac,
    loadStrategy,
    loadDelivery,
    loadResources,
    loadRisks,
    loadBudget,
    loadMeetings,
    loadSync,
    loadRbac,
    triggerInitialSync
  }
})
