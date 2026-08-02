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

export interface SellerStockRow {
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity: number
  unit: string
}

export interface SellerMovement {
  movement_uid: string
  operation_type: 'purchase_in' | 'sales_out'
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity_delta: number
  new_quantity: number
  unit: string
  total_amount: number
  counterparty_name: string
  created_at: string
}

export interface SellerStockParams {
  productUid?: string
}

export async function sellerStock(
  productUid?: string,
): Promise<SellerStockRow[]> {
  const query = new URLSearchParams()
  if (productUid) query.set('product_uid', productUid)
  const qs = query.toString()
  return request<SellerStockRow[]>(
    `/seller/stock${qs ? `?${qs}` : ''}`,
  )
}

export interface MovementParams {
  productUid?: string
  operationType?: string
  dateFrom?: string
  dateTo?: string
  limit?: number
}

export async function sellerInventoryMovements(
  params: MovementParams = {},
): Promise<SellerMovement[]> {
  const query = new URLSearchParams()
  if (params.productUid) query.set('product_uid', params.productUid)
  if (params.operationType) query.set('operation_type', params.operationType)
  if (params.dateFrom) query.set('date_from', params.dateFrom)
  if (params.dateTo) query.set('date_to', params.dateTo)
  if (params.limit) query.set('limit', String(params.limit))
  const qs = query.toString()
  return request<SellerMovement[]>(
    `/seller/inventory-movements${qs ? `?${qs}` : ''}`,
  )
}

export interface SellerPurchaseInRequest {
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity: number
  unit: string
  total_amount: number
  counterparty_name: string
}

export type SellerSalesOutRequest = SellerPurchaseInRequest

export interface SellerEntryResult {
  status: string
  operation_type: string
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity_delta: number
  new_quantity: number
  unit: string
  total_amount: number
  counterparty_name: string
  movement_uid: string
}

export async function sellerPurchaseIn(
  req: SellerPurchaseInRequest,
): Promise<SellerEntryResult> {
  return request<SellerEntryResult>('/seller/purchase-in', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function sellerSalesOut(
  req: SellerSalesOutRequest,
): Promise<SellerEntryResult> {
  return request<SellerEntryResult>('/seller/sales-out', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export interface SellerChatResponse {
  response: string
  ouid: string
}

export async function sellerChat(message: string): Promise<SellerChatResponse> {
  return request<SellerChatResponse>('/seller/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}
