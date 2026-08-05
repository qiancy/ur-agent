import { request } from './client'
import type { SellerLoginResult } from './seller'

export interface SpaceMember {
  puid: string
  name: string
  role: string
  joined_at: string
}

export interface SpaceJoinRequest {
  request_uid: string
  requester_puid: string
  requester_name: string | null
  message: string | null
  status: string
  created_at: string
}

export interface SpaceInvite {
  invite_uid: string
  invitee_puid: string
  role: string
  status: string
  created_at: string
  created_by_puid: string
  ouid: string
  organization_name: string
  organization_type: string
}

export interface MyJoinRequest {
  request_uid: string
  requester_puid: string
  message: string | null
  status: string
  created_at: string
  ouid: string
  organization_name: string
  organization_type: string
}

export interface SpaceMembersData {
  members: SpaceMember[]
}

export interface SpaceJoinRequestsData {
  requests: SpaceJoinRequest[]
}

export interface MyInvitesData {
  invites: SpaceInvite[]
}

export interface MyJoinRequestsData {
  requests: MyJoinRequest[]
}

export async function getSpaceMembers(): Promise<SpaceMembersData> {
  return request<SpaceMembersData>('/spaces/current/members')
}

export async function getSpaceJoinRequests(
  status = 'pending',
): Promise<SpaceJoinRequestsData> {
  return request<SpaceJoinRequestsData>(
    `/spaces/current/join-requests?status=${encodeURIComponent(status)}`,
  )
}

export async function getMyInvites(status = 'pending'): Promise<MyInvitesData> {
  return request<MyInvitesData>(
    `/spaces/invites/mine?status=${encodeURIComponent(status)}`,
  )
}

export async function getMyJoinRequests(
  status = 'pending',
): Promise<MyJoinRequestsData> {
  return request<MyJoinRequestsData>(
    `/spaces/join-requests/mine?status=${encodeURIComponent(status)}`,
  )
}

export interface SpaceCreateParams {
  name: string
  org_type: string
  ouid?: string
  description?: string
}

export async function createSpace(
  params: SpaceCreateParams,
): Promise<SellerLoginResult> {
  return request<SellerLoginResult>('/spaces', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function createInvite(
  ouid: string,
  invitee_puid: string,
  role = 'member',
): Promise<{ invite_uid: string; ouid: string; invitee_puid: string; role: string; status: string }> {
  return request(`/spaces/${encodeURIComponent(ouid)}/invites`, {
    method: 'POST',
    body: JSON.stringify({ invitee_puid, role }),
  })
}

export async function acceptInvite(
  invite_uid: string,
): Promise<{ ouid: string; puid: string; role: string; status: string }> {
  return request('/spaces/invites/accept', {
    method: 'POST',
    body: JSON.stringify({ invite_uid }),
  })
}

export async function createJoinRequest(
  ouid: string,
  message?: string,
): Promise<{ request_uid: string; ouid: string; requester_puid: string; message: string | null; status: string }> {
  return request(`/spaces/${encodeURIComponent(ouid)}/join-requests`, {
    method: 'POST',
    body: JSON.stringify({ message: message ?? null }),
  })
}

export async function approveJoinRequest(
  request_uid: string,
): Promise<{ request_uid: string; ouid: string; puid: string; role: string; status: string }> {
  return request('/spaces/join-requests/approve', {
    method: 'POST',
    body: JSON.stringify({ request_uid }),
  })
}

export async function rejectJoinRequest(
  request_uid: string,
): Promise<{ request_uid: string; ouid: string; requester_puid: string; status: string }> {
  return request('/spaces/join-requests/reject', {
    method: 'POST',
    body: JSON.stringify({ request_uid }),
  })
}

export async function leaveSpace(
  ouid: string,
): Promise<{ ouid: string; puid: string; status: string }> {
  return request('/spaces/leave', {
    method: 'POST',
    body: JSON.stringify({ ouid }),
  })
}

export async function kickMember(
  ouid: string,
  member_puid: string,
): Promise<{ ouid: string; puid: string; status: string }> {
  return request('/spaces/kick', {
    method: 'POST',
    body: JSON.stringify({ ouid, member_puid }),
  })
}

export async function transferOwner(
  ouid: string,
  new_owner_puid: string,
): Promise<{ ouid: string; new_owner_puid: string; status: string }> {
  return request('/spaces/transfer', {
    method: 'POST',
    body: JSON.stringify({ ouid, new_owner_puid }),
  })
}
