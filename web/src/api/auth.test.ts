import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import {
  myOrganizations,
  switchOrganization,
  registerAccount,
  loginAccount,
} from './auth'

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
      organizations: [
        { ouid: 'taobao_shop_a', name: '淘宝小店 A', type: 'ecommerce', role: 'owner' },
        { ouid: 'family', name: '我的家庭', type: 'family', role: 'member' },
      ],
      requires_organization: false,
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
    expect(result.organization?.ouid).toBe('family')
    if (result.organization) assertNoDbIdKeys(Object.keys(result.organization))
    assertNoDbIdKeys(Object.keys(result.person))
  })
})

describe('registerAccount', () => {
  it('posts login/password/name and optional puid/initial_ouid to /auth/register', async () => {
    const body = {
      access_token: 'token-r',
      token_type: 'bearer',
      person: { puid: 'newbie', name: '新手' },
      organization: { ouid: 'shop_a', name: '新店铺', type: 'ecommerce' },
      membership: { role: 'member' },
      system_role: 'user',
      organizations: [
        { ouid: 'shop_a', name: '新店铺', type: 'ecommerce', role: 'member' },
      ],
      requires_organization: false,
    }
    fetchMock.mockResolvedValue(jsonResponse(body))

    const result = await registerAccount({
      login: 'newbie',
      password: 'pass123',
      name: '新手',
      puid: 'newbie',
      initialOuid: 'shop_a',
    })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/auth/register')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({
      login: 'newbie',
      password: 'pass123',
      name: '新手',
      puid: 'newbie',
      initial_ouid: 'shop_a',
    })
    expect(localStorage.getItem('unires_token')).toBe('token-r')
    assertNoDbIdKeys(Object.keys(result.person))
    if (result.organization) assertNoDbIdKeys(Object.keys(result.organization))
    for (const org of result.organizations) {
      assertNoDbIdKeys(Object.keys(org))
    }
  })

  it('omits optional puid/initial_ouid and does not store a token when no space yet', async () => {
    const body = {
      access_token: null,
      token_type: 'bearer',
      person: { puid: 'newbie', name: '新手' },
      organization: null,
      membership: null,
      system_role: 'user',
      organizations: [],
      requires_organization: true,
    }
    fetchMock.mockResolvedValue(jsonResponse(body))

    const result = await registerAccount({
      login: 'newbie',
      password: 'pass123',
      name: '新手',
    })

    const [, options] = fetchMock.mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({
      login: 'newbie',
      password: 'pass123',
      name: '新手',
    })
    expect(localStorage.getItem('unires_token')).toBeNull()
    expect(result.requires_organization).toBe(true)
  })
})

describe('loginAccount', () => {
  it('posts only login/password to /auth/login and stores the token', async () => {
    const body = {
      access_token: 'token-9',
      token_type: 'bearer',
      person: { puid: 'zhansan', name: '张三' },
      organization: { ouid: 'zhansan_shop', name: '张三小铺', type: 'ecommerce' },
      membership: { role: 'owner' },
      system_role: 'user',
      organizations: [
        { ouid: 'zhansan_shop', name: '张三小铺', type: 'ecommerce', role: 'owner' },
      ],
      requires_organization: false,
    }
    fetchMock.mockResolvedValue(jsonResponse(body))

    const result = await loginAccount('zhansan', 'demo123')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/auth/login')
    expect(JSON.parse(options.body)).toEqual({ login: 'zhansan', password: 'demo123' })
    expect(localStorage.getItem('unires_token')).toBe('token-9')
    expect(result.organization?.ouid).toBe('zhansan_shop')
  })
})
