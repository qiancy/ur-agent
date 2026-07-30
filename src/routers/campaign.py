"""
Campaign import, list, replay, and deletion endpoints.
"""
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request

from src.models.schemas import CampaignImportRequest
from src.routers.deps import (
    require_authenticated, require_system_super,
    get_allowed_organization_ids, is_system_super,
)
from src.db.database import (
    add_membership,
    add_campaign_import_org,
    create_campaign_event,
    create_campaign_import,
    create_organization,
    create_party,
    create_person,
    create_resource,
    create_resource_warehouse,
    create_transaction,
    create_warehouse,
    delete_campaign_import,
    get_campaign_import,
    get_active_campaign_import_by_code,
    get_campaign_import_org_ids,
    get_campaign_replay,
    list_campaign_imports_for_orgs,
    query_membership,
    query_organization_by_ouid,
    query_person_by_puid,
)

router = APIRouter(prefix="/campaigns", tags=["campaign"])

REPO_ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_DIR = REPO_ROOT / "data" / "campaigns"


def _load_template(campaign_code: str) -> tuple[Dict[str, Any], Path]:
    safe_code = campaign_code.strip()
    if not safe_code or any(ch in safe_code for ch in "/\\."):
        raise HTTPException(400, "Invalid campaign_code")
    path = CAMPAIGN_DIR / f"{safe_code}.json"
    if not path.exists():
        raise HTTPException(404, "Campaign template not found")
    try:
        return json.loads(path.read_text(encoding="utf-8")), path
    except json.JSONDecodeError as exc:
        raise HTTPException(500, f"Invalid campaign template JSON: {exc}") from exc


