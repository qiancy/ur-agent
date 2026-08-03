import { request, setToken } from './client'
import type { SellerLoginResult, SellerOrgRef } from './seller'

export type UserOrganization = SellerOrgRef

export async function myOrganizations(): Promise<UserOrganization[]> {
  return request<UserOrganization[]>('/auth/me/organizations')
}

export interface RegisterParams {
  login: string
  password: string
  name: string
  puid?: string
  initialOuid?: string
}

export async function registerAccount(
  params: RegisterParams,
): Promise<SellerLoginResult> {
  const body: Record<string, string> = {
    login: params.login,
    password: params.password,
    name: params.name,
  }
  if (params.puid) body.puid = params.puid
  if (params.initialOuid) body.initial_ouid = params.initialOuid
  const result = await request<SellerLoginResult>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  if (result.access_token) setToken(result.access_token)
  return result
}

export async function loginAccount(
  login: string,
  password: string,
): Promise<SellerLoginResult> {
  const result = await request<SellerLoginResult>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ login, password }),
  })
  if (result.access_token) setToken(result.access_token)
  return result
}

export async function switchOrganization(
  ouid: string,
): Promise<SellerLoginResult> {
  const result = await request<SellerLoginResult>('/auth/switch-organization', {
    method: 'POST',
    body: JSON.stringify({ ouid }),
  })
  if (result.access_token) setToken(result.access_token)
  return result
}
