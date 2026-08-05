import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SidebarNav from './SidebarNav.vue'
import type { WorkspaceNavItem } from '../workspace/types'

const ECOMMERCE_NAV: WorkspaceNavItem[] = [
  { key: 'workbench', label: '工作台', icon: '', kind: 'view', group: 'observe', component: () => {} },
  { key: 'products', label: '商品', icon: '', kind: 'view', group: 'operate', component: () => {} },
  { key: 'stock', label: '库存', icon: '', kind: 'view', group: 'operate', component: () => {} },
  { key: 'movements', label: '库存流水', icon: '', kind: 'view', group: 'operate', component: () => {} },
  { key: 'summary', label: '经营摘要', icon: '', kind: 'view', group: 'operate', component: () => {} },
  { key: 'seller-ai', label: 'Seller AI', icon: '', kind: 'view', group: 'ai', component: () => {} },
]

const SPACE_NAV: WorkspaceNavItem[] = [
  { key: 'overview', label: '空间总览', icon: '', kind: 'view', group: 'observe', component: () => {} },
  { key: 'resources', label: '资源', icon: '', kind: 'view', group: 'observe', component: () => {} },
  { key: 'persons', label: '人员', icon: '', kind: 'view', group: 'observe', component: () => {} },
  { key: 'timeline', label: '时间线', icon: '', kind: 'view', group: 'observe', component: () => {} },
  { key: 'flows', label: '多维观察', icon: '', kind: 'view', group: 'observe', component: () => {} },
]

function mountNav(currentView = 'workbench', items: WorkspaceNavItem[] = ECOMMERCE_NAV) {
  return mount(SidebarNav, { props: { currentView, navItems: items } })
}

describe('SidebarNav', () => {
  it('renders the ecommerce nav items with their labels', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Uni-Resource Agent')
    for (const item of ECOMMERCE_NAV) {
      const el = wrapper.find(`[data-view="${item.key}"]`)
      expect(el.exists()).toBe(true)
      expect(el.text()).toContain(item.label)
    }
    // ecommerce must not expose non-ecommerce space keys
    expect(wrapper.find('[data-view="overview"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="flows"]').exists()).toBe(false)
  })

  it('renders the non-ecommerce nav items when given space nav', () => {
    const wrapper = mountNav('overview', SPACE_NAV)
    for (const item of SPACE_NAV) {
      const el = wrapper.find(`[data-view="${item.key}"]`)
      expect(el.exists()).toBe(true)
      expect(el.text()).toContain(item.label)
    }
    // space nav must not expose seller keys
    expect(wrapper.find('[data-view="workbench"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="products"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="chat"]').exists()).toBe(false)
  })

  it('marks the current view active', () => {
    const wrapper = mountNav('stock', ECOMMERCE_NAV)
    expect(wrapper.find('[data-view="stock"]').classes()).toContain('active')
    expect(wrapper.find('[data-view="workbench"]').classes()).not.toContain(
      'active',
    )
  })

  it('emits navigate when a nav button is clicked', async () => {
    const wrapper = mountNav('overview', SPACE_NAV)
    await wrapper.find('[data-view="persons"]').trigger('click')
    expect(wrapper.emitted('navigate')).toBeTruthy()
    expect(wrapper.emitted('navigate')![0]).toEqual(['persons'])
  })

  it('renders nav items grouped by group', () => {
    const wrapper = mountNav('workbench', ECOMMERCE_NAV)
    const groupLabels = wrapper.findAll('.nav-group-label')
    expect(groupLabels.length).toBeGreaterThanOrEqual(3)
    expect(groupLabels.at(0)?.text()).toBe('观察')
    expect(groupLabels.at(1)?.text()).toBe('经营')
    expect(groupLabels.at(2)?.text()).toBe('AI')
  })

  it('no longer duplicates the current shop or logout (moved to the header)', () => {
    const wrapper = mountNav()
    expect(wrapper.find('[data-test="logout"]').exists()).toBe(false)
    expect(wrapper.text()).not.toMatch(/\b(id|pid|oid)\b/i)
  })
})