def _find_or_create_org(org_cfg: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
    rows = query_organization_by_ouid(org_cfg["ouid"])
    if rows:
        return rows[0], False
    return create_organization(
        name=org_cfg["name"],
        org_type=org_cfg.get("type", "campaign"),
        description=org_cfg.get("description"),
        funds=org_cfg.get("funds", 0),
        reputation=org_cfg.get("reputation", 0),
        ouid=org_cfg["ouid"],
    ), True


def _find_or_create_person(person_cfg: Dict[str, Any]) -> Dict[str, Any]:
    rows = query_person_by_puid(person_cfg["puid"])
    if rows:
        return rows[0]
    return create_person(name=person_cfg["name"], puid=person_cfg["puid"])


def _direction_amount(direction: str, amount: float) -> float:
    if direction in {"out", "-"}:
        return -abs(float(amount))
    if direction in {"in", "+"}:
        return abs(float(amount))
    raise HTTPException(400, f"Invalid party direction: {direction}")


@router.get("/templates")
async def list_campaign_templates(request: Request):
    require_authenticated(request)
    templates = []
    if CAMPAIGN_DIR.exists():
        for path in sorted(CAMPAIGN_DIR.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            templates.append({
                "campaign_code": data.get("campaign_code", path.stem),
                "campaign_name": data.get("campaign_name", path.stem),
                "source_file": str(path.relative_to(REPO_ROOT)),
            })
    return templates


@router.post("/import", status_code=201)
async def import_campaign(body: CampaignImportRequest, request: Request):
    payload = require_system_super(request)
    template, path = _load_template(body.campaign_code)

    existing = get_active_campaign_import_by_code(template["campaign_code"])
    if existing:
        return {
            "campaign_import": existing[0],
            "already_imported": True,
            "message": "Campaign already imported and active",
        }

    campaign = create_campaign_import(
        campaign_code=template["campaign_code"],
        campaign_name=template["campaign_name"],
        source_file=str(path.relative_to(REPO_ROOT)),
        imported_by_puid=payload["puid"],
    )

    orgs: Dict[str, Dict[str, Any]] = {}
    people: Dict[str, Dict[str, Any]] = {}
    warehouses: Dict[tuple[str, str], Dict[str, Any]] = {}
    resources = []
    transactions = []
    events = []

    try:
        for org_cfg in template.get("organizations", []):
            org, created = _find_or_create_org(org_cfg)
            orgs[org["ouid"]] = org
            add_campaign_import_org(campaign["id"], org["id"], created)

        for person_cfg in template.get("persons", []):
            person = _find_or_create_person(person_cfg)
            people[person["puid"]] = person

        for member_cfg in template.get("memberships", []):
            person = people.get(member_cfg["puid"])
            org = orgs.get(member_cfg["ouid"])
            if not person or not org:
                raise HTTPException(400, "Invalid membership in campaign template")
            if not query_membership(person["id"], org["id"]):
                add_membership(person["id"], org["id"], member_cfg.get("role", "member"))

        for wh_cfg in template.get("warehouses", []):
            org = orgs.get(wh_cfg["ouid"])
            if not org:
                raise HTTPException(400, "Invalid warehouse organization in campaign template")
            wh = create_warehouse(
                org["id"], wh_cfg["name"], wh_cfg["code"],
                wh_cfg.get("location"), wh_cfg.get("description")
            )
            warehouses[(org["ouid"], wh["code"])] = wh

        for res_cfg in template.get("resources", []):
            org = orgs.get(res_cfg["ouid"])
            if not org:
                raise HTTPException(400, "Invalid resource organization in campaign template")
            person_id = None
            if res_cfg.get("puid"):
                person = people.get(res_cfg["puid"])
                if person:
                    person_id = person["id"]
            res = create_resource(
                organization_id=org["id"],
                name=res_cfg["name"],
                resource_type=res_cfg.get("type", "physical"),
                unit=res_cfg.get("unit"),
                amount=res_cfg.get("amount"),
                currency=res_cfg.get("currency"),
                person_id=person_id,
                content=res_cfg.get("content"),
            )
            resources.append(res)
            if res_cfg.get("warehouse_code") and res_cfg.get("amount") is not None:
                wh = warehouses.get((org["ouid"], res_cfg["warehouse_code"]))
                if wh:
                    create_resource_warehouse(
                        res["id"], wh["code"], res_cfg["amount"], res_cfg.get("unit")
                    )
                    create_resource_warehouse(
                        res["id"], "total", res_cfg["amount"], res_cfg.get("unit")
                    )

        for tx_cfg in template.get("transactions", []):
            org = orgs.get(tx_cfg["ouid"])
            if not org:
                raise HTTPException(400, "Invalid transaction organization in campaign template")
            tx = create_transaction(
                amount=tx_cfg["amount"],
                category=tx_cfg["category"],
                description=tx_cfg.get("description"),
                organization_id=org["id"],
            )
            transactions.append(tx)
            for party_cfg in tx_cfg.get("parties", []):
                person = people.get(party_cfg["puid"])
                if not person:
                    raise HTTPException(400, "Invalid transaction party in campaign template")
                create_party(
                    person_id=person["id"],
                    organization_id=org["id"],
                    transaction_id=tx["id"],
                    role=party_cfg.get("role", "participant"),
                    description=party_cfg.get("description"),
                    funds_change=_direction_amount(party_cfg.get("direction", "in"), party_cfg.get("amount", 0)),
                    reputation_change=party_cfg.get("reputation_change", 0),
                )

        for event_cfg in template.get("events", []):
            org = orgs.get(event_cfg["ouid"])
            if not org:
                raise HTTPException(400, "Invalid event organization in campaign template")
            event = create_campaign_event(
                campaign_import_id=campaign["id"],
                organization_id=org["id"],
                seq=event_cfg["seq"],
                title=event_cfg["title"],
                description=event_cfg.get("description"),
                payload=event_cfg,
            )
            events.append(event)
    except Exception:
        delete_campaign_import(campaign["id"])
        raise

    return {
        "campaign_import": campaign,
        "organizations": list(orgs.values()),
        "persons": list(people.values()),
        "resources": len(resources),
        "warehouses": len(warehouses),
        "transactions": len(transactions),
        "events": len(events),
    }


@router.get("/imports")
async def list_campaign_imports(request: Request):
    payload = require_authenticated(request)
    return list_campaign_imports_for_orgs(
        organization_ids=get_allowed_organization_ids(payload),
        include_all=is_system_super(payload),
    )


@router.get("/imports/{campaign_import_id}/replay")
async def replay_campaign(campaign_import_id: int, request: Request):
    payload = require_authenticated(request)
    rows = get_campaign_import(campaign_import_id)
    if not rows or rows[0]["status"] != "active":
        raise HTTPException(404, "Campaign import not found")

    allowed_ids = get_allowed_organization_ids(payload)
    campaign_org_ids = get_campaign_import_org_ids(campaign_import_id)
    if not is_system_super(payload) and not set(allowed_ids).intersection(campaign_org_ids):
        raise HTTPException(403, "No access to this campaign")

    events = get_campaign_replay(
        campaign_import_id,
        organization_ids=allowed_ids,
        include_all=is_system_super(payload),
    )
    return {
        "campaign_import_id": rows[0]["id"],
        "campaign_code": rows[0]["campaign_code"],
        "campaign_name": rows[0]["campaign_name"],
        "events": [
            {
                "seq": row["seq"],
                "title": row["title"],
                "description": row["description"],
                "payload": row["payload"],
                "organization": {
                    "ouid": row["ouid"],
                    "name": row["organization_name"],
                    "type": row["organization_type"],
                },
            }
            for row in events
        ],
    }


@router.delete("/imports/{campaign_import_id}")
async def remove_campaign_import(campaign_import_id: int, request: Request):
    require_system_super(request)
    result = delete_campaign_import(campaign_import_id)
    if not result.get("deleted"):
        raise HTTPException(404, "Campaign import not found")
    return result
