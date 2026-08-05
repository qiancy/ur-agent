import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MembersTable from './MembersTable.vue'
import type { SpaceMember } from '../api/spaceGovernance'

const OWNER: SpaceMember = {
  puid: 'zhangsan',
  name: '张三',
  role: 'owner',
  joined_at: '2026-08-01T10:00:00',
}
const ADMIN: SpaceMember = {
  puid: 'lisi',
  name: '李四',
  role: 'admin',
  joined_at: '2026-08-01T10:00:00',
}
const MEMBER: SpaceMember = {
  puid: 'wangwu',
  name: '王五',
  role: 'member',
  joined_at: '2026-08-02T10:00:00',
}

function mountTable(
  members: SpaceMember[],
  currentPuid = 'zhangsan',
  role = 'owner',
) {
  return mount(MembersTable, {
    props: { members, currentPuid, role },
  })
}

describe('MembersTable', () => {
  it('renders every member row with business fields only', () => {
    const wrapper = mountTable([OWNER, MEMBER])
    const rows = wrapper.findAll('[data-test="member-row"]')
    expect(rows).toHaveLength(2)
    expect(wrapper.text()).toContain('zhangsan')
    expect(wrapper.text()).toContain('wangwu')
    expect(wrapper.text()).toContain('owner')
    expect(wrapper.text()).toContain('member')
  })

  it('shows an empty state when there are no members', () => {
    const wrapper = mountTable([])
    expect(wrapper.find('[data-test="members-empty"]').exists()).toBe(true)
  })

  it('owner sees kick for non-owner non-self members and transfer for all non-self', () => {
    const wrapper = mountTable([OWNER, ADMIN, MEMBER], 'zhangsan', 'owner')
    expect(wrapper.find('[data-test="kick-zhangsan"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="kick-wangwu"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="kick-lisi"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="transfer-wangwu"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="transfer-lisi"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="transfer-zhangsan"]').exists()).toBe(false)
  })

  it('admin sees kick for members but no transfer and cannot kick owners', () => {
    const wrapper = mountTable([OWNER, MEMBER], 'lisi', 'admin')
    expect(wrapper.find('[data-test="kick-wangwu"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="kick-zhangsan"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="transfer-wangwu"]').exists()).toBe(false)
  })

  it('plain member sees no management actions', () => {
    const wrapper = mountTable([OWNER, MEMBER], 'wangwu', 'member')
    expect(wrapper.find('[data-test="kick-wangwu"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="kick-zhangsan"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="transfer-zhangsan"]').exists()).toBe(false)
  })

  it('emits kick and transfer with the member payload', async () => {
    const wrapper = mountTable([OWNER, MEMBER], 'zhangsan', 'owner')
    await wrapper.find('[data-test="kick-wangwu"]').trigger('click')
    expect(wrapper.emitted('kick')).toBeTruthy()
    expect(wrapper.emitted('kick')![0]).toEqual([MEMBER])

    await wrapper.find('[data-test="transfer-wangwu"]').trigger('click')
    expect(wrapper.emitted('transfer')![0]).toEqual([MEMBER])
  })
})
