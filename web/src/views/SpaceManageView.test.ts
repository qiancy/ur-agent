import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SpaceManageView from './SpaceManageView.vue'
import { getSpaceMembers, kickMember, transferOwner } from '../api/spaceGovernance'

vi.mock('../api/spaceGovernance', () => ({
  getSpaceMembers: vi.fn(),
  kickMember: vi.fn(),
  transferOwner: vi.fn(),
  createInvite: vi.fn(),
}))

const getSpaceMembersMock = vi.mocked(getSpaceMembers)
const kickMemberMock = vi.mocked(kickMember)
const transferOwnerMock = vi.mocked(transferOwner)

const MEMBERS = {
  members: [
    { puid: 'zhangsan', name: '张三', role: 'owner', joined_at: '2026-08-01T10:00:00' },
    { puid: 'wangwu', name: '王五', role: 'member', joined_at: '2026-08-02T10:00:00' },
  ],
}

const BASE_PROPS = {
  ouid: 'co_01',
  orgType: 'company',
  role: 'owner',
  puid: 'zhangsan',
  personName: '张三',
  organizationName: '团队',
}

function mountView(overrides: Partial<typeof BASE_PROPS> = {}) {
  return mount(SpaceManageView, {
    props: { ...BASE_PROPS, ...overrides },
  })
}

describe('SpaceManageView', () => {
  beforeEach(() => {
    getSpaceMembersMock.mockReset()
    kickMemberMock.mockReset()
    transferOwnerMock.mockReset()
    getSpaceMembersMock.mockResolvedValue(MEMBERS)
    kickMemberMock.mockResolvedValue({
      ouid: 'co_01',
      puid: 'wangwu',
      status: 'removed',
    })
    transferOwnerMock.mockResolvedValue({
      ouid: 'co_01',
      new_owner_puid: 'wangwu',
      status: 'transferred',
    })
  })

  it('loads and renders the space info and members', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(getSpaceMembersMock).toHaveBeenCalled()
    expect(wrapper.find('[data-test="space-info"]').text()).toContain('团队')
    expect(wrapper.find('[data-test="space-info"]').text()).toContain('co_01')
    expect(wrapper.findAll('[data-test="member-row"]')).toHaveLength(2)
  })

  it('owner sees 邀请成员 and 创建空间 buttons', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('[data-test="invite-member"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="create-space"]').exists()).toBe(true)
  })

  it('plain member does not see management actions', async () => {
    const wrapper = mountView({ role: 'member' })
    await flushPromises()
    expect(wrapper.find('[data-test="invite-member"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-test="member-row"]')).toHaveLength(2)
  })

  it('personal space is read-only and shows the personal hint', async () => {
    const wrapper = mountView({ orgType: 'personal', role: 'owner' })
    await flushPromises()
    expect(wrapper.find('[data-test="invite-member"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="personal-hint"]').exists()).toBe(true)
  })

  it('kicks a member through the confirm dialog and reloads', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="kick-wangwu"]').trigger('click')
    expect(wrapper.find('[data-test="confirm-dialog"]').exists()).toBe(true)
    await wrapper.find('[data-test="confirm-ok"]').trigger('click')
    await flushPromises()

    expect(kickMemberMock).toHaveBeenCalledWith('co_01', 'wangwu')
    expect(getSpaceMembersMock).toHaveBeenCalledTimes(2)
  })

  it('transfers ownership through the confirm dialog and reloads', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="transfer-wangwu"]').trigger('click')
    await wrapper.find('[data-test="confirm-ok"]').trigger('click')
    await flushPromises()

    expect(transferOwnerMock).toHaveBeenCalledWith('co_01', 'wangwu')
    expect(getSpaceMembersMock).toHaveBeenCalledTimes(2)
  })

  it('emits navigate-space create from the 创建空间 button', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('[data-test="create-space"]').trigger('click')
    expect(wrapper.emitted('navigate-space')![0]).toEqual(['create'])
  })

  it('copies the ouid to the clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    })
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="copy-ouid"]').trigger('click')
    await flushPromises()

    expect(writeText).toHaveBeenCalledWith('co_01')
    expect(wrapper.find('[data-test="copy-ouid"]').text()).toBe('已复制')
  })
})
