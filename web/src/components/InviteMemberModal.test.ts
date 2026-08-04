import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import InviteMemberModal from './InviteMemberModal.vue'
import { createInvite } from '../api/spaceGovernance'

vi.mock('../api/spaceGovernance', () => ({
  createInvite: vi.fn(),
}))

const createInviteMock = vi.mocked(createInvite)

function mountModal(open = true, ouid = 'co_01') {
  return mount(InviteMemberModal, { props: { open, ouid } })
}

describe('InviteMemberModal', () => {
  beforeEach(() => {
    createInviteMock.mockReset()
  })

  it('does not render when closed', () => {
    const wrapper = mountModal(false)
    expect(wrapper.find('[data-test="invite-modal"]').exists()).toBe(false)
  })

  it('renders the form when open', () => {
    const wrapper = mountModal()
    expect(wrapper.find('[data-test="invite-modal"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="invitee-puid"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="invite-role"]').exists()).toBe(true)
  })

  it('validates that invitee puid is required', async () => {
    const wrapper = mountModal()
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('[data-test="invite-error"]').text()).toContain('PUID')
    expect(createInviteMock).not.toHaveBeenCalled()
  })

  it('creates the invite and emits invited then closes', async () => {
    createInviteMock.mockResolvedValue({
      invite_uid: 'inv_1',
      ouid: 'co_01',
      invitee_puid: 'lisi',
      role: 'member',
      status: 'pending',
    })
    const wrapper = mountModal()
    await wrapper.find('[data-test="invitee-puid"]').setValue('lisi')
    await wrapper.find('[data-test="invite-role"]').setValue('viewer')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createInviteMock).toHaveBeenCalledWith('co_01', 'lisi', 'viewer')
    expect(wrapper.emitted('invited')).toBeTruthy()
    expect(wrapper.emitted('invited')![0][0]).toMatchObject({ invite_uid: 'inv_1' })
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close via the close button', async () => {
    const wrapper = mountModal()
    await wrapper.find('[data-test="invite-close"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('surfaces an API error in the form', async () => {
    createInviteMock.mockRejectedValue(new Error('invite failed'))
    const wrapper = mountModal()
    await wrapper.find('[data-test="invitee-puid"]').setValue('lisi')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[data-test="invite-error"]').text()).toContain('invite failed')
  })
})
