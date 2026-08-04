import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LeaveSpaceView from './LeaveSpaceView.vue'
import { leaveSpace } from '../api/spaceGovernance'

vi.mock('../api/spaceGovernance', () => ({
  leaveSpace: vi.fn(),
}))

const leaveSpaceMock = vi.mocked(leaveSpace)

const BASE_PROPS = {
  ouid: 'co_01',
  orgType: 'company',
  role: 'member',
  puid: 'zhangsan',
  personName: '张三',
  organizationName: '团队',
}

function mountView(overrides: Partial<typeof BASE_PROPS> = {}) {
  return mount(LeaveSpaceView, {
    props: { ...BASE_PROPS, ...overrides },
  })
}

describe('LeaveSpaceView', () => {
  beforeEach(() => {
    leaveSpaceMock.mockReset()
    leaveSpaceMock.mockResolvedValue({ ouid: 'co_01', puid: 'zhangsan', status: 'left' })
  })

  it('renders the org name and a confirmation flow', async () => {
    const wrapper = mountView()
    expect(wrapper.find('[data-test="leave-space-view"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('团队')
    expect(wrapper.find('[data-test="confirm-dialog"]').exists()).toBe(false)
  })

  it('leaves after the confirm dialog and emits leave-confirmed', async () => {
    const wrapper = mountView()
    await wrapper.find('[data-test="leave-confirm-open"]').trigger('click')
    expect(wrapper.find('[data-test="confirm-dialog"]').exists()).toBe(true)

    await wrapper.find('[data-test="confirm-ok"]').trigger('click')
    await flushPromises()

    expect(leaveSpaceMock).toHaveBeenCalledWith('co_01')
    expect(wrapper.emitted('leave-confirmed')).toHaveLength(1)
  })

  it('shows the owner warning when the current role is owner', () => {
    const wrapper = mountView({ role: 'owner' })
    expect(wrapper.find('[data-test="owner-warn"]').exists()).toBe(true)
  })

  it('surfaces an API error on failure', async () => {
    leaveSpaceMock.mockRejectedValue(new Error('Last owner cannot leave'))
    const wrapper = mountView({ role: 'owner' })
    await wrapper.find('[data-test="leave-confirm-open"]').trigger('click')
    await wrapper.find('[data-test="confirm-ok"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test="leave-error"]').text()).toContain('Last owner')
    expect(wrapper.emitted('leave-confirmed')).toBeUndefined()
  })

  it('navigates back to manage', async () => {
    const wrapper = mountView()
    await wrapper.find('[data-test="leave-back"]').trigger('click')
    expect(wrapper.emitted('navigate-space')![0]).toEqual(['manage'])
  })
})
