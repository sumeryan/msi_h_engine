"""
Powered by Renoir
Author: Igor Daniel G Goncalves - igor.goncalves@renoirgroup.com

Cliente da API Frappe para o projeto MSI
"""

import os
import json
from typing import Any, Optional
from ast import Dict
import requests
import log
from engine_logger import EngineLogger

class ArterisApi(EngineLogger):
    """
    Class for interacting with the Arteris API.
    Provides methods to fetch DocTypes and their fields.
    """

    def __init__(self):
        """
        Initializes the ArterisApi instance with the base URL and API token.

        Args:
            api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
            api_token (str): The authorization token in the format 'token key:secret'.
        """
        self.api_token = os.getenv("ARTERIS_API_TOKEN")
        self.api_base_url = f"{os.getenv('ARTERIS_API_BASE_URL')}"
        self.api_get_keys = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.engine.get_keys"
        self.api_get_contracts = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.engine.get_contracts"
        self.logger = log.get_logger("Engine - Update Frappe")

    def _call_post(self, url: str, measurement = None, body = None, params = None):
        """
        Realiza chamadas de POST para a API
        """
        resource_url = f"{self.api_base_url}/method/arteris_app.api.{url}"
        if not params:
            params = {}
        if measurement:
            params = {
                "measurement": measurement
            }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }
        try:

            if body:
                response = requests.post(resource_url, headers=headers, params=params, json=body, timeout=300)
            else:
                response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            self.log_error(f"Error: {e}:\n{e.response.text if e.response else ''}")
            return None

    def _call_get(self, url, params, body = None) -> Any:
        """
        Executa uma chamada GET na API
        """

        headers = {"Authorization": self.api_token}

        try:
            if body:
                response = requests.get(url, headers=headers, params=params, json=body, timeout=30)
            else:
                response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            self.log_error(f"Error fetching DocTypes from API: {e}\n{e.response.text if e.response else ''}")
            return None
        except json.JSONDecodeError as e:
            self.log_error(f"Error decoding DocTypes JSON response: {e}")
            return None

    def _post_update(self, doctype: str, fields: Dict, values: Dict, id: str):
        """
        Realiza chamadas de POST para a API, atualizando um doctype existente.
        """

        resource_url = f"{self.api_base_url}/method/arteris_app.api.engine.update_doctype"
        params = {}
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }
        body = {
            "doctype": doctype,
            "fields": fields,
            "parameters_values": values,
            "id": id,
        }

        try:
            response = requests.post(
                resource_url,
                headers=headers,
                params=params,
                json=body,
                timeout=300)
            # Raises HTTPError for 4xx/5xx responses
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            self.log_error(f"Error: {e}\n{e.response.text if e.response else ''}")
            return None

    def update(self, results: dict, formulas: dict):
        """
        Atualiza os registros de medição com base nos resultados das formulas
        """

        def get_formula(path: str, formulas: dict):
            """
            Recupera a formula correspondente ao caminho fornecido.
            """
            for formula in formulas['formulas']:
                if formula.get('path') == path:
                    return  formula.get('update').get('doctype'), formula.get('update').get('fieldname')
            return None, None

        updates = {}

        if results:
            for result in results:

                for path_result in result.get('results'):

                    if path_result.get('status') == 'error':
                        continue

                    doctype, field = get_formula(path_result.get('path'), formulas)

                    if not doctype or not field:
                        continue

                    _id = result.get('id')
                    if not _id in updates:
                        updates[_id] = {
                            "doctype": doctype,
                            "fields": [],
                            "values": []
                        }

                    updates[_id]['fields'].append(field)
                    updates[_id]['values'].append(path_result.get('result'))

            for __id, update in updates.items():
                self.log_info(f"Updating {update['doctype']}, {update['fields']} for ID {__id} with values: {update['values']}", indent=1)
                if len(update['fields']) == 0:
                    continue
                self._post_update(update['doctype'], update['fields'], update['values'], __id)

    def sumarize_measurement(self, measurement: str):
        self.log_info(f"Totalizando medição", indent=1)
        self._call_post('measurement.sumarize_measurement', measurement)

    def check_orphans_records(self, measurement: str):
        self.log_info(f"Verificando registros órfãos", indent=1)
        self._call_post('measurement.check_orphans_records', measurement)

    def update_measurement_records(self, measurement: str):
        self.log_info(f"Atualizando os registros de medição", indent=1)
        self._call_post('measurement.update_measurement_records', measurement)

    def update_hours_measurement_record(self, measurement: str):
        self.log_info(f"Atualizando os registros de horas da medição", indent=1)
        self._call_post('measurement.update_hours_measurement_record', measurement)

    def update_reidi_measurement_record(self, measurement: str):
        self.log_info(f"Calculando os valores de REIDI para a medição", indent=1)
        self._call_post('measurement.update_reidi_measurement_record', measurement)

    def apply_measurement_performance_conditions(self, measurement: str):
        self.log_info(f"Aplicando as condições de produtividade compensatoria para a medição", indent=1)
        self._call_post('measurement.apply_measurement_performance_conditions', measurement)

    def apply_measurement_items_factor(self, measurement: str):
        self.log_info(f"Aplicando condições de fator de produtividade para a medição", indent=1)
        self._call_post('measurement.apply_measurement_items_factor', measurement)        

    def create_measurement_items_balance(self, measurement: str):
        self.log_info(f"Criando registros de saldo de pagamento de itens contratuais para a medição", indent=1)
        self._call_post('measurement.create_measurement_items_balance', measurement)     

    def update_cities(self, measurement: str):
        self.log_info(f"Atualizando registro de cidades e rodovias", indent=1)
        self._call_post('measurement.update_cities', params = {"measurement": measurement})

    def update_measurement_productivity(self, measurement: str):
        self.log_info(f"Atualizando registros de produtividade compensatoria", indent=1)
        self._call_post('measurement.update_measurement_productivity', measurement)

    def create_measurement_sap_orders_records(self, measurement: str):
        self.log_info(f"Criando registros de pedidos SAP para a medição", indent=1)
        self._call_post('measurement.create_measurement_sap_orders_records', measurement)

    def update_sap_orders_balance(self):
        self.log_info(f"Atualizando saldo dos pedidos SAP", indent=1)
        self._call_post('measurement.update_sap_orders_balance', None)

    def get_arteris_doctypes(self, child: bool = False):
        """
        Fetches all DocTypes from the Arteris API that belong to the 'Arteris' module and are not Child Items.

        Args:
            api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
            api_token (str): The authorization token in the format 'token key:secret'.

        Returns:
            list or None: A list of dictionaries, where each dictionary represents a DocType
                        found (containing at least the 'name' key).
                        Returns None in case of an error in the request or JSON decoding.
        """
        doctype_url = f"{self.api_base_url}/resource/DocType"
        params = {
            "filters": json.dumps([
                ["module", "=", "Arteris"],
                ["istable", "=", "1"] if child else ["istable", "!=", "1"]
            ]),
            "limit_page_length": 0  
        }

        data = self._call_get(doctype_url, params)

        return data.get("data", [])

    def get_docfields_for_doctype(self, doctype_name):
        """
        Fetches DocFields (field metadata) for a specific DocType.

        Filters to exclude fields of type 'Section Break' and 'Column Break' and
        selects only 'fieldname', 'label', and 'fieldtype'.

        Args:
            api_base_url (str): The base URL of the resource API.
            api_token (str): The authorization token.
            doctype_name (str): The name of the DocType for which to fetch fields.
            child (bool, optional): Indicates if the DocType is a Child Item. Defaults to False.

        Returns:
            list or None: A list of dictionaries, where each dictionary represents a DocField
                        (containing 'fieldname', 'label', 'fieldtype').
                        Returns None in case of an error in the request or JSON decoding.
                        Returns an empty list if no fields are found after filtering.
        """

        docfield_url = f"{self.api_base_url}/resource/DocType/{doctype_name}"
        params = {
            "limit_page_length": 0  
        }

        data = self._call_get(docfield_url, params)

        return data.get("data", [])

    def get_keys_api(self, doctype_name: str, return_field: str, filters: Dict):
        """
        Fetches keys for a specific DocType from the Arteris API based on a filter.

        Args:
            doctype_name (str): The name of the DocType to fetch keys from (e.g., 'Asset').
            filter_name (str): The name of the filter field (e.g., 'status').
            filter_value (str): The value of the filter field (e.g., 'Active').

        Returns:
            list or None: A list of strings containing the key values of the DocType.
                        Returns None in case of an error in the request or JSON decoding.
        """
        resource_url = f"{self.api_get_keys}"
        params = {}
        body = {
            "doctype": doctype_name,
            "filters": filters,
            "return_field": return_field
        }

        data = self._call_get(resource_url, params, body)
        keys = [k[return_field] for k in data.get("message", [])]

        return keys

    def get_keys(self, doctype_name, filters=None):
        """
        Fetches the keys of a specific DocType from the Arteris API.
        
        Args:
            api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
            api_token (str): The authorization token in the format 'token key:secret'.
            doctype_name (str): The name of the DocType to fetch keys from (e.g., 'Asset').
            
        Returns:
            list or None: A list of strings containing the key values of the DocType.
                        Returns None in case of an error in the request or JSON decoding.
        """
        resource_url = f"{self.api_base_url}/resource/{doctype_name}"
        if filters:
            resource_url=f"{resource_url}?filters={filters}"
        
        params = {
            "limit_page_length": 0  
        }

        data = self._call_get(resource_url, params)
        keys = [item["name"] for item in data.get("data", [])]

        return keys

    def remove_properties_recursively(self, data, properties_to_remove):
        """
        Recursively removes specified properties from a JSON object.
        
        Args:
            data: The JSON object from which to remove properties.
            properties_to_remove: List of properties to be removed.
            
        Returns:
            The JSON object with the properties removed.
        """
        if isinstance(data, dict):
            # Removes properties from the current dictionary
            for prop in properties_to_remove:
                if prop in data:
                    del data[prop]
            
            # Recursively processes all dictionary values
            for key, value in list(data.items()):
                data[key] = self.remove_properties_recursively(value, properties_to_remove)
                
        elif isinstance(data, list):
            # Recursively processes all list items
            for i, item in enumerate(data):
                data[i] = self.remove_properties_recursively(item, properties_to_remove)
                
        return data

    def get_data_from_key(self, doctype_name, key):
        """
        Fetches data for a specific DocType from the Arteris API using a key.
        
        Args:
            api_base_url (str): The base URL of the resource API (e.g., 'https://host/api/resource').
            api_token (str): The authorization token in the format 'token key:secret'.
            doctype_name (str): The name of the DocType to fetch data from (e.g., 'Asset').
            key (str): The key of the DocType to fetch data for.
            
        Returns:
            A JSON object containing the DocType data or None in case of error.
            The following properties are removed from the returned JSON (including in nested objects):
            'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx'
        """
        resource_url = f"{self.api_base_url}/resource/{doctype_name}/{key}"
        # print("URL", resource_url)
        params = {
            "limit_page_length": 0  
        }
        headers = {"Authorization": self.api_token}

        data = self._call_get(resource_url, params, headers)

        if "data" in data:
            # print(f"Data for '{doctype_name}' with key '{key}' received successfully!")
            
            # Removes the specified properties recursively
            data_filtered = data["data"]
            properties_to_remove = [] #['owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'parentfield', 'parenttype', 'is_group']
            
            # Applies recursive property removal
            data_filtered = self.remove_properties_recursively(data_filtered, properties_to_remove)
            
            return data_filtered
        else:
            # print(f"No data found for '{doctype_name}' with key '{key}'!")
            return None

    def get_contracts(self):
        """
        Recupera os contratos para calculo
        """

        resource_url = f"{self.api_base_url}/method/arteris_app.api.engine.get_contracts"

        data = self._call_get(resource_url, params={})
    
        contracts = data.get('message', [])

        return contracts

    def write_errors(self, measurement, errors):
        """
        Grava os erros do motor
        """
        resource_url = f"engine.write_errors"
        params = {}
        body = {
            "measurement": measurement,
            "errors": errors
        }

        return self._call_post(resource_url, params, body)