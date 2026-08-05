import { request } from './client'

export type ProductStatus = 'active' | 'inactive'

export interface SellerProduct {
  product_uid: string
  unit: string
  status: ProductStatus
  stock_total: number
  stock_location_count: number
  description: string | null
}

export interface CreateProductRequest {
  product_uid: string
  unit: string
  description?: string
}

export interface ProductStatusResult {
  product_uid: string
  unit: string
  status: ProductStatus
}

export async function listProducts(): Promise<SellerProduct[]> {
  return request<SellerProduct[]>('/seller/products')
}

export async function createProduct(
  input: CreateProductRequest,
): Promise<SellerProduct> {
  return request<SellerProduct>('/seller/products', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function setProductStatus(
  productUid: string,
  status: ProductStatus,
): Promise<ProductStatusResult> {
  return request<ProductStatusResult>(
    `/seller/products/${encodeURIComponent(productUid)}`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    },
  )
}
