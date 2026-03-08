import type { ModuleCard } from './types'

export const PMO_MODULE_CARDS: ModuleCard[] = [
  {
    key: 'strategy',
    title: 'Strategy',
    description: 'Goals and initiatives alignment',
    route: '/pmo/strategy'
  },
  {
    key: 'delivery',
    title: 'Delivery',
    description: 'Portfolios, programs, projects, milestones',
    route: '/pmo/delivery'
  },
  {
    key: 'resources',
    title: 'Resources',
    description: 'Allocations and capacity overview',
    route: '/pmo/resources'
  },
  {
    key: 'risks',
    title: 'Risks',
    description: 'Risk registry and AI suggestions',
    route: '/pmo/risks'
  },
  {
    key: 'budget',
    title: 'Budget',
    description: 'Transactions and plan/fact baseline',
    route: '/pmo/budget'
  },
  {
    key: 'meetings',
    title: 'Meetings',
    description: 'Decisions and action items',
    route: '/pmo/meetings'
  },
  {
    key: 'sync',
    title: 'Sync',
    description: 'Background synchronization status',
    route: '/pmo/sync'
  },
  {
    key: 'rbac',
    title: 'RBAC',
    description: 'Role model and access matrix',
    route: '/pmo/rbac'
  }
]
