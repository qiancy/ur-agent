import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ConfirmDialog from './ConfirmDialog.vue'

function mountDialog(props: Record<string, unknown> = {}) {
  return mount(ConfirmDialog, {
    props: {
      open: true,
      title: '确定？',
      message: '此操作不可撤销',
      ...props,
    },
  })
}

describe('ConfirmDialog', () => {
  it('does not render when closed', () => {
    const wrapper = mountDialog({ open: false })
    expect(wrapper.find('[data-test="confirm-dialog"]').exists()).toBe(false)
  })

  it('renders title and message when open', () => {
    const wrapper = mountDialog()
    expect(wrapper.find('[data-test="confirm-dialog"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('确定？')
    expect(wrapper.find('[data-test="confirm-message"]').text()).toBe('此操作不可撤销')
  })

  it('emits confirm on the confirm button', async () => {
    const wrapper = mountDialog()
    await wrapper.find('[data-test="confirm-ok"]').trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
  })

  it('emits cancel on the cancel button', async () => {
    const wrapper = mountDialog()
    await wrapper.find('[data-test="confirm-cancel"]').trigger('click')
    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  it('renders the danger style for destructive confirms', () => {
    const wrapper = mountDialog({ danger: true })
    expect(wrapper.find('[data-test="confirm-ok"].danger').exists()).toBe(true)
  })
})
