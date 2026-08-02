import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SidebarNav from './SidebarNav.vue'

const NAV_ITEMS = [
  'workbench',
  'stock',
  'movements',
  'summary',
  'chat',
]

function mountNav(currentView = 'workbench') {
  return mount(SidebarNav, { props: { currentView } })
}

describe('SidebarNav', () => {
  it('renders all five nav items and the brand', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Uni-Resource Agent')
    for (const item of NAV_ITEMS) {
      expect(wrapper.find(`[data-view="${item}"]`).exists()).toBe(true)
    }
  })

  it('marks the current view active', () => {
    const wrapper = mountNav('stock')
    expect(wrapper.find('[data-view="stock"]').classes()).toContain('active')
    expect(wrapper.find('[data-view="workbench"]').classes()).not.toContain(
      'active',
    )
  })

  it('emits navigate when a nav button is clicked', async () => {
    const wrapper = mountNav()
    await wrapper.find('[data-view="movements"]').trigger('click')
    expect(wrapper.emitted('navigate')).toBeTruthy()
    expect(wrapper.emitted('navigate')![0]).toEqual(['movements'])
  })

  it('no longer duplicates the current shop or logout (moved to the header)', () => {
    const wrapper = mountNav()
    expect(wrapper.find('[data-test="logout"]').exists()).toBe(false)
    expect(wrapper.text()).not.toMatch(/\b(id|pid|oid)\b/i)
  })
})
