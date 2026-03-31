import oci
from config import OciHelper, COMPARTMENT_OCID 

def _iam():
    return OciHelper.get_client("identity", region="us-ashburn-1")

TOOLS = [
    {
        "name": "list_policies",
        "description": "List IAM policies in a compartment.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False}
        }
    },
    {
        "name": "list_groups",
        "description": "List IAM groups in the tenancy.",
        "parameters": {}
    },
    {
        "name": "list_users_in_group",
        "description": "List users in a specific IAM group.",
        "parameters": {
            "group_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "list_compartments",
        "description": "List all compartments under a parent compartment. Returns name AND ocid for each.",
        "parameters": {
            "compartment_id": {"type": "str", "description": "Parent compartment OCID", "required": False}
        }
    },
]

def list_policies(compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _iam().list_policies(compartment_id=cid).data
    return [{"id": p.id, "name": p.name, "statements": p.statements} for p in items]

def list_groups(compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _iam().list_groups(compartment_id=cid).data
    return [{"id": g.id, "name": g.name, "description": g.description} for g in items]

def list_users_in_group(group_id: str, compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _iam().list_user_group_memberships(
        compartment_id=cid,
        group_id=group_id
    ).data
    users = []
    for m in items:
        u = _iam().get_user(m.user_id).data
        users.append({"id": u.id, "name": u.name, "email": u.email})
    return users

def list_compartments(compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    print("\n"*5)
    print("-"*10)
    print(cid)
    items = _iam().list_compartments(compartment_id=cid).data
    return [{"id": p.id, "name": p.name} for p in items]

TOOL_MAP = {
    "list_policies": list_policies,
    "list_groups": list_groups,
    "list_users_in_group": list_users_in_group,
    "list_compartments": list_compartments,
}