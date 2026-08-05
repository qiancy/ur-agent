import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SidebarNav from './SidebarNav.vue'

const ECOMMERCE_NAV = [
  ['workbench', '工作台'],
  ['products', '商品'],
  ['stock', '库存'],
  ['movements', '库存流水'],
  ['summary', '经营摘要'],
  ['chat', 'Seller AI'],
]

const SPACE_NAV = [
  ['overview', '空间总览'],
  ['resources', '资源'],
  ['persons', '人员'],
  ['timeline', '时间线'],
  ['flows', '多维观察'],
]

function mountNav(currentView = 'workbench', orgType = 'ecommerce') {
  return mount(SidebarNav, { props: { currentView, orgType } })
}

describe('SidebarNav', () => {
  it('renders the ecommerce nav items with their labels', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Uni-Resource Agent')
    for (const [key, label] of ECOMMERCE_NAV) {
      const item = wrapper.find(`[data-view="${key}"]`)
      expect(item.exists()).toBe(true)
      expect(item.text()).toContain(label)
    }
    // ecommerce must not expose non-ecommerce space keys
    expect(wrapper.find('[data-view="overview"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="flows"]').exists()).toBe(false)
  })

  it('renders the non-ecommerce nav items when orgType is not ecommerce', () => {
    const wrapper = mountNav('overview', 'family')
    for (const [key, label] of SPACE_NAV) {
      const item = wrapper.find(`[data-view="${key}"]`)
      expect(item.exists()).toBe(true)
      expect(item.text()).toContain(label)
    }
    // space nav must not expose seller keys
    expect(wrapper.find('[data-view="workbench"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="products"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="chat"]').exists()).toBe(false)
  })

  it('marks the current view active', () => {
    const wrapper = mountNav('stock', 'ecommerce')
    expect(wrapper.find('[data-view="stock"]').classes()).toContain('active')
    expect(wrapper.find('[data-view="workbench"]').classes()).not.toContain(
      'active',
    )
  })

  it('emits navigate when a nav button is clicked', async () => {
    const wrapper = mountNav('overview', 'family')
    await wrapper.find('[data-view="persons"]').trigger('click')
    expect(wrapper.emitted('navigate')).toBeTruthy()
    expect(wrapper.emitted('navigate')![0]).toEqual(['persons'])
  })

  it('no longer duplicates the current shop or logout (moved to the header)', () => {
    const wrapper = mountNav()
    expect(wrapper.find('[data-test="logout"]').exists()).toBe(false)
    expect(wrapper.text()).not.toMatch(/\b(id|pid|oid)\b/i)
  })
})
