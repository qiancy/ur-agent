import { request } from './client'

export interface SpaceOverviewData {
  space: {
    ouid: string
    name: string
    type: string
    role: string
  }
  counts: {
    resources: number
    persons: number
    transactions: number
    recent_events: number
  }
  funds: number
}

export interface ResourceLocation {
  warehouse_code: string
  location_path: string
  quantity: number
  unit: string
}

export type ResourceType = 'physical' | 'knowledge' | 'financial' | 'human'

export interface SpaceResource {
  name: string
  type: ResourceType
  unit: string | null
  amount: number | null
  description: string | null
  locations?: ResourceLocation[]
}

export interface SpaceResourcesData {
  grouped: {
    physical: SpaceResource[]
    knowledge: SpaceResource[]
    financial: SpaceResource[]
    human: SpaceResource[]
  }
}

export interface SpacePerson {
  name: string
  puid: string
  role: string
}

export interface SpaceTransaction {
  transaction_uid: string
  from_party_name: string
  to_party_name: string
  amount: number
  category: string
  description: string | null
  created_at: string
}

export interface EventPayload {
  info_flow?: string
  logistics_flow?: string
  people_flow?: string
  risk?: string
}

export interface TimelineEvent {
  seq: number
  campaign_code: string
  campaign_name: string
  title: string
  description: string | null
  payload: EventPayload
}

export interface SpaceTimelineData {
  events: TimelineEvent[]
}

export interface SpaceDashboardParams {
  transactionLimit?: number
}

export interface SpaceDashboardData {
  status: string
  overview: SpaceOverviewData
  resources: SpaceResourcesData
  persons: SpacePerson[]
  transactions: SpaceTransaction[]
  timeline: SpaceTimelineData
}

export async function getSpaceOverview(): Promise<SpaceOverviewData> {
  return request<SpaceOverviewData>('/spaces/current/overview')
}

export async function getSpaceDashboard(
  params: SpaceDashboardParams = {},
): Promise<SpaceDashboardData> {
  const query = new URLSearchParams()
  if (params.transactionLimit) query.set('transaction_limit', String(params.transactionLimit))
  const qs = query.toString()
  return request<SpaceDashboardData>(
    `/spaces/current/dashboard${qs ? `?${qs}` : ''}`,
  )
}

export async function getSpaceResources(): Promise<SpaceResourcesData> {
  return request<SpaceResourcesData>('/spaces/current/resources')
}

export async function getSpacePersons(): Promise<SpacePerson[]> {
  return request<SpacePerson[]>('/spaces/current/persons')
}

export async function getSpaceTransactions(
  limit?: number,
): Promise<SpaceTransaction[]> {
  const query = new URLSearchParams()
  if (limit) query.set('limit', String(limit))
  const qs = query.toString()
  return request<SpaceTransaction[]>(
    `/spaces/current/transactions${qs ? `?${qs}` : ''}`,
  )
}

export async function getSpaceTimeline(): Promise<SpaceTimelineData> {
  return request<SpaceTimelineData>('/spaces/current/timeline')
}
