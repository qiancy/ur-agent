import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import AppHeader from './AppHeader.vue'
import type { UserOrganization } from '../api/auth'

const ORGS: UserOrganization[] = [
  { ouid: 'taobao_shop_a', name: '淘宝小店 A', type: 'ecommerce', role: 'owner' },
  { ouid: 'family', name: '我的家庭', type: 'family', role: 'member' },
]

function mountHeader(overrides: Partial<Record<string, unknown>> = {}) {
  return mount(AppHeader, {
    props: {
      personName: '张三',
      puid: 'zhangsan',
      organizationName: '淘宝小店 A',
      ouid: 'taobao_shop_a',
      orgType: 'ecommerce',
      role: 'owner',
      organizations: ORGS,
      ...overrides,
    },
  })
}

describe('AppHeader', () => {
  it('renders the current user, organization, business type and role', () => {
    const wrapper = mountHeader()
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('zhangsan')
    expect(wrapper.text()).toContain('淘宝小店 A')
    expect(wrapper.text()).toContain('ecommerce')
    expect(wrapper.text()).toContain('owner')
  })

  it('lists organizations in the switch dropdown and selects the current ouid', () => {
    const wrapper = mountHeader()
    const select = wrapper.find('select[data-test="org-switch"]')
    expect(select.exists()).toBe(true)
    const options = select.findAll('option')
    expect(options).toHaveLength(2)
    expect((select.element as HTMLSelectElement).value).toBe('taobao_shop_a')
  })

  it('emits switch-organization with the target ouid when another org is chosen', async () => {
    const wrapper = mountHeader()
    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    expect(wrapper.emitted('switch-organization')).toBeTruthy()
    expect(wrapper.emitted('switch-organization')![0]).toEqual(['family'])
  })

  it('emits logout when the logout button is clicked', async () => {
    const wrapper = mountHeader()
    await wrapper.find('button[data-test="header-logout"]').trigger('click')
    expect(wrapper.emitted('logout')).toHaveLength(1)
  })

  it('renders an AI entry that only emits navigate-ai (never sends a request)', async () => {
    const wrapper = mountHeader()
    const entry = wrapper.find('button[data-test="header-ai-entry"]')
    expect(entry.exists()).toBe(true)
    await entry.trigger('click')
    expect(wrapper.emitted('navigate-ai')).toHaveLength(1)
  })

  it('removed the header AI input and 问 AI button', () => {
    const wrapper = mountHeader()
    expect(wrapper.find('input[data-test="header-ai"]').exists()).toBe(false)
    expect(wrapper.find('button[data-test="header-ai-send"]').exists()).toBe(false)
  })

  it('exposes the space menu and re-emits its action as navigate-space-menu', async () => {
    const wrapper = mountHeader({ role: 'member' })
    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    await wrapper.find('[data-test="space-menu-item-join"]').trigger('click')
    expect(wrapper.emitted('navigate-space-menu')).toBeTruthy()
    expect(wrapper.emitted('navigate-space-menu')![0]).toEqual(['join'])
  })
})
