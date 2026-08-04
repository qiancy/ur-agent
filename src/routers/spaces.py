"""Spaces observation + governance endpoints (BE-10 / AUTH-03).

Strict JWT only (`require_strict_org_context`) — never accepts ouid/puid query
params. Business-facing DTOs only, no DB numeric ids.
"""
from fastapi import APIRouter, HTTPException, Query, Request
from psycopg2.errors import UniqueViolation

from src.routers.deps import require_authenticated, require_strict_org_context
from src.db.database import (
    get_space_overview, get_space_resources, get_space_persons,
    get_space_transactions, get_space_timeline,
    query_organization_by_ouid, query_person_by_puid, query_membership,
    create_org_with_owner, create_org_invite,
    query_invite_by_uid, accept_invite,
    create_join_request as db_create_join_request,
    query_join_request_by_uid,
    approve_join_request as db_approve_join_request,
    remove_membership, count_org_owners, transfer_ownership,
    list_org_members_dto, list_org_join_requests_dto,
    list_person_invites_dto, list_person_join_requests_dto,
    reject_join_request as db_reject_join_request,
)
from src.models.schemas import (
    SpaceCreate, InviteCreate, AcceptInviteRequest, JoinRequestCreate,
    ApproveJoinRequestRequest, RejectJoinRequestRequest,
    LeaveSpaceRequest, KickMemberRequest,
    TransferOwnerRequest,
)

router = APIRouter(prefix="/spaces", tags=["spaces"])

_IDENTITY_QUERY_PARAMS = {"puid", "ouid"}

_VALID_ORG_TYPES = {"family", "ecommerce", "campaign", "starship", "company"}

# Governance responses carry only business fields (puid/ouid/uid), never DB ids.
_GOV_FORBIDDEN = {"id", "organization_id", "membership_id"}


def _reject_identity_params(request: Request) -> None:
    """Reject identity/internal-PK query params; context comes only from JWT."""
    for key in request.query_params:
        key_l = key.lower()
        if key_l == "id" or key_l.endswith("_id") or key_l in _IDENTITY_QUERY_PARAMS:
            raise HTTPException(400, f"Query parameter '{key}' is not allowed")


def _gov_dto(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k not in _GOV_FORBIDDEN}


def _get_person_org(puid: str, ouid: str):
    from src.db.database import query_person_by_puid, query_organization_by_ouid, query_membership
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(404, "Person not found")
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    memberships = query_membership(persons[0]["id"], orgs[0]["id"])
    return persons[0], orgs[0], (memberships[0] if memberships else None)


def _fetch_account_for_person(person_id: int, payload: dict):
    from src.db.database import _fetch
    accounts = _fetch("SELECT * FROM account WHERE person_id = %s ORDER BY id",
                      (person_id,))
    return accounts or [{
        "system_role": payload.get("system_role", "user"),
        "login": payload.get("puid"), "status": "active",
    }]


def _org_ouid_by_id(organization_id: int) -> str:
    from src.db.database import _fetch
    rows = _fetch("SELECT ouid FROM organization WHERE id = %s", (organization_id,))
    if not rows:
        raise HTTPException(404, "Organization not found")
    return rows[0]["ouid"]


def query_organization_by_id(organization_id: int):
    from src.db.database import _fetch
    return _fetch("SELECT * FROM organization WHERE id = %s", (organization_id,))


