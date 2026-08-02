import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import {
  API_BASE,
  apiUrl,
  setToken,
  getToken,
  clearToken,
  request,
  ApiError,
} from './client'
import { isAuthenticated, setAuthenticated } from './session'

const TOKEN_KEY = 'unires_token'

describe('client token persistence', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('setToken stores the token and getToken reads it back', () => {
    setToken('abc.def.ghi')
    expect(getToken()).toBe('abc.def.ghi')
    expect(localStorage.getItem(TOKEN_KEY)).toBe('abc.def.ghi')
  })

  it('clearToken removes the stored token', () => {
    setToken('abc')
    clearToken()
    expect(getToken()).toBeNull()
  })
})

describe('client request', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    localStorage.clear()
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('apiUrl prefixes API_BASE to the path', () => {
    expect(apiUrl('/seller/summary')).toBe(`${API_BASE}/seller/summary`)
  })

  it('attaches Authorization Bearer header when a token is set', async () => {
    setToken('jwt-token-1')
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'ok' }),
    })

    await request('/seller/summary')

    const [, options] = fetchMock.mock.calls[0]
    expect(options.headers['Authorization']).toBe('Bearer jwt-token-1')
  })

  it('sends no Authorization header without a token', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'ok' }),
    })

    await request('/seller/summary')

    const [, options] = fetchMock.mock.calls[0]
    expect(options.headers['Authorization']).toBeUndefined()
  })

  it('throws ApiError with status and body on non-ok response', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      text: () => Promise.resolve('Authentication required.'),
    })

    await expect(request('/seller/summary')).rejects.toThrow(ApiError)
    await expect(request('/seller/summary')).rejects.toThrow(
      /Authentication required/,
    )
  })

  it('clears the token when the server responds 401', async () => {
    setToken('expired-token')
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      text: () => Promise.resolve('unauthorized'),
    })

    await expect(request('/seller/summary')).rejects.toThrow(ApiError)
    expect(getToken()).toBeNull()
  })

  it('marks the session unauthenticated on 401 so the app returns to login', async () => {
    setToken('expired-token')
    setAuthenticated(true)
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      text: () => Promise.resolve('unauthorized'),
    })

    await expect(request('/seller/summary')).rejects.toThrow(ApiError)
    expect(isAuthenticated.value).toBe(false)
  })
})
