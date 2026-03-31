# debug_auth.py
# import oci
# from config import get_oci_config, GENAI_ENDPOINT, COMPARTMENT_OCID

# cfg = get_oci_config()
# print("Tenancy:  ", cfg["tenancy"])
# print("Region:   ", cfg["region"])
# print("Key file: ", cfg["key_file"])
# print("Endpoint: ", GENAI_ENDPOINT)
# print("Compartment:", COMPARTMENT_OCID)

# # Try a simple identity call to confirm auth works at all
# identity = oci.identity.IdentityClient(config=cfg)
# tenancy = identity.get_tenancy(cfg["tenancy"]).data
# print("Auth OK — tenancy name:", tenancy.name)

from config import OciHelper, COMPARTMENT_OCID

print("Testing auth via OciHelper...")
client = OciHelper.get_client("identity", region="us-ashburn-1")

signer = OciHelper.get_signer()
# Extract tenancy from the signer's token
import oci
cfg = oci.config.from_file()
tenancy_id = cfg["tenancy"]

tenancy = client.get_tenancy(tenancy_id).data
print("Auth OK — tenancy name:", tenancy.name)
print("Compartment:", COMPARTMENT_OCID)