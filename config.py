import oci, os

# --- OCI auth (config file profile) ---
OCI_CONFIG_FILE = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
OCI_PROFILE = os.getenv("OCI_PROFILE", "DEFAULT")
COMPARTMENT_OCID = os.getenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..xxxxxxxx") # root or specific

# --- OCI Generative AI ---
GENAI_ENDPOINT = "https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com"
GENAI_MODEL_ID = "ocid1.generativeaimodel.oc1.iad.amaaaaaask7dceyargceyuaysrjzo2metq2rinavayxqmpu7tkm6mmfojcvq" # or meta.llama-3-...
# GENAI_MODEL_ID = "ocid1.generativeaimodel.oc1.iad.amaaaaaask7dceyaeo4ehrn25guuats5s45hnvswlhxo6riop275l2bkr2vq" # or meta.llama-3-...
GENAI_MAX_TOKENS = 2048


class OciHelper:
    ###################################################
    # OCI CLIENT INITIALIZATION AND AUTHENTICATION
    ###################################################
    CLIENT_CLASS_MAP = {
        'identity': oci.identity.IdentityClient,
        'devops': oci.devops.DevopsClient,
        'secrets': oci.secrets.SecretsClient,
        'virtual_network': oci.core.VirtualNetworkClient,
        'compute': oci.core.ComputeClient,             
        'generative_ai': oci.generative_ai_inference.GenerativeAiInferenceClient
    }

    ###################################################
    # REGION MAPPING DICTIONARY
    ###################################################
    REGIONS = {
        "iad": "us-ashburn-1",
        "ord": "us-chicago-1",
        "auh": "me-abudhabi-1",
        "dxb": "me-dubai-1",
        "jed": "me-jeddah-1",
        "phx": "us-phoenix-1",
        "yyz": "ca-toronto-1",
        "yul": "ca-montreal-1",
        "mel": "ap-melbourne-1",
        "syd": "ap-sydney-1",
        "fra": "eu-frankfurt-1",
        "lhr": "uk-london-1",
        "cwl": "uk-cardiff-1",
        "mad": "eu-madrid-1",
        "ruh": "me-riyadh-1",
        "sto": "eu-stockholm-1",
        "gru": "sa-saopaulo-1",
        "vcp": "sa-vinhedo-1",
        "cdg": "eu-paris-1",
        "ams": "eu-amsterdam-1",
        "lfi": "us-langley-1",  
        "luf": "us-luke-1",     
        "str": "eu-frankfurt-2",  
        "vll": "eu-madrid-2",
        "drz": "us-shawnee-1"     
    }
    
    @staticmethod
    def auth(profile):
        """
        Sets up OCI SecurityTokenSigner authentication using a local config file.
        """
        if profile == "DEFAULT":
            config = oci.config.from_file()
        else:
            config = oci.config.from_file(profile_name=profile)
        token_file = config['security_token_file']
        with open(token_file, 'r') as f:
            token = f.read()
        private_key = oci.signer.load_private_key_from_file(config['key_file'])
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        return signer

    @staticmethod
    def get_signer():
        try:
            print("getting resource principal")
            return oci.auth.signers.get_resource_principals_signer() # When pipeline working.
        except EnvironmentError as e:
            print(e)
            print("getting user principal")
            return OciHelper.auth("DEFAULT") # When user testing.

    @staticmethod
    def get_client(client_name, region=None):
        if region == None:
            region = "us-ashburn-1"
        if client_name not in OciHelper.CLIENT_CLASS_MAP:
            print(f"Unknown client {client_name}")
            raise RuntimeError('Unknown client %s' % client_name)
        try:
            print(client_name)
            client = OciHelper.CLIENT_CLASS_MAP[client_name](
                {'region': region}, signer=OciHelper.get_signer(), retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        except oci.exceptions.ServiceError as e:
            print("Error requesting client: {e}")
        return client
    

def get_oci_config():
    cfg = oci.config.from_file(OCI_CONFIG_FILE, OCI_PROFILE)
    oci.config.validate_config(cfg)   # raises immediately if key/tenancy missing
    return cfg