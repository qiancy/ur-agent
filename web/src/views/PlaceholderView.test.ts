import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PlaceholderView from './PlaceholderView.vue'

describe('PlaceholderView', () => {
  it('renders the default message 功能即将开放', () => {
    const wrapper = mount(PlaceholderView)
    expect(wrapper.find('[data-test="placeholder-view"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="placeholder-message"]').text()).toBe(
      '功能即将开放',
    )
  })

  it('renders a custom message passed via props', () => {
    const wrapper = mount(PlaceholderView, {
      props: { message: '该业务空间暂未接入 AI' },
    })
    expect(wrapper.find('[data-test="placeholder-message"]').text()).toBe(
      '该业务空间暂未接入 AI',
    )
  })
})
