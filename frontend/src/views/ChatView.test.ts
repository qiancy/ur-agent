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

  it('renders the header exchange question and answer when provided', () => {
    const wrapper = mount(ChatView, {
      props: {
        headerExchange: { question: '低库存有哪些', answer: '当前低库存 2 项' },
      },
    })
    expect(wrapper.find('[data-test="header-exchange"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('低库存有哪些')
    expect(wrapper.text()).toContain('当前低库存 2 项')
  })
})
