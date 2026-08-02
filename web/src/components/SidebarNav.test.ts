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

describe('SidebarNav', () => {
  it('renders all five nav items and the shop brand', () => {
    const wrapper = mount(SidebarNav, {
      props: {
        currentView: 'workbench',
        organizationName: '淘宝小店 A',
        ouid: 'shop_a',
        role: 'owner',
      },
    })

    expect(wrapper.text()).toContain('Uni-Resource Agent')
    for (const item of NAV_ITEMS) {
      expect(wrapper.find(`[data-view="${item}"]`).exists()).toBe(true)
    }
  })

  it('marks the current view active', () => {
    const wrapper = mount(SidebarNav, {
      props: {
        currentView: 'stock',
        organizationName: '淘宝小店 A',
        ouid: 'shop_a',
        role: 'owner',
      },
    })

    expect(wrapper.find('[data-view="stock"]').classes()).toContain('active')
    expect(wrapper.find('[data-view="workbench"]').classes()).not.toContain(
      'active',
    )
  })

  it('emits navigate when a nav button is clicked', async () => {
    const wrapper = mount(SidebarNav, {
      props: {
        currentView: 'workbench',
        organizationName: '淘宝小店 A',
        ouid: 'shop_a',
        role: 'owner',
      },
    })

    await wrapper.find('[data-view="movements"]').trigger('click')
    expect(wrapper.emitted('navigate')).toBeTruthy()
    expect(wrapper.emitted('navigate')![0]).toEqual(['movements'])
  })

  it('shows shop identity without any DB id fields', () => {
    const wrapper = mount(SidebarNav, {
      props: {
        currentView: 'workbench',
        organizationName: '淘宝小店 A',
        ouid: 'shop_a',
        role: 'owner',
      },
    })

    const text = wrapper.text()
    expect(text).toContain('shop_a')
    expect(text).not.toMatch(/\b(id|pid|oid)\b/i)
    expect(text).not.toMatch(/[a-z]+_id/i)
  })

  it('emits logout when the logout button is clicked', async () => {
    const wrapper = mount(SidebarNav, {
      props: {
        currentView: 'workbench',
        organizationName: '淘宝小店 A',
        ouid: 'shop_a',
        role: 'owner',
      },
    })

    await wrapper.find('[data-test="logout"]').trigger('click')
    expect(wrapper.emitted('logout')).toBeTruthy()
  })
})
