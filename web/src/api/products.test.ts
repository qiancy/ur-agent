import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { setToken } from './client'
import {
  listProducts,
  createProduct,
  setProductStatus,
} from './products'

function assertNoDbIdKeys(keys: string[]) {
  for (const key of keys) {
    expect(key).not.toBe('id')
    expect(key).not.toBe('pid')
    expect(key).not.toBe('oid')
    expect(key.endsWith('_id')).toBe(false)
  }
}

const fetchMock = vi.fn()

const PRODUCTS = [
  {
    product_uid: 'SKU-001',
    unit: '个',
    status: 'active',
    stock_total: 120,
    stock_location_count: 2,
    description: '示例商品',
  },
  {
    product_uid: 'SKU-002',
    unit: '盒',
    status: 'inactive',
    stock_total: 0,
    stock_location_count: 0,
    description: null,
  },
]

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

describe('listProducts', () => {
  it('fetches /seller/products with the stored Bearer token', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(PRODUCTS))

    const rows = await listProducts()

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/products')
    expect(options.headers['Authorization']).toBe('Bearer token-123')
    expect(rows).toHaveLength(2)
    expect(rows[0].product_uid).toBe('SKU-001')
    expect(rows[1].status).toBe('inactive')
    assertNoDbIdKeys(Object.keys(rows[0]))
  })

  it('throws and clears the token when the backend returns 401', async () => {
    setToken('expired')
    fetchMock.mockResolvedValue(jsonResponse(null, false, 401))

    await expect(listProducts()).rejects.toThrow(/unauthorized/)
    expect(localStorage.getItem('unires_token')).toBeNull()
  })
})

describe('createProduct', () => {
  it('posts business fields only to /seller/products', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(PRODUCTS[0], true, 201))

    const result = await createProduct({
      product_uid: 'SKU-001',
      unit: '个',
      description: '示例商品',
    })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/products')
    expect(options.method).toBe('POST')
    const body = JSON.parse(options.body)
    expect(body).toEqual({
      product_uid: 'SKU-001',
      unit: '个',
      description: '示例商品',
    })
    assertNoDbIdKeys(Object.keys(body))
    expect(result.product_uid).toBe('SKU-001')
  })

  it('omits description when it is not provided', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(jsonResponse(PRODUCTS[1], true, 201))

    await createProduct({ product_uid: 'SKU-002', unit: '盒' })

    const [, options] = fetchMock.mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({
      product_uid: 'SKU-002',
      unit: '盒',
    })
  })
})

describe('setProductStatus', () => {
  it('patches the status to /seller/products/{product_uid}', async () => {
    setToken('token-123')
    fetchMock.mockResolvedValue(
      jsonResponse({ product_uid: 'SKU-001', unit: '个', status: 'inactive' }),
    )

    const result = await setProductStatus('SKU-001', 'inactive')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/seller/products/SKU-001')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'inactive' })
    expect(result.status).toBe('inactive')
    assertNoDbIdKeys(Object.keys(result))
  })

  it('throws and clears the token on 401', async () => {
    setToken('expired')
    fetchMock.mockResolvedValue(jsonResponse(null, false, 401))

    await expect(setProductStatus('SKU-001', 'active')).rejects.toThrow(
      /unauthorized/,
    )
    expect(localStorage.getItem('unires_token')).toBeNull()
  })
})
