import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import {
  sellerLogin,
  sellerSummary,
  sellerWorkbench,
  sellerStock,
  sellerInventoryMovements,
  sellerPurchaseIn,
  sellerSalesOut,
  sellerChat,
} from './seller'

function assertNoDbIdKeys(keys: string[]) {
  for (const key of keys) {
    expect(key).not.toBe('id')
    expect(key).not.toBe('pid')
    expect(key).not.toBe('oid')
    expect(key.endsWith('_id')).toBe(false)
  }
}

const fetchMock = vi.fn()

const LOGIN_BODY = {
  access_token: 'token-123',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: [
    { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce', role: 'owner' },
  ],
  requires_organization: false,
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

    const result = await sellerLogin('shopkeeper', 'pass123')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/auth/seller-login')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({
      login: 'shopkeeper',
      password: 'pass123',
    })
    expect(localStorage.getItem('unires_token')).toBe('token-123')
    expect(result.access_token).toBe('token-123')
    expect(result.organization?.ouid).toBe('shop_demo')
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

const STOCK_ROWS = [
  {
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity: 4,
    unit: '件',
  },
  {
    product_uid: 'charger_20w',
    warehouse_code: 'WH-A',
    location_path: 'A-03-02',
    quantity: 2,
    unit: '件',
  },
]

const MOVEMENTS = [
  {
    movement_uid: 'mv_000000000001',
    operation_type: 'purchase_in',
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity_delta: 20,
    new_quantity: 24,
    unit: '件',
    total_amount: 80,
    counterparty_name: '供应商甲',
    created_at: '2026-08-02T10:00:00',
  },
]

const WORKBENCH_BODY = {
  status: 'ok',
  summary: SUMMARY_BODY,
  stock: STOCK_ROWS,
  movements: MOVEMENTS,
}

describe('sellerStock', () => {
  it('fetches /seller/stock and returns stock rows', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(STOCK_ROWS))

    const rows = await sellerStock()

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/stock')
    expect(rows[0].product_uid).toBe('usb_cable_1m')
    expect(rows[0].warehouse_code).toBe('WH-A')
  })

  it('passes product_uid as a query parameter', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(STOCK_ROWS))

    await sellerStock('usb_cable_1m')

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('product_uid=usb_cable_1m')
  })
})

describe('sellerInventoryMovements', () => {
  it('fetches /seller/inventory-movements and returns movement rows', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(MOVEMENTS))

    const rows = await sellerInventoryMovements()

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/inventory-movements')
    expect(rows[0].operation_type).toBe('purchase_in')
    expect(rows[0].movement_uid).toBe('mv_000000000001')
  })

  it('passes operation_type, date_from, date_to and limit filters', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(MOVEMENTS))

    await sellerInventoryMovements({
      operationType: 'sales_out',
      dateFrom: '2026-08-01',
      dateTo: '2026-08-02',
      limit: 20,
    })

    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('operation_type=sales_out')
    expect(url).toContain('date_from=2026-08-01')
    expect(url).toContain('date_to=2026-08-02')
    expect(url).toContain('limit=20')
  })
})

describe('sellerWorkbench', () => {
  it('fetches /seller/workbench with aggregate params and business fields only', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(WORKBENCH_BODY))

    const data = await sellerWorkbench({
      movementsLimit: 10,
      lowStockThreshold: 5,
      topN: 6,
    })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/workbench')
    expect(url).toContain('movements_limit=10')
    expect(url).toContain('low_stock_threshold=5')
    expect(url).toContain('top_n=6')
    expect(options.headers['Authorization']).toBe('Bearer token-123')
    expect(data.summary.sales_amount).toBe(1280)
    expect(data.stock[0].product_uid).toBe('usb_cable_1m')
    expect(data.movements[0].movement_uid).toBe('mv_000000000001')
    assertNoDbIdKeys(Object.keys(data.summary))
    assertNoDbIdKeys(Object.keys(data.stock[0]))
    assertNoDbIdKeys(Object.keys(data.movements[0]))
  })

  it('clears the token when the aggregate endpoint returns 401', async () => {
    setToken('expired')
    fetchMock.mockResolvedValue(jsonResponse(null, false, 401))

    await expect(sellerWorkbench()).rejects.toThrow(/unauthorized/)
    expect(localStorage.getItem('unires_token')).toBeNull()
  })
})

describe('sellerPurchaseIn', () => {
  it('posts business fields only to /seller/purchase-in', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse({ status: 'ok', new_quantity: 24 }))

    await sellerPurchaseIn({
      product_uid: 'usb_cable_1m',
      warehouse_code: 'WH-A',
      location_path: 'A-02-01',
      quantity: 20,
      unit: '件',
      total_amount: 80,
      counterparty_name: '供应商甲',
    })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/purchase-in')
    const body = JSON.parse(options.body)
    expect(body).toEqual({
      product_uid: 'usb_cable_1m',
      warehouse_code: 'WH-A',
      location_path: 'A-02-01',
      quantity: 20,
      unit: '件',
      total_amount: 80,
      counterparty_name: '供应商甲',
    })
    const bodyKeys = Object.keys(body)
    assertNoDbIdKeys(bodyKeys)
  })
})

describe('sellerSalesOut', () => {
  it('posts business fields only to /seller/sales-out', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse({ status: 'ok', new_quantity: 4 }))

    await sellerSalesOut({
      product_uid: 'usb_cable_1m',
      warehouse_code: 'WH-A',
      location_path: 'A-02-01',
      quantity: 20,
      unit: '件',
      total_amount: 60,
      counterparty_name: '买家乙',
    })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/sales-out')
    const body = JSON.parse(options.body)
    expect(body).toEqual({
      product_uid: 'usb_cable_1m',
      warehouse_code: 'WH-A',
      location_path: 'A-02-01',
      quantity: 20,
      unit: '件',
      total_amount: 60,
      counterparty_name: '买家乙',
    })
    assertNoDbIdKeys(Object.keys(body))
  })
})

describe('sellerChat', () => {
  it('posts only the message to /seller/chat and returns the response', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(
      jsonResponse({ response: '今日销售收入 ¥12,840', ouid: 'shop_demo' }),
    )

    const result = await sellerChat('今天销售收入是多少？')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/chat')
    expect(JSON.parse(options.body)).toEqual({ message: '今天销售收入是多少？' })
    expect(result.response).toContain('12,840')
  })
})
