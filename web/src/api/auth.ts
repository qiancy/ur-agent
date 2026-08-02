import { request, setToken } from './client'
import type { SellerLoginResult } from './seller'

export interface UserOrganization {
  ouid: string
  name: string
  type: string
  role: string
}

export async function myOrganizations(): Promise<UserOrganization[]> {
  return request<UserOrganization[]>('/auth/me/organizations')
}

export async function switchOrganization(
  ouid: string,
): Promise<SellerLoginResult> {
  const result = await request<SellerLoginResult>('/auth/switch-organization', {
    method: 'POST',
    body: JSON.stringify({ ouid }),
  })
  setToken(result.access_token)
  return result
}
