import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import {
  getSpaceDashboard,
  getSpaceOverview,
  getSpaceResources,
  getSpacePersons,
  getSpaceTransactions,
  getSpaceTimeline,
} from './spaces'

function assertNoDbIdKeys(keys: string[]) {
  for (const key of keys) {
    expect(key).not.toBe('id')
    expect(key).not.toBe('pid')
    expect(key).not.toBe('oid')
    expect(key.endsWith('_id')).toBe(false)
  }
}

const fetchMock = vi.fn()

const OVERVIEW = {
  space: { ouid: 'zhangsan_family', name: '张三家庭', type: 'family', role: 'owner' },
  counts: { resources: 6, persons: 4, transactions: 3, recent_events: 2 },
  funds: 8500,
}

const RESOURCES = {
  grouped: {
    physical: [
      {
        name: '教材',
        type: 'physical',
        unit: '本',
        amount: 12,
        description: '小学五年级数学',
        locations: [
          { warehouse_code: 'WH1', location_path: 'A1', quantity: 12, unit: '本' },
        ],
      },
    ],
    knowledge: [{ name: '错题本', type: 'knowledge', unit: '份', amount: null, description: '张小宝错题整理' }],
    financial: [],
    human: [],
  },
}

const PERSONS = [{ name: '张三', puid: 'zhangsan', role: 'owner' }]

const TRANSACTIONS = [
  {
    transaction_uid: 'txn-0001',
    from_party_name: '张三',
    to_party_name: '书店',
    amount: 128,
    category: '教育支出',
    description: '购买教材',
    created_at: '2026-08-01T10:00:00',
  },
]

const TIMELINE = {
  events: [
    {
      seq: 1,
      campaign_code: 'family_learning',
      campaign_name: '家庭学习空间',
      title: '每日学习要求',
      description: '完成数学口算 20 题',
      payload: { info_flow: '通知下发', logistics_flow: '', people_flow: '张小宝', risk: '' },
    },
  ],
}

const DASHBOARD = {
  status: 'ok',
  overview: OVERVIEW,
  resources: RESOURCES,
  persons: PERSONS,
  transactions: TRANSACTIONS,
  timeline: TIMELINE,
}

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(ok ? '' : 'unauthorized'),
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

describe('spaces API', () => {
  it('getSpaceDashboard fetches aggregate data with business fields only', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(DASHBOARD))

    const result = await getSpaceDashboard({ transactionLimit: 10 })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/dashboard?transaction_limit=10')
    expect(options.headers['Authorization']).toBe('Bearer token-123')
    expect(result.overview.space.ouid).toBe('zhangsan_family')
    expect(result.resources.grouped.physical[0].locations?.[0].warehouse_code).toBe('WH1')
    expect(result.persons[0].puid).toBe('zhangsan')
    expect(result.transactions[0].transaction_uid).toBe('txn-0001')
    expect(result.timeline.events[0].campaign_code).toBe('family_learning')
    assertNoDbIdKeys(Object.keys(result.overview.space))
    assertNoDbIdKeys(Object.keys(result.resources.grouped.physical[0]))
    assertNoDbIdKeys(Object.keys(result.persons[0]))
    assertNoDbIdKeys(Object.keys(result.transactions[0]))
  })

  it('getSpaceOverview fetches /spaces/current/overview with Bearer token', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(OVERVIEW))

    const result = await getSpaceOverview()

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/overview')
    expect(options.headers['Authorization']).toBe('Bearer token-123')
    expect(result.space.ouid).toBe('zhangsan_family')
    expect(result.counts.resources).toBe(6)
    expect(result.funds).toBe(8500)
  })

  it('getSpaceResources returns grouped resources with physical locations', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(RESOURCES))

    const result = await getSpaceResources()

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/resources')
    expect(result.grouped.physical[0].locations?.[0].warehouse_code).toBe('WH1')
    expect(result.grouped.knowledge[0].amount).toBeNull()
    assertNoDbIdKeys(Object.keys(result.grouped.physical[0]))
  })

  it('getSpacePersons returns business fields only', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(PERSONS))

    const result = await getSpacePersons()

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/persons')
    expect(result[0].puid).toBe('zhangsan')
    assertNoDbIdKeys(Object.keys(result[0]))
  })

  it('getSpaceTransactions fetches /spaces/current/transactions', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(TRANSACTIONS))

    const result = await getSpaceTransactions()

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/transactions')
    expect(result[0].transaction_uid).toBe('txn-0001')
    assertNoDbIdKeys(Object.keys(result[0]))
  })

  it('getSpaceTransactions passes the limit query parameter', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(TRANSACTIONS))

    await getSpaceTransactions(10)

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/transactions?limit=10')
  })

  it('getSpaceTimeline returns the event sequence', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(TIMELINE))

    const result = await getSpaceTimeline()

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/spaces/current/timeline')
    expect(result.events[0].campaign_code).toBe('family_learning')
    expect(result.events[0].payload.people_flow).toBe('张小宝')
  })

  it('returns empty events when the backend has no timeline', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse({ events: [] }))

    const result = await getSpaceTimeline()
    expect(result.events).toEqual([])
  })

  it('clears the token and rejects on 401', async () => {
    setToken('expired')
    fetchMock.mockResolvedValue(jsonResponse(null, false, 401))

    await expect(getSpaceDashboard()).rejects.toThrow(/unauthorized/)
    expect(localStorage.getItem('unires_token')).toBeNull()
  })
})
