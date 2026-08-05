import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SpaceMenu from './SpaceMenu.vue'

function mountMenu(role = 'owner', orgType = 'ecommerce') {
  return mount(SpaceMenu, { props: { role, orgType } })
}

async function openMenu(wrapper: ReturnType<typeof mountMenu>) {
  await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
  expect(wrapper.find('[data-test="space-menu-panel"]').exists()).toBe(true)
}

describe('SpaceMenu', () => {
  it('shows manage, create, join and leave for owner; review for owner/admin', async () => {
    const owner = mountMenu('owner', 'company')
    await openMenu(owner)
    expect(owner.find('[data-test="space-menu-item-manage"]').exists()).toBe(true)
    expect(owner.find('[data-test="space-menu-item-create"]').exists()).toBe(true)
    expect(owner.find('[data-test="space-menu-item-join"]').exists()).toBe(true)
    expect(owner.find('[data-test="space-menu-item-review"]').exists()).toBe(true)
    expect(owner.find('[data-test="space-menu-item-leave"]').exists()).toBe(true)

    const admin = mountMenu('admin', 'company')
    await openMenu(admin)
    expect(admin.find('[data-test="space-menu-item-review"]').exists()).toBe(true)
    expect(admin.find('[data-test="space-menu-item-leave"]').exists()).toBe(true)
  })

  it('hides 审核申请 for regular members but keeps join and leave', async () => {
    const wrapper = mountMenu('member', 'company')
    await openMenu(wrapper)
    expect(wrapper.find('[data-test="space-menu-item-manage"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-create"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-join"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-leave"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-review"]').exists()).toBe(false)
  })

  it('hides 退出空间 inside a personal space', async () => {
    const wrapper = mountMenu('owner', 'personal')
    await openMenu(wrapper)
    expect(wrapper.find('[data-test="space-menu-item-manage"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-review"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-leave"]').exists()).toBe(false)
  })

  it('is closed by default and toggles on click', async () => {
    const wrapper = mountMenu('member')
    expect(wrapper.find('[data-test="space-menu-panel"]').exists()).toBe(false)
    await openMenu(wrapper)
    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    expect(wrapper.find('[data-test="space-menu-panel"]').exists()).toBe(false)
  })

  it('emits select with the action and closes the panel', async () => {
    const wrapper = mountMenu('member')
    await openMenu(wrapper)
    await wrapper.find('[data-test="space-menu-item-join"]').trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual(['join'])
    expect(wrapper.find('[data-test="space-menu-panel"]').exists()).toBe(false)
  })
})
