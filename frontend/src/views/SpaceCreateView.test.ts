import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SpaceCreateView from './SpaceCreateView.vue'
import { createSpace } from '../api/spaceGovernance'

vi.mock('../api/spaceGovernance', () => ({
  createSpace: vi.fn(),
}))

const createSpaceMock = vi.mocked(createSpace)

const RESULT = {
  access_token: 'new-token',
  token_type: 'bearer',
  person: { puid: 'zhangsan', name: '张三' },
  organization: { ouid: 'org_shop', name: '新店', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: [{ ouid: 'org_shop', name: '新店', type: 'ecommerce', role: 'owner' }],
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
  return mount(SpaceCreateView, { props: BASE_PROPS })
}

describe('SpaceCreateView', () => {
  beforeEach(() => {
    createSpaceMock.mockReset()
    createSpaceMock.mockResolvedValue(RESULT)
  })

  it('validates that the name is required', async () => {
    const wrapper = mountView()
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('[data-test="create-error"]').text()).toContain('空间名称')
    expect(createSpaceMock).not.toHaveBeenCalled()
  })

  it('posts name and org_type on submit', async () => {
    const wrapper = mountView()
    await wrapper.find('[data-test="create-name"]').setValue('新店')
    await wrapper.find('[data-test="create-org-type"]').setValue('ecommerce')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createSpaceMock).toHaveBeenCalledWith({
      name: '新店',
      org_type: 'ecommerce',
    })
    expect(wrapper.emitted('context-updated')![0]).toEqual([RESULT])
  })

  it('sends optional ouid and description when filled', async () => {
    const wrapper = mountView()
    await wrapper.find('[data-test="create-name"]').setValue('家庭账本')
    await wrapper.find('[data-test="create-org-type"]').setValue('family')
    await wrapper.find('[data-test="create-ouid"]').setValue('family_2026')
    await wrapper.find('[data-test="create-description"]').setValue('我家')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createSpaceMock).toHaveBeenCalledWith({
      name: '家庭账本',
      org_type: 'family',
      ouid: 'family_2026',
      description: '我家',
    })
  })

  it('surfaces an API error', async () => {
    createSpaceMock.mockRejectedValue(new Error('ouid taken'))
    const wrapper = mountView()
    await wrapper.find('[data-test="create-name"]').setValue('X')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[data-test="create-error"]').text()).toContain('ouid taken')
  })

  it('navigates back to manage', async () => {
    const wrapper = mountView()
    await wrapper.find('[data-test="back-to-manage"]').trigger('click')
    expect(wrapper.emitted('navigate-space')![0]).toEqual(['manage'])
  })
})
