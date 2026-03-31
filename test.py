# coding: utf-8
# Copyright (c) 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

##########################################################################
# chat_demo.py
# Supports Python 3
##########################################################################
# Info:
# Get texts from LLM model for given prompts using OCI Generative AI Service.
##########################################################################
# Application Command line(no parameter needed)
# python chat_demo.py
##########################################################################
import oci

##################################################
# OCI CLIENT INITIALIZATION AND AUTHENTICATION
###################################################
CLIENT_CLASS_MAP = {
    'identity': oci.identity.IdentityClient,
    'devops': oci.devops.DevopsClient,
    'secrets': oci.secrets.SecretsClient,
    'virtual_network': oci.core.VirtualNetworkClient,
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

def get_signer():
    try:
        print("getting resource principal")
        return oci.auth.signers.get_resource_principals_signer() # When pipeline working.
    except EnvironmentError as e:
        print(e)
        print("getting user principal")
        return auth("DEFAULT") # When user testing.

def get_client(client_name, region=None):
    if region == None:
        region = "us-phoenix-1"
    if client_name not in CLIENT_CLASS_MAP:
        print(f"Unknown client {client_name}")
        raise RuntimeError('Unknown client %s' % client_name)
    try:
        print(client_name)
        client = CLIENT_CLASS_MAP[client_name](
            {'region': region}, signer=get_signer(), retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
    except oci.exceptions.ServiceError as e:
        print("Error requesting client: {e}")
    return client
# Setup basic variables
# Auth Config
# TODO: Please update config profile name and use the compartmentId that has policies grant permissions for using Generative AI Service
compartment_id = "ocid1.compartment.oc1..aaaaaaaastguw64nmxf33trvattya2ykrfamt5glt2e7mbkiadt3eh43ty5a"
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

# Service endpoint
endpoint = "https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com"

generative_ai_inference_client = get_client("generative_ai", region="us-ashburn-1")
# generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config=config, service_endpoint=endpoint, retry_strategy=oci.retry.NoneRetryStrategy(), timeout=(10,240))
chat_detail = oci.generative_ai_inference.models.ChatDetails()

content = oci.generative_ai_inference.models.TextContent()
content.text = "hello"
message = oci.generative_ai_inference.models.Message()
message.role = "USER"
message.content = [content]

chat_request = oci.generative_ai_inference.models.GenericChatRequest()
chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
chat_request.messages = [message]
chat_request.max_tokens = 6000
chat_request.temperature = 1
chat_request.frequency_penalty = 0
chat_request.presence_penalty = 0
chat_request.top_p = 0.95
chat_request.top_k = 1
chat_request.seed = None

chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="ocid1.generativeaimodel.oc1.iad.amaaaaaask7dceyargceyuaysrjzo2metq2rinavayxqmpu7tkm6mmfojcvq")
chat_detail.chat_request = chat_request
chat_detail.compartment_id = compartment_id

chat_response = generative_ai_inference_client.chat(chat_detail)

# Print result
print("**************************Chat Result**************************")
print(vars(chat_response))
