import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChatPanel from './ChatPanel.vue'

const chatMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerChat: (...args: unknown[]) => chatMock(...args),
}))

describe('ChatPanel', () => {
  beforeEach(() => {
    chatMock.mockReset()
  })

  it('renders an input and send button', () => {
    const wrapper = mount(ChatPanel)
    expect(wrapper.find('input[data-test="chat-input"]').exists()).toBe(true)
    expect(wrapper.find('button[data-test="chat-send"]').exists()).toBe(true)
  })

  it('sends only the message to sellerChat and renders the ai reply', async () => {
    chatMock.mockResolvedValue({ response: '今日销售收入 ¥12,840', ouid: 'shop_demo' })
    const wrapper = mount(ChatPanel)

    await wrapper.find('input[data-test="chat-input"]').setValue('今天销售收入是多少？')
    await wrapper.find('button[data-test="chat-send"]').trigger('click')
    await flushPromises()

    expect(chatMock).toHaveBeenCalledTimes(1)
    expect(chatMock).toHaveBeenCalledWith('今天销售收入是多少？')
    expect(wrapper.text()).toContain('今天销售收入是多少？')
    expect(wrapper.text()).toContain('12,840')
  })

  it('does not send empty messages', async () => {
    const wrapper = mount(ChatPanel)
    await wrapper.find('button[data-test="chat-send"]').trigger('click')
    expect(chatMock).not.toHaveBeenCalled()
  })

  it('disables the send button while awaiting a reply', async () => {
    let resolveReply: (v: unknown) => void = () => {}
    chatMock.mockImplementation(() => new Promise((resolve) => (resolveReply = resolve)))
    const wrapper = mount(ChatPanel)

    await wrapper.find('input[data-test="chat-input"]').setValue('库存多少？')
    await wrapper.find('button[data-test="chat-send"]').trigger('click')

    expect(wrapper.find('button[data-test="chat-send"]').attributes('disabled')).toBeDefined()

    resolveReply({ response: 'ok', ouid: 'shop_demo' })
    await flushPromises()
  })

  it('shows an error message when the chat request fails', async () => {
    chatMock.mockRejectedValue(new Error('AI 处理失败'))
    const wrapper = mount(ChatPanel)

    await wrapper.find('input[data-test="chat-input"]').setValue('查询')
    await wrapper.find('button[data-test="chat-send"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('AI 处理失败')
  })
})
