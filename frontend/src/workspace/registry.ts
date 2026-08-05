import type { Component } from 'vue'
import type {
  WorkspaceCapability,
  WorkspaceDefinition,
  WorkspaceNavGroup,
  WorkspaceNavItem,
  GenericSection,
} from './types'

// View components
import WorkbenchView from '../views/WorkbenchView.vue'
import ProductsView from '../views/ProductsView.vue'
import StockView from '../views/StockView.vue'
import MovementsView from '../views/MovementsView.vue'
import SummaryView from '../views/SummaryView.vue'
import ChatView from '../views/ChatView.vue'
import GenericSpaceView from '../views/GenericSpaceView.vue'
import SpaceManageView from '../views/SpaceManageView.vue'
import SpaceCreateView from '../views/SpaceCreateView.vue'
import JoinSpaceView from '../views/JoinSpaceView.vue'
import ReviewRequestsView from '../views/ReviewRequestsView.vue'
import LeaveSpaceView from '../views/LeaveSpaceView.vue'

type ComponentMap = Record<string, Component>

const viewComponents: ComponentMap = {
  'workbench': WorkbenchView,
  'products': ProductsView,
  'stock': StockView,
  'movements': MovementsView,
  'summary': SummaryView,
  'seller-ai': ChatView,
  'overview': GenericSpaceView,
  'resources': GenericSpaceView,
  'persons': GenericSpaceView,
  'timeline': GenericSpaceView,
  'flows': GenericSpaceView,
  'space-manage': SpaceManageView,
  'space-create': SpaceCreateView,
  'space-join': JoinSpaceView,
  'space-review': ReviewRequestsView,
  'space-leave': LeaveSpaceView,
}

const SECTION_MAP: Record<string, GenericSection> = {
  'overview': 'overview',
  'resources': 'resources',
  'persons': 'persons',
  'timeline': 'timeline',
  'flows': 'flows',
}

const GROUP_LABELS: Record<string, string> = {
  observe: '观察',
  operate: '经营',
  ai: 'AI',
  governance: '空间治理',
}

export type { WorkspaceCapability, WorkspaceDefinition, WorkspaceNavGroup, WorkspaceNavItem, GenericSection, WorkspaceNavKind, WorkspaceViewComponent } from './types'

export { GROUP_LABELS }

function makeNavItem(
  key: WorkspaceCapability,
  label: string,
  icon: string,
  group: WorkspaceNavGroup,
  options: Partial<Pick<WorkspaceNavItem, 'kind' | 'requiresRole'>> = {},
): WorkspaceNavItem {
  const kind = options.kind ?? 'view'
  const section = kind === 'view' ? SECTION_MAP[key] : undefined
  const component = kind === 'view' ? viewComponents[key] : undefined
  return {
    key,
    label,
    icon,
    kind,
    group,
    requiresRole: options.requiresRole,
    component,
    section,
  }
}

const BASE_ITEMS: WorkspaceNavItem[] = [
  makeNavItem('overview', '空间总览', 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z', 'observe'),
  makeNavItem('resources', '资源', 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4', 'observe'),
  makeNavItem('persons', '人员', 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z', 'observe'),
  makeNavItem('timeline', '时间线', 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', 'observe'),
  makeNavItem('flows', '多维观察', 'M13 10V3L4 14h7v7l9-11h-7z', 'observe'),
  makeNavItem('space-manage', '管理空间', 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z', 'governance', { requiresRole: ['owner', 'admin'] }),
  makeNavItem('space-create', '创建空间', 'M12 4v16m8-8H4', 'governance'),
  makeNavItem('space-join', '加入空间', 'M18 9v3m0 0v3m0-3h3m-3 0h-3', 'governance'),
  makeNavItem('space-review', '审核申请', 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', 'governance', { requiresRole: ['owner', 'admin'] }),
  makeNavItem('space-leave', '退出空间', 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1', 'governance'),
]

const ECOMMERCE_EXTRA: WorkspaceNavItem[] = [
  makeNavItem('workbench', '工作台', 'M4 5a2 2 0 012-2h12a2 2 0 012 2v3H4V5zm0 5h7v9H6a2 2 0 01-2-2v-7zm9 0h7v7a2 2 0 01-2 2h-5v-9z', 'observe'),
  makeNavItem('products', '商品', 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4', 'operate'),
  makeNavItem('stock', '库存', 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10', 'operate'),
  makeNavItem('movements', '库存流水', 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', 'operate'),
  makeNavItem('summary', '经营摘要', 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', 'operate'),
  makeNavItem('seller-ai', 'Seller AI', 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-4.272C3.512 14.461 3 13.762 3 13c0-4.418 4.03-8 9-8s9 3.582 9 8z', 'ai'),
]

export function getWorkspaceDefinition(orgType: string): WorkspaceDefinition {
  const baseCapabilities: WorkspaceCapability[] = [
    'overview', 'resources', 'persons', 'timeline', 'flows',
    'space-manage', 'space-create', 'space-join', 'space-review', 'space-leave',
  ]

  if (orgType === 'personal') {
    const capabilities: WorkspaceCapability[] = [
      'overview', 'resources', 'persons', 'timeline', 'flows', 'space-create', 'space-join',
    ]
    return {
      orgType: 'personal',
      defaultView: 'overview',
      capabilities,
      navItems: BASE_ITEMS.filter((item) => capabilities.includes(item.key)),
    }
  }

  if (orgType === 'ecommerce') {
    const ecommerceCapabilities: WorkspaceCapability[] = [
      ...baseCapabilities,
      'workbench', 'products', 'stock', 'movements', 'summary', 'seller-ai',
    ]
    return {
      orgType: 'ecommerce',
      defaultView: 'workbench',
      capabilities: ecommerceCapabilities,
      navItems: [
        ECOMMERCE_EXTRA[0],
        ...BASE_ITEMS,
        ...ECOMMERCE_EXTRA.slice(1),
      ],
    }
  }

  // Default: campaign, family, starship, company, etc.
  return {
    orgType,
    defaultView: 'overview',
    capabilities: baseCapabilities,
    navItems: BASE_ITEMS,
  }
}

export function filterNavItems(
  items: WorkspaceNavItem[],
  role: string,
): WorkspaceNavItem[] {
  return items.filter((item) => {
    if (!item.requiresRole) return true
    return item.requiresRole.includes(role as 'owner' | 'admin' | 'member' | 'viewer')
  })
}

export function clampToAllowedView(
  requested: string | undefined,
  definition: WorkspaceDefinition,
  role: string,
): WorkspaceCapability {
  const allowed = filterNavItems(definition.navItems, role)
  const allowedKeys = new Set(allowed.map((item) => item.key))
  if (!requested || !allowedKeys.has(requested as WorkspaceCapability)) {
    return definition.defaultView
  }
  return requested as WorkspaceCapability
}
