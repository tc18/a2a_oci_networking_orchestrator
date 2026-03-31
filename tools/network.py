import oci
from config import get_oci_config, COMPARTMENT_OCID, OciHelper

def _vn_client():
    return OciHelper.get_client("virtual_network", region="us-ashburn-1")

# ── Tool definitions (schema for the LLM) ──────────────────────────────────
TOOLS = [
    {
        "name": "list_vcns",
        "description": "List all VCNs in a compartment.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False}
        }
    },
    {
        "name": "get_vcn",
        "description": "Get details of a specific VCN by OCID.",
        "parameters": {
            "vcn_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "list_subnets",
        "description": "List subnets in a VCN.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False},
            "vcn_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "get_route_tables",
        "description": "List route tables for a VCN.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False},
            "vcn_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "get_drg_attachments",
        "description": "List DRG attachments for a VCN or DRG.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False},
            "vcn_id": {"type": "str", "required": False},
            "drg_id": {"type": "str", "required": False}
        }
    },
    {
        "name": "get_drg_route_table",
        "description": "Get route table entries for a DRG route table.",
        "parameters": {
            "drg_route_table_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "get_security_lists",
        "description": "List security lists for a subnet.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False},
            "vcn_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "get_nsg_rules",
        "description": "Get NSG security rules for a network security group.",
        "parameters": {
            "nsg_id": {"type": "str", "description": "NSG OCID", "required": True}
        }
    },
]

def slim_tools(tools: list[dict]) -> list[dict]:
    """Strip verbose fields from tool schemas before sending to LLM."""
    result = []
    for t in tools:
        slim_params = {
            k: {"type": v["type"]}
            for k, v in t.get("parameters", {}).items()
        }
        result.append({
            "name": t["name"],
            "description": t["description"],
            "parameters": slim_params,
        })
    return result

# ── Tool implementations ────────────────────────────────────────────────────
def list_vcns(compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    print(cid)
    print("you are in list_vcn")
    items = _vn_client().list_vcns(compartment_id=cid).data
    return [{"id": v.id, "display_name": v.display_name, "cidr_block": v.cidr_block} for v in items]

def get_vcn(vcn_id: str):
    v = _vn_client().get_vcn(vcn_id).data
    return {"id": v.id, "display_name": v.display_name, "cidr_block": v.cidr_block, "state": v.lifecycle_state}

def list_subnets(vcn_id: str, compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _vn_client().list_subnets(compartment_id=cid, vcn_id=vcn_id).data
    return [{"id": s.id, "display_name": s.display_name, "cidr_block": s.cidr_block,
             "route_table_id": s.route_table_id} for s in items]

def get_route_tables(vcn_id: str, compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    tables = _vn_client().list_route_tables(compartment_id=cid, vcn_id=vcn_id).data
    result = []
    for rt in tables:
        rules = []
        for r in rt.route_rules:
            rules.append({
                "destination": r.destination,
                "destination_type": r.destination_type,
                "network_entity_id": r.network_entity_id,
            })
        result.append({"id": rt.id, "display_name": rt.display_name, "rules": rules})
    return result

def get_drg_attachments(compartment_id: str = None, vcn_id: str = None, drg_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _vn_client().list_drg_attachments(
        compartment_id=cid,
        vcn_id=vcn_id,
        drg_id=drg_id,
    ).data
    return [{"id": a.id, "drg_id": a.drg_id, "vcn_id": a.vcn_id,
             "drg_route_table_id": a.drg_route_table_id} for a in items]

def get_drg_route_table(drg_route_table_id: str):
    rt = _vn_client().get_drg_route_table(drg_route_table_id).data
    rules = _vn_client().list_drg_route_rules(drg_route_table_id).data
    return {
        "id": rt.id,
        "display_name": rt.display_name,
        "rules": [{"destination": r.destination, "next_hop_drg_attachment_id": r.next_hop_drg_attachment_id} for r in rules]
    }

def get_security_lists(vcn_id: str, compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _vn_client().list_security_lists(compartment_id=cid, vcn_id=vcn_id).data
    result = []
    for sl in items:
        result.append({
            "id": sl.id,
            "display_name": sl.display_name,
            "ingress_rules": [{"protocol": r.protocol, "source": r.source} for r in sl.ingress_security_rules],
            "egress_rules": [{"protocol": r.protocol, "destination": r.destination} for r in sl.egress_security_rules],
        })
    return result

def get_nsg_rules(nsg_id: str):
    rules = _vn_client().list_network_security_group_security_rules(nsg_id).data
    return [{"direction": r.direction, "protocol": r.protocol, "source": getattr(r, "source", None),
             "destination": getattr(r, "destination", None)} for r in rules]

# ── Dispatch ────────────────────────────────────────────────────────────────
TOOL_MAP = {
    "list_vcns": list_vcns,
    "get_vcn": get_vcn,
    "list_subnets": list_subnets,
    "get_route_tables": get_route_tables,
    "get_drg_attachments": get_drg_attachments,
    "get_drg_route_table": get_drg_route_table,
    "get_security_lists": get_security_lists,
    "get_nsg_rules": get_nsg_rules,
}