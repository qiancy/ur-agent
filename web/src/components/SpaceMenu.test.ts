import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SpaceMenu from './SpaceMenu.vue'

function mountMenu(role = 'owner') {
  return mount(SpaceMenu, { props: { role } })
}

async function openMenu(wrapper: ReturnType<typeof mountMenu>) {
  await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
  expect(wrapper.find('[data-test="space-menu-panel"]').exists()).toBe(true)
}

describe('SpaceMenu', () => {
  it('shows 管理空间 and 审核申请 for owner/admin roles', async () => {
    const owner = mountMenu('owner')
    await openMenu(owner)
    expect(owner.find('[data-test="space-menu-item-manage"]').exists()).toBe(true)
    expect(owner.find('[data-test="space-menu-item-review"]').exists()).toBe(true)
    expect(owner.find('[data-test="space-menu-item-join"]').exists()).toBe(false)
    expect(owner.find('[data-test="space-menu-item-leave"]').exists()).toBe(false)

    const admin = mountMenu('admin')
    await openMenu(admin)
    expect(admin.find('[data-test="space-menu-item-review"]').exists()).toBe(true)
  })

  it('shows 管理空间, 加入空间 and 退出空间 for regular members', async () => {
    const wrapper = mountMenu('member')
    await openMenu(wrapper)
    expect(wrapper.find('[data-test="space-menu-item-manage"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-join"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-leave"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="space-menu-item-review"]').exists()).toBe(false)
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
