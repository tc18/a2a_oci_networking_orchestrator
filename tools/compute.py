import oci
from config import OciHelper, COMPARTMENT_OCID

def _cc():
    return OciHelper.get_client("identity", region="us-ashburn-1")

TOOLS = [
    {
        "name": "list_instances",
        "description": "List compute instances in a compartment.",
        "parameters": {
            "compartment_id": {"type": "str", "required": False}
        }
    },
    {
        "name": "get_instance",
        "description": "Get details of a specific compute instance.",
        "parameters": {
            "instance_id": {"type": "str", "required": True}
        }
    },
    {
        "name": "get_vnic_attachments",
        "description": "Get VNIC attachments for an instance (returns private/public IPs).",
        "parameters": {
            "instance_id": {"type": "str", "required": True},
            "compartment_id": {"type": "str", "required": False}
        }
    },
]

def list_instances(compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    items = _cc().list_instances(compartment_id=cid).data
    return [{"id": i.id, "display_name": i.display_name,
             "shape": i.shape, "state": i.lifecycle_state} for i in items]

def get_instance(instance_id: str):
    i = _cc().get_instance(instance_id).data
    return {"id": i.id, "display_name": i.display_name, "shape": i.shape,
            "state": i.lifecycle_state, "region": i.region}

def get_vnic_attachments(instance_id: str, compartment_id: str = None):
    cid = compartment_id or COMPARTMENT_OCID
    vn_client = oci.core.VirtualNetworkClient(config=get_oci_config())
    attachments = _cc().list_vnic_attachments(compartment_id=cid, instance_id=instance_id).data
    result = []
    for att in attachments:
        vnic = vn_client.get_vnic(att.vnic_id).data
        result.append({
            "vnic_id": vnic.id,
            "private_ip": vnic.private_ip,
            "public_ip": vnic.public_ip,
            "subnet_id": vnic.subnet_id,
            "is_primary": vnic.is_primary,
        })
    return result

TOOL_MAP = {
    "list_instances": list_instances,
    "get_instance": get_instance,
    "get_vnic_attachments": get_vnic_attachments,
}