import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import JoinRequestTable from './JoinRequestTable.vue'
import type { SpaceJoinRequest } from '../api/spaceGovernance'

const REQ: SpaceJoinRequest = {
  request_uid: 'req_0001',
  requester_puid: 'wangwu',
  requester_name: '王五',
  message: '申请加入',
  status: 'pending',
  created_at: '2026-08-03T10:00:00',
}

function mountTable(requests: SpaceJoinRequest[], canApprove = true) {
  return mount(JoinRequestTable, { props: { requests, canApprove } })
}

describe('JoinRequestTable', () => {
  it('renders request rows with requester and message', () => {
    const wrapper = mountTable([REQ])
    const rows = wrapper.findAll('[data-test="join-request-row"]')
    expect(rows).toHaveLength(1)
    expect(wrapper.text()).toContain('王五')
    expect(wrapper.text()).toContain('wangwu')
    expect(wrapper.text()).toContain('申请加入')
  })

  it('shows approve/reject buttons when canApprove and emits on click', async () => {
    const wrapper = mountTable([REQ], true)
    await wrapper.find('[data-test="approve-req_0001"]').trigger('click')
    expect(wrapper.emitted('approve')![0]).toEqual([REQ])

    await wrapper.find('[data-test="reject-req_0001"]').trigger('click')
    expect(wrapper.emitted('reject')![0]).toEqual([REQ])
  })

  it('hides approve/reject buttons when canApprove is false', () => {
    const wrapper = mountTable([REQ], false)
    expect(wrapper.find('[data-test="approve-req_0001"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="reject-req_0001"]').exists()).toBe(false)
  })

  it('shows an empty state when there are no requests', () => {
    const wrapper = mountTable([])
    expect(wrapper.find('[data-test="join-requests-empty"]').exists()).toBe(true)
  })
})
