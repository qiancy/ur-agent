import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import {
  getSpaceMembers,
  getSpaceJoinRequests,
  getMyInvites,
  getMyJoinRequests,
  createSpace,
  createInvite,
  acceptInvite,
  createJoinRequest,
  approveJoinRequest,
  rejectJoinRequest,
  leaveSpace,
  kickMember,
  transferOwner,
} from './spaceGovernance'

const fetchMock = vi.fn()

const MEMBERS = {
  members: [
    { puid: 'zhangsan', name: '张三', role: 'owner', joined_at: '2026-08-01T10:00:00' },
    { puid: 'lisi', name: '李四', role: 'member', joined_at: '2026-08-02T10:00:00' },
  ],
}

const JOIN_REQUESTS = {
  requests: [
    {
      request_uid: 'req_0001',
      requester_puid: 'wangwu',
      requester_name: '王五',
      message: '申请加入',
      status: 'pending',
      created_at: '2026-08-03T10:00:00',
    },
  ],
}

const INVITES = {
  invites: [
    {
      invite_uid: 'inv_0001',
      invitee_puid: 'zhangsan',
      role: 'member',
      status: 'pending',
      created_at: '2026-08-03T11:00:00',
      created_by_puid: 'owner1',
      ouid: 'family_01',
      organization_name: '我的家庭',
      organization_type: 'family',
    },
  ],
}

const MY_REQUESTS = {
  requests: [
    {
      request_uid: 'req_0002',
      requester_puid: 'zhangsan',
      message: '求加入',
      status: 'pending',
      created_at: '2026-08-03T12:00:00',
      ouid: 'co_01',
      organization_name: '团队',
      organization_type: 'company',
    },
  ],
}

const CREATE_SPACE_RESULT = {
  access_token: 'new-token',
  token_type: 'bearer',
  person: { puid: 'zhangsan', name: '张三' },
  organization: { ouid: 'org_shop', name: '新店', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: [{ ouid: 'org_shop', name: '新店', type: 'ecommerce', role: 'owner' }],
  requires_organization: false,
}

function assertNoDbIdKeys(keys: string[]) {
  for (const key of keys) {
    expect(key).not.toBe('id')
    expect(key).not.toBe('pid')
    expect(key).not.toBe('oid')
    expect(key.endsWith('_id')).toBe(false)
  }
}

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(ok ? '' : 'error'),
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

describe('spaceGovernance API', () => {
  it('getSpaceMembers fetches /spaces/current/members with Bearer token', async () => {
    setToken('token-x')
    fetchMock.mockResolvedValue(jsonResponse(MEMBERS))

    const result = await getSpaceMembers()

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/members')
    expect(options.headers['Authorization']).toBe('Bearer token-x')
    expect(result.members).toHaveLength(2)
    assertNoDbIdKeys(Object.keys(result.members[0]))
  })

  it('getSpaceJoinRequests lists pending requests', async () => {
    setToken('token-x')
    fetchMock.mockResolvedValue(jsonResponse(JOIN_REQUESTS))

    const result = await getSpaceJoinRequests('pending')

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/join-requests?status=pending')
    expect(result.requests[0].message).toBe('申请加入')
  })

  it('getMyInvites lists pending invites', async () => {
    setToken('token-x')
    fetchMock.mockResolvedValue(jsonResponse(INVITES))

    const result = await getMyInvites('pending')

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/invites/mine?status=pending')
    expect(result.invites[0].organization_name).toBe('我的家庭')
  })

  it('getMyJoinRequests lists my submitted requests', async () => {
    setToken('token-x')
    fetchMock.mockResolvedValue(jsonResponse(MY_REQUESTS))

    const result = await getMyJoinRequests('pending')

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/join-requests/mine?status=pending')
    expect(result.requests[0].ouid).toBe('co_01')
  })

  it('createSpace POSTs name and org_type to /spaces', async () => {
    setToken('token-x')
    fetchMock.mockResolvedValue(jsonResponse(CREATE_SPACE_RESULT, true, 201))

    const result = await createSpace({ name: '新店', org_type: 'ecommerce' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body as string)).toEqual({
      name: '新店',
      org_type: 'ecommerce',
    })
    expect(result.organization?.ouid).toBe('org_shop')
  })

  it('createInvite POSTs invitee_puid and role', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { invite_uid: 'inv_1', ouid: 'co_01', invitee_puid: 'lisi', role: 'viewer', status: 'pending' },
        true,
        201,
      ),
    )

    await createInvite('co_01', 'lisi', 'viewer')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/co_01/invites')
    expect(JSON.parse(options.body as string)).toEqual({
      invitee_puid: 'lisi',
      role: 'viewer',
    })
  })

  it('acceptInvite POSTs the invite uid', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ ouid: 'co_01', puid: 'zhangsan', role: 'member', status: 'accepted' }),
    )

    await acceptInvite('inv_1')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/invites/accept')
    expect(JSON.parse(options.body as string)).toEqual({ invite_uid: 'inv_1' })
  })

  it('createJoinRequest POSTs ouid and message', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { request_uid: 'req_1', ouid: 'co_01', requester_puid: 'zhangsan', message: 'hi', status: 'pending' },
        true,
        201,
      ),
    )

    await createJoinRequest('co_01', 'hi')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/co_01/join-requests')
    expect(JSON.parse(options.body as string)).toEqual({ message: 'hi' })
  })

  it('approveJoinRequest and rejectJoinRequest post the request uid', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ status: 'approved' }))
    await approveJoinRequest('req_1')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({
      request_uid: 'req_1',
    })

    fetchMock.mockResolvedValue(jsonResponse({ status: 'rejected' }))
    await rejectJoinRequest('req_1')
    expect(fetchMock.mock.calls[1][0]).toContain('/spaces/join-requests/reject')
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toEqual({
      request_uid: 'req_1',
    })
  })

  it('leaveSpace, kickMember and transferOwner post business fields only', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ouid: 'co_01', puid: 'zhangsan', status: 'left' }))
    await leaveSpace('co_01')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ ouid: 'co_01' })

    fetchMock.mockResolvedValue(jsonResponse({ ouid: 'co_01', puid: 'lisi', status: 'removed' }))
    await kickMember('co_01', 'lisi')
    expect(fetchMock.mock.calls[1][0]).toContain('/spaces/kick')
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toEqual({
      ouid: 'co_01',
      member_puid: 'lisi',
    })

    fetchMock.mockResolvedValue(jsonResponse({ ouid: 'co_01', new_owner_puid: 'lisi', status: 'transferred' }))
    await transferOwner('co_01', 'lisi')
    expect(fetchMock.mock.calls[2][0]).toContain('/spaces/transfer')
    expect(JSON.parse(fetchMock.mock.calls[2][1].body as string)).toEqual({
      ouid: 'co_01',
      new_owner_puid: 'lisi',
    })
  })
})
