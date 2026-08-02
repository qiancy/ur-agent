import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatView from './ChatView.vue'

vi.mock('../components/ChatPanel.vue', () => ({
  default: {
    template: '<div class="chat-panel-stub" />',
  },
}))

describe('ChatView', () => {
  it('renders a full page with ChatPanel and a read-only hint', () => {
    const wrapper = mount(ChatView)
    expect(wrapper.find('.chat-panel-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('Seller AI')
    expect(wrapper.text()).toContain('只读查询')
  })
})