@router.get("/current/overview")
async def space_overview(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_overview(ctx["organization_id"], ctx.get("role"))


@router.get("/current/resources")
async def space_resources(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_resources(ctx["organization_id"])


@router.get("/current/persons")
async def space_persons(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_persons(ctx["organization_id"])


@router.get("/current/transactions")
async def space_transactions(request: Request, limit: int = Query(default=20, ge=1, le=100)):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_transactions(ctx["organization_id"], limit=limit)


@router.get("/current/timeline")
async def space_timeline(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return {"events": get_space_timeline(ctx["organization_id"])}


@router.post("", status_code=201)
async def create_space(body: SpaceCreate, request: Request):
    """Create an organization; caller becomes its owner. JWT required."""
    payload = require_authenticated(request)
    if not body.name.strip():
        raise HTTPException(422, "name is required")
    if body.org_type not in _VALID_ORG_TYPES:
        raise HTTPException(422, f"org_type must be one of {sorted(_VALID_ORG_TYPES)}")
    if body.org_type == "personal":
        raise HTTPException(422, "personal spaces are auto-created at registration")
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    person = persons[0]
    try:
        org = create_org_with_owner(body.name, body.org_type, person["id"],
                                    description=body.description, ouid=body.ouid)
    except UniqueViolation:
        raise HTTPException(409, "ouid already taken")
    from src.db.database import query_membership as _qm
    membership = _qm(person["id"], org["id"])[0]
    from src.routers.auth import _context_dto
    account = _fetch_account_for_person(person["id"], payload)[0]
    return _context_dto(person, org, account, membership)


@router.post("/{ouid}/invites", status_code=201)
async def create_invite(ouid: str, body: InviteCreate, request: Request):
    """owner/admin of the org creates an invite. JWT must be in that org context."""
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != ouid:
        raise HTTPException(403, "Invite must be created from the target org context")
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can create invites")
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Personal spaces do not accept invites (MVP)")
    role = body.role or "member"
    if role not in ("member", "viewer"):
        raise HTTPException(422, "invite role must be 'member' or 'viewer'")
    invite = create_org_invite(orgs[0]["id"], body.invitee_puid, role,
                               ctx["puid"])
    return _gov_dto({
        "invite_uid": invite["invite_uid"],
        "ouid": ouid,
        "invitee_puid": body.invitee_puid,
        "role": invite["role"],
        "status": invite["status"],
    })


@router.post("/invites/accept")
async def accept_org_invite(body: AcceptInviteRequest, request: Request):
    """Invitee accepts an invite (JWT person must match invitee_puid)."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    invites = query_invite_by_uid(body.invite_uid)
    if not invites:
        raise HTTPException(404, "Invite not found")
    invite = invites[0]
    if invite["invitee_puid"] != puid:
        raise HTTPException(403, "Invite belongs to another person")
    if invite["status"] != "pending":
        raise HTTPException(409, "Invite already used")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    membership = accept_invite(body.invite_uid, persons[0]["id"])
    if not membership:
        raise HTTPException(409, "Invite already used or already a member")
    return _gov_dto({
        "ouid": _org_ouid_by_id(invite["organization_id"]),
        "puid": puid,
        "role": membership["role"],
        "status": "accepted",
    })


@router.post("/{ouid}/join-requests", status_code=201)
async def create_join_request(ouid: str, body: JoinRequestCreate, request: Request):
    """Any authenticated user may request to join an org (not the personal type)."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Personal spaces are not joinable (MVP)")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    if query_membership(persons[0]["id"], orgs[0]["id"]):
        raise HTTPException(409, "Already a member")
    req = db_create_join_request(orgs[0]["id"], puid, message=body.message)
    return _gov_dto({
        "request_uid": req["request_uid"],
        "ouid": ouid,
        "requester_puid": puid,
        "message": req.get("message"),
        "status": req["status"],
    })


@router.post("/join-requests/approve")
async def approve_join_request(body: ApproveJoinRequestRequest, request: Request):
    """owner/admin of the target org approves a join request."""
    reqs = query_join_request_by_uid(body.request_uid)
    if not reqs:
        raise HTTPException(404, "Join request not found")
    req = reqs[0]
    if req["status"] != "pending":
        raise HTTPException(409, "Join request already processed")
    orgs = query_organization_by_id(req["organization_id"])
    if not orgs:
        raise HTTPException(404, "Organization not found")
    # caller must be owner/admin of that org (any space context allowed for lookup)
    payload = require_authenticated(request)
    puid = payload.get("puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    memberships = query_membership(persons[0]["id"], req["organization_id"])
    if not memberships or memberships[0]["role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can approve join requests")
    requester = query_person_by_puid(req["requester_puid"])
    if not requester:
        raise HTTPException(404, "Requester person not found")
    membership = db_approve_join_request(body.request_uid, requester[0]["id"])
    if not membership:
        raise HTTPException(409, "Join request already processed or already a member")
    return _gov_dto({
        "request_uid": req["request_uid"],
        "ouid": orgs[0]["ouid"],
        "puid": req["requester_puid"],
        "role": membership["role"],
        "status": "approved",
    })


@router.post("/leave")
async def leave_space(body: LeaveSpaceRequest, request: Request):
    """Member leaves an org. Personal space cannot be left; last owner cannot leave."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    person, org, membership = _get_person_org(puid, body.ouid)
    if not membership:
        raise HTTPException(403, "No membership in this organization")
    if org["type"] == "personal":
        raise HTTPException(422, "Personal space cannot be left")
    if membership["role"] == "owner" and count_org_owners(org["id"]) <= 1:
        raise HTTPException(409, "Last owner cannot leave; transfer ownership first")
    remove_membership(person["id"], org["id"])
    return {"ouid": body.ouid, "puid": puid, "status": "left"}


@router.post("/kick")
async def kick_member(body: KickMemberRequest, request: Request):
    """owner/admin removes a member/viewer; last owner and personal members protected."""
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != body.ouid:
        raise HTTPException(403, "Kick must be issued from the target org context")
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can remove members")
    orgs = query_organization_by_ouid(body.ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Members of a personal space cannot be removed")
    target, _, target_membership = _get_person_org(body.member_puid, body.ouid)
    if not target_membership:
        raise HTTPException(404, "Member not found in this organization")
    if target_membership["role"] == "owner":
        if count_org_owners(orgs[0]["id"]) <= 1:
            raise HTTPException(409, "Cannot remove the last owner")
        raise HTTPException(403, "Owner can only be removed via ownership transfer")
    if target["puid"] == ctx["puid"]:
        raise HTTPException(422, "Use /spaces/leave to leave by yourself")
    remove_membership(target["id"], orgs[0]["id"])
    return {"ouid": body.ouid, "puid": body.member_puid, "status": "removed"}


@router.post("/transfer")
async def transfer_owner(body: TransferOwnerRequest, request: Request):
    """Owner transfers ownership to another member (old owner becomes admin)."""
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != body.ouid:
        raise HTTPException(403, "Transfer must be issued from the target org context")
    if ctx.get("role") != "owner":
        raise HTTPException(403, "Only the owner can transfer ownership")
    if body.new_owner_puid == ctx["puid"]:
        raise HTTPException(422, "Already the owner")
    orgs = query_organization_by_ouid(body.ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    target, _, target_membership = _get_person_org(body.new_owner_puid, body.ouid)
    if not target_membership:
        raise HTTPException(404, "New owner must be an existing member")
    transfer_ownership(orgs[0]["id"], target["id"])
    return {"ouid": body.ouid, "new_owner_puid": body.new_owner_puid, "status": "transferred"}


@router.get("/current/members")
async def space_current_members(request: Request):
    """Members of the current space context (business DTO, no DB ids)."""
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return {"members": list_org_members_dto(ctx["organization_id"])}


@router.get("/current/join-requests")
async def space_current_join_requests(request: Request,
                                      status: str = Query(default="pending")):
    """Pending join requests for the current space (owner/admin only)."""
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can view join requests")
    if status not in ("pending", "approved", "rejected"):
        raise HTTPException(422, "status must be pending, approved or rejected")
    return {"requests": list_org_join_requests_dto(ctx["organization_id"], status=status)}


@router.get("/invites/mine")
async def space_invites_mine(request: Request,
                             status: str = Query(default="pending")):
    """Invites addressed to the authenticated person (pending by default)."""
    _reject_identity_params(request)
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    if status not in ("pending", "accepted", "declined"):
        raise HTTPException(422, "status must be pending, accepted or declined")
    return {"invites": list_person_invites_dto(puid, status=status)}


@router.get("/join-requests/mine")
async def space_join_requests_mine(request: Request,
                                   status: str = Query(default="pending")):
    """Join requests submitted by the authenticated person."""
    _reject_identity_params(request)
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    if status not in ("pending", "approved", "rejected"):
        raise HTTPException(422, "status must be pending, approved or rejected")
    return {"requests": list_person_join_requests_dto(puid, status=status)}


@router.post("/join-requests/reject")
async def reject_join_request(body: RejectJoinRequestRequest, request: Request):
    """owner/admin of the target org rejects a pending join request."""
    reqs = query_join_request_by_uid(body.request_uid)
    if not reqs:
        raise HTTPException(404, "Join request not found")
    req = reqs[0]
    if req["status"] != "pending":
        raise HTTPException(409, "Join request already processed")
    orgs = query_organization_by_id(req["organization_id"])
    if not orgs:
        raise HTTPException(404, "Organization not found")
    payload = require_authenticated(request)
    puid = payload.get("puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    memberships = query_membership(persons[0]["id"], req["organization_id"])
    if not memberships or memberships[0]["role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can reject join requests")
    if not db_reject_join_request(body.request_uid):
        raise HTTPException(409, "Join request already processed")
    return {"request_uid": req["request_uid"], "ouid": orgs[0]["ouid"],
            "requester_puid": req["requester_puid"], "status": "rejected"}
