import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginView from './LoginView.vue'

const loginMock = vi.fn()
const registerMock = vi.fn()

vi.mock('../api/auth', () => ({
  loginAccount: (...args: unknown[]) => loginMock(...args),
  registerAccount: (...args: unknown[]) => registerMock(...args),
}))

const RESULT = {
  access_token: 'token-1',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shopkeeper_personal', name: '店主的个人空间', type: 'personal' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: [
    { ouid: 'shopkeeper_personal', name: '店主的个人空间', type: 'personal', role: 'owner' },
  ],
  requires_organization: false,
}

describe('LoginView', () => {
  beforeEach(() => {
    loginMock.mockReset()
    registerMock.mockReset()
  })

  it('renders a login form with login/password fields', () => {
    const wrapper = mount(LoginView)
    expect(wrapper.find('input[data-test="login"]').exists()).toBe(true)
    expect(wrapper.find('input[data-test="password"]').exists()).toBe(true)
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('input[data-test="login"]').attributes('placeholder')).toBe(
      'zhansan',
    )
  })

  it('calls loginAccount with the entered credentials and emits authenticated on success', async () => {
    loginMock.mockResolvedValue(RESULT)
    const wrapper = mount(LoginView)

    await wrapper.find('input[data-test="login"]').setValue('zhansan')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')

    expect(loginMock).toHaveBeenCalledWith('zhansan', 'pass123')
    expect(wrapper.emitted('authenticated')).toBeTruthy()
    expect(wrapper.emitted('authenticated')![0]).toEqual([RESULT])
  })

  it('shows an error message and does not emit on failed login', async () => {
    loginMock.mockRejectedValue(new Error('Invalid credentials'))
    const wrapper = mount(LoginView)

    await wrapper.find('input[data-test="login"]').setValue('zhansan')
    await wrapper.find('input[data-test="password"]').setValue('wrong')
    await wrapper.find('form').trigger('submit')

    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('authenticated')).toBeUndefined()
    expect(wrapper.text()).toContain('Invalid credentials')
  })

  it('switches to register mode and calls registerAccount on submit', async () => {
    registerMock.mockResolvedValue({ ...RESULT, access_token: 'token-r' })
    const wrapper = mount(LoginView)

    await wrapper.find('button[data-test="go-register"]').trigger('click')
    expect(wrapper.find('input[data-test="register-name"]').exists()).toBe(true)

    await wrapper.find('input[data-test="login"]').setValue('newbie')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('input[data-test="register-name"]').setValue('新手')
    await wrapper.find('input[data-test="register-puid"]').setValue('newbie')
    await wrapper.find('form').trigger('submit')

    expect(registerMock).toHaveBeenCalledWith({
      login: 'newbie',
      password: 'pass123',
      name: '新手',
      puid: 'newbie',
    })
    expect(wrapper.emitted('authenticated')).toBeTruthy()
  })

  it('emits authenticated immediately when registration returns a personal space', async () => {
    registerMock.mockResolvedValue({ ...RESULT, access_token: 'token-r' })
    const wrapper = mount(LoginView)

    await wrapper.find('button[data-test="go-register"]').trigger('click')
    await wrapper.find('input[data-test="login"]').setValue('newbie')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('input[data-test="register-name"]').setValue('新手')
    await wrapper.find('form').trigger('submit')

    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('authenticated')).toBeTruthy()
    const emitted = wrapper.emitted('authenticated')![0][0] as { access_token: string }
    expect(emitted.access_token).toBe('token-r')
  })
})
