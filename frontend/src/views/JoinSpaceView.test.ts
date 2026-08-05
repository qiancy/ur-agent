import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import JoinSpaceView from './JoinSpaceView.vue'
import {
  acceptInvite,
  createJoinRequest,
  getMyInvites,
  getMyJoinRequests,
} from '../api/spaceGovernance'
import { switchOrganization } from '../api/auth'

vi.mock('../api/spaceGovernance', () => ({
  acceptInvite: vi.fn(),
  createJoinRequest: vi.fn(),
  getMyInvites: vi.fn(),
  getMyJoinRequests: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  switchOrganization: vi.fn(),
}))

const acceptInviteMock = vi.mocked(acceptInvite)
const createJoinRequestMock = vi.mocked(createJoinRequest)
const getMyInvitesMock = vi.mocked(getMyInvites)
const getMyJoinRequestsMock = vi.mocked(getMyJoinRequests)
const switchOrganizationMock = vi.mocked(switchOrganization)

const INVITES = {
  invites: [
    {
      invite_uid: 'inv_1',
      invitee_puid: 'zhangsan',
      role: 'member',
      status: 'pending',
      created_at: '2026-08-03T10:00:00',
      created_by_puid: 'owner1',
      ouid: 'family_01',
      organization_name: '我的家庭',
      organization_type: 'family',
    },
  ],
}

const MY_REQUESTS = {
  requests: [
    {
      request_uid: 'req_1',
      requester_puid: 'zhangsan',
      message: '求加入',
      status: 'pending',
      created_at: '2026-08-03T11:00:00',
      ouid: 'co_01',
      organization_name: '团队',
      organization_type: 'company',
    },
  ],
}

const SWITCH_RESULT = {
  access_token: 'token-2',
  token_type: 'bearer',
  person: { puid: 'zhangsan', name: '张三' },
  organization: { ouid: 'family_01', name: '我的家庭', type: 'family' },
  membership: { role: 'member' },
  system_role: 'user',
  organizations: [],
  requires_organization: false,
}

const BASE_PROPS = {
  ouid: 'co_01',
  orgType: 'company',
  role: 'owner',
  puid: 'zhangsan',
  personName: '张三',
  organizationName: '团队',
}

function mountView() {
  return mount(JoinSpaceView, { props: BASE_PROPS })
}

describe('JoinSpaceView', () => {
  beforeEach(() => {
    getMyInvitesMock.mockReset()
    getMyJoinRequestsMock.mockReset()
    acceptInviteMock.mockReset()
    createJoinRequestMock.mockReset()
    switchOrganizationMock.mockReset()
    getMyInvitesMock.mockResolvedValue(INVITES)
    getMyJoinRequestsMock.mockResolvedValue(MY_REQUESTS)
    acceptInviteMock.mockResolvedValue({
      ouid: 'family_01',
      puid: 'zhangsan',
      role: 'member',
      status: 'accepted',
    })
    createJoinRequestMock.mockResolvedValue({
      request_uid: 'req_2',
      ouid: 'co_02',
      requester_puid: 'zhangsan',
      message: 'hi',
      status: 'pending',
    })
    switchOrganizationMock.mockResolvedValue(SWITCH_RESULT)
  })

  it('loads invites on mount and shows the invites tab by default', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(getMyInvitesMock).toHaveBeenCalledWith('pending')
    expect(wrapper.findAll('[data-test="invite-row"]')).toHaveLength(1)
    expect(wrapper.text()).toContain('我的家庭')
  })

  it('accepts an invite, switches organization and emits context-updated', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="accept-inv_1"]').trigger('click')
    await flushPromises()

    expect(acceptInviteMock).toHaveBeenCalledWith('inv_1')
    expect(switchOrganizationMock).toHaveBeenCalledWith('family_01')
    expect(wrapper.emitted('context-updated')![0]).toEqual([SWITCH_RESULT])
  })

  it('accepts an invite by invite_uid input and switches organization', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="accept-invite-uid"]').setValue('inv_x1')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(acceptInviteMock).toHaveBeenCalledWith('inv_x1')
    expect(switchOrganizationMock).toHaveBeenCalledWith('family_01')
    expect(wrapper.emitted('context-updated')![0]).toEqual([SWITCH_RESULT])
  })

  it('shows an empty state when there are no invites', async () => {
    getMyInvitesMock.mockResolvedValue({ invites: [] })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('[data-test="invites-empty"]').exists()).toBe(true)
  })

  it('submits a join request from the apply tab and refreshes the list', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="tab-requests"]').trigger('click')
    await wrapper.find('[data-test="apply-ouid"]').setValue('co_02')
    await wrapper.find('[data-test="apply-message"]').setValue('hi')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createJoinRequestMock).toHaveBeenCalledWith('co_02', 'hi')
    expect(getMyJoinRequestsMock).toHaveBeenCalled()
  })

  it('validates that the apply ouid is required', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('[data-test="tab-requests"]').trigger('click')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[data-test="join-error"]').text()).toContain('OUID')
    expect(createJoinRequestMock).not.toHaveBeenCalled()
  })

  it('renders my request status chips in the requests tab', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('[data-test="tab-requests"]').trigger('click')
    expect(wrapper.findAll('[data-test="my-request-row"]')).toHaveLength(1)
    expect(wrapper.text()).toContain('待审核')
  })
})
