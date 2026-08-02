import { request, setToken } from './client'

export interface SellerLoginResult {
  access_token: string
  token_type: string
  person: { puid: string; name: string }
  organization: { ouid: string; name: string; type: string }
  membership: { role: string }
  system_role: string
}

export interface SellerSummary {
  status: string
  date_from: string | null
  date_to: string | null
  sales_amount: number
  purchase_amount: number
  net_cash_flow: number
  purchase_count: number
  sales_count: number
  movement_count: number
  product_count: number
  stock_location_count: number
  current_stock_quantity: number
  estimated_inventory_value: number
  valuation_method: string
  low_stock_items: {
    product_uid: string
    quantity: number
    unit: string | null
  }[]
  top_products_by_sales: {
    product_uid: string
    sales_amount: number
    sales_quantity: number
  }[]
}

export async function sellerLogin(
  login: string,
  password: string,
): Promise<SellerLoginResult> {
  const result = await request<SellerLoginResult>('/auth/seller-login', {
    method: 'POST',
    body: JSON.stringify({ login, password }),
  })
  setToken(result.access_token)
  return result
}

export interface SummaryParams {
  dateFrom?: string
  dateTo?: string
}

export async function sellerSummary(
  params: SummaryParams = {},
): Promise<SellerSummary> {
  const query = new URLSearchParams()
  if (params.dateFrom) query.set('date_from', params.dateFrom)
  if (params.dateTo) query.set('date_to', params.dateTo)
  const qs = query.toString()
  return request<SellerSummary>(`/seller/summary${qs ? `?${qs}` : ''}`)
}
