import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import { sellerLogin, sellerSummary } from './seller'

const fetchMock = vi.fn()

const LOGIN_BODY = {
  access_token: 'token-123',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
}

const SUMMARY_BODY = {
  status: 'ok',
  date_from: null,
  date_to: null,
  sales_amount: 1280,
  purchase_amount: 600,
  net_cash_flow: 680,
  purchase_count: 3,
  sales_count: 5,
  movement_count: 8,
  product_count: 4,
  stock_location_count: 6,
  current_stock_quantity: 42,
  estimated_inventory_value: 2100,
  valuation_method: 'weighted_average_purchase_cost',
  low_stock_items: [{ product_uid: 'usb_cable_1m', quantity: 2, unit: '根' }],
  top_products_by_sales: [
    { product_uid: 'usb_cable_1m', sales_amount: 640, sales_quantity: 16 },
  ],
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

describe('sellerLogin', () => {
  it('posts credentials to /auth/seller-login and stores the access token', async () => {
    fetchMock.mockResolvedValue(jsonResponse(LOGIN_BODY))

    const result = await sellerLogin('shopkeeper@shop_demo', 'pass123')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/auth/seller-login')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({
      login: 'shopkeeper@shop_demo',
      password: 'pass123',
    })
    expect(localStorage.getItem('unires_token')).toBe('token-123')
    expect(result.access_token).toBe('token-123')
    expect(result.organization.ouid).toBe('shop_demo')
  })
})

describe('sellerSummary', () => {
  it('fetches /seller/summary with the stored Bearer token', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(SUMMARY_BODY))

    const summary = await sellerSummary()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/summary')
    expect(options.headers['Authorization']).toBe('Bearer token-123')
    expect(summary.sales_amount).toBe(1280)
    expect(summary.low_stock_items[0].product_uid).toBe('usb_cable_1m')
  })

  it('passes date_from and date_to as query parameters', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(SUMMARY_BODY))

    await sellerSummary({ dateFrom: '2026-08-01', dateTo: '2026-08-02' })

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('date_from=2026-08-01')
    expect(url).toContain('date_to=2026-08-02')
  })

  it('throws and clears the token when the backend returns 401', async () => {
    setToken('expired')
    fetchMock.mockResolvedValue(jsonResponse(null, false, 401))

    await expect(sellerSummary()).rejects.toThrow(/unauthorized/)
    expect(localStorage.getItem('unires_token')).toBeNull()
  })
})
