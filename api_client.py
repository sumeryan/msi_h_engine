"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

API Client Data module for fetching entity data from the Arteris API.
This module provides functions to retrieve entity keys and data from the Arteris API.
"""

import requests
import json
import os
from typing import Literal
import urllib3
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Desabilitar avisos de SSL se necessário
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def custom_url(api_base_url, api_token, method: Literal["GET", "POST", "PUT", "DELETE"] = "GET", body = None, timeout = 30):

    resource_url = f"{api_base_url}"
    params = {}
    headers = {
        "Authorization": api_token,
        "Content-Type": "application/json",
    }

    # Configuração SSL
    verify_ssl = True
    cert_path = None
    
    # Debug: verificar variável de ambiente
    ssl_disable = os.getenv("DISABLE_SSL_VERIFY", "false").lower()
    print(f"Debug: DISABLE_SSL_VERIFY = {ssl_disable}")
    
    # Verificar configuração SSL (prioridade: DISABLE_SSL_VERIFY)
    if ssl_disable == "true":
        verify_ssl = False
        print("Warning: SSL verification disabled")
    elif os.path.exists("../ssl-certs/arteris_com_br.crt"):
        cert_path = "../ssl-certs/arteris_com_br.crt"
        verify_ssl = cert_path
        print(f"Using custom certificate: {cert_path}")
    else:
        print("Using default SSL verification")

    try:

        if body:
            if not isinstance(body, dict):
                body = json.loads(body)

        if method == "GET":
            response = requests.get(resource_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl)
        elif method == "POST":
            if body:
                response = requests.post(resource_url, headers=headers, params=params, json=body, timeout=timeout, verify=verify_ssl)
            else:
                response = requests.post(resource_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl)
        elif method == "PUT":
            if body:
                response = requests.put(resource_url, headers=headers, params=params, json=body, timeout=timeout, verify=verify_ssl)
            else:
                response = requests.put(resource_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl)
        elif method == "DELETE":
            response = requests.delete(resource_url, headers=headers, params=params, timeout=timeout, verify=verify_ssl)

        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    