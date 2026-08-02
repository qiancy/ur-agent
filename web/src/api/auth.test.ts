import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import { myOrganizations, switchOrganization } from './auth'

const fetchMock = vi.fn()

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(ok ? '' : 'unauthorized'),
  }
}

function assertNoDbIdKeys(keys: string[]) {
  for (const key of keys) {
    expect(key).not.toBe('id')
    expect(key).not.toBe('pid')
    expect(key).not.toBe('oid')
    expect(key.endsWith('_id')).toBe(false)
  }
}

beforeEach(() => {
  localStorage.clear()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('myOrganizations', () => {
  it('fetches /auth/me/organizations and returns business-only org rows', async () => {
    const body = [
      { ouid: 'taobao_shop_a', name: '淘宝小店 A', type: 'ecommerce', role: 'owner' },
      { ouid: 'family', name: '我的家庭', type: 'family', role: 'member' },
    ]
    setToken('token-1')
    fetchMock.mockResolvedValue(jsonResponse(body))

    const orgs = await myOrganizations()

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/auth/me/organizations')
    expect(options.headers['Authorization']).toBe('Bearer token-1')
    expect(orgs).toHaveLength(2)
    expect(orgs[0].ouid).toBe('taobao_shop_a')
    expect(orgs[1].type).toBe('family')
    for (const row of orgs) {
      assertNoDbIdKeys(Object.keys(row))
    }
  })

  it('throws and clears the token when the backend returns 401', async () => {
    setToken('expired')
    fetchMock.mockResolvedValue(jsonResponse(null, false, 401))

    await expect(myOrganizations()).rejects.toThrow(/unauthorized/)
    expect(localStorage.getItem('unires_token')).toBeNull()
  })
})

describe('switchOrganization', () => {
  it('posts only ouid to /auth/switch-organization and stores the new token', async () => {
    const body = {
      access_token: 'token-2',
      token_type: 'bearer',
      person: { puid: 'zhangsan', name: '张三' },
      organization: { ouid: 'family', name: '我的家庭', type: 'family' },
      membership: { role: 'member' },
      system_role: 'user',
    }
    fetchMock.mockResolvedValue(jsonResponse(body))

    const result = await switchOrganization('family')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/auth/switch-organization')
    expect(options.method).toBe('POST')
    const sent = JSON.parse(options.body)
    expect(sent).toEqual({ ouid: 'family' })
    assertNoDbIdKeys(Object.keys(sent))
    expect(localStorage.getItem('unires_token')).toBe('token-2')
    expect(result.organization.ouid).toBe('family')
    assertNoDbIdKeys(Object.keys(result.organization))
    assertNoDbIdKeys(Object.keys(result.person))
  })
})
