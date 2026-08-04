import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ReviewRequestsView from './ReviewRequestsView.vue'
import {
  approveJoinRequest,
  getSpaceJoinRequests,
  rejectJoinRequest,
} from '../api/spaceGovernance'

vi.mock('../api/spaceGovernance', () => ({
  approveJoinRequest: vi.fn(),
  rejectJoinRequest: vi.fn(),
  getSpaceJoinRequests: vi.fn(),
}))

const approveJoinRequestMock = vi.mocked(approveJoinRequest)
const rejectJoinRequestMock = vi.mocked(rejectJoinRequest)
const getSpaceJoinRequestsMock = vi.mocked(getSpaceJoinRequests)

const REQUESTS = {
  requests: [
    {
      request_uid: 'req_1',
      requester_puid: 'wangwu',
      requester_name: '王五',
      message: '申请加入',
      status: 'pending',
      created_at: '2026-08-03T10:00:00',
    },
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

function mountView() {
  return mount(ReviewRequestsView, { props: BASE_PROPS })
}

describe('ReviewRequestsView', () => {
  beforeEach(() => {
    getSpaceJoinRequestsMock.mockReset()
    approveJoinRequestMock.mockReset()
    rejectJoinRequestMock.mockReset()
    getSpaceJoinRequestsMock.mockResolvedValue(REQUESTS)
    approveJoinRequestMock.mockResolvedValue({
      request_uid: 'req_1',
      ouid: 'co_01',
      puid: 'wangwu',
      role: 'member',
      status: 'approved',
    })
    rejectJoinRequestMock.mockResolvedValue({
      request_uid: 'req_1',
      ouid: 'co_01',
      requester_puid: 'wangwu',
      status: 'rejected',
    })
  })

  it('loads pending requests on mount', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(getSpaceJoinRequestsMock).toHaveBeenCalledWith('pending')
    expect(wrapper.findAll('[data-test="join-request-row"]')).toHaveLength(1)
    expect(wrapper.text()).toContain('王五')
    expect(wrapper.text()).toContain('申请加入')
  })

  it('approves a request and reloads the list', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="approve-req_1"]').trigger('click')
    await flushPromises()

    expect(approveJoinRequestMock).toHaveBeenCalledWith('req_1')
    expect(getSpaceJoinRequestsMock).toHaveBeenCalledTimes(2)
  })

  it('rejects a request and reloads the list', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('[data-test="reject-req_1"]').trigger('click')
    await flushPromises()

    expect(rejectJoinRequestMock).toHaveBeenCalledWith('req_1')
    expect(getSpaceJoinRequestsMock).toHaveBeenCalledTimes(2)
  })

  it('shows an empty state when there are no pending requests', async () => {
    getSpaceJoinRequestsMock.mockResolvedValue({ requests: [] })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('[data-test="join-requests-empty"]').exists()).toBe(true)
  })

  it('member/viewer sees a no-permission page and does not load requests', async () => {
    const wrapper = mount(ReviewRequestsView, {
      props: { ...BASE_PROPS, role: 'member' },
    })
    await flushPromises()
    expect(wrapper.find('[data-test="review-no-perm"]').exists()).toBe(true)
    expect(getSpaceJoinRequestsMock).not.toHaveBeenCalled()
  })
})
