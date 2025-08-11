from ast import Dict
import requests
import log
import os
from engine_logger import EngineLogger

class UpdateFrappe(EngineLogger):
    def __init__(self):
        self.api_token = os.getenv("ARTERIS_API_TOKEN")
        self.api_base_url = os.getenv("ARTERIS_API_BASE_URL")
        self.logger = log.get_logger("Engine - Update Frappe")

    def _update_measurement_records(self, contract: str):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.update_contract_measurement_records"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def _update_hours_measurement_records(self, contract: str):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.update_hours_contract_records"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            

    def _update_reidi_measurement_records(self, contract: str):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.update_reidi_contract_records"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            
        
    def _apply_contract_performance_conditions(self, contract: str):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.apply_contract_performance_conditions"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            
        
    def _apply_contract_items_factor(self, contract: str):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.apply_contract_items_factor"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            
         
    def _create_contract_items_balance(self, contract: str):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.create_contract_items_balance"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            

    def _update_cities(self):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.update_cities"
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            

    def _sumarize(self, contract):

        resource_url = f"{self.api_base_url}/method/arteris_app.api.measurement.sumarize_contract_measurements?contract={contract}"
        params = {}
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def _post(self, doctype: str, fields: Dict, values: Dict, id: str):

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

            response = requests.post(resource_url, headers=headers, params=params, json=body, timeout=300)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
        
    def _get_formula(self, path: str, formulas: dict):
        for formula in formulas['formulas']:
            if formula.get('path') == path:
                return  formula.get('update').get('doctype'), formula.get('update').get('fieldname')
        
        return None, None

    def update(self, results: dict = None, formulas: dict = None):

        updates = {}

        for result in results:

            for path_result in result.get('results'):

                if path_result.get('status') == 'error':
                    continue

                doctype, field = self._get_formula(path_result.get('path'), formulas)

                if not doctype or not field:
                    continue

                id = result.get('id')
                if not id in updates:
                    updates[id] = {
                        "doctype": doctype,
                        "fields": [],
                        "values": []
                    }

                updates[id]['fields'].append(field)
                updates[id]['values'].append(path_result.get('result'))

        for id, update in updates.items():
            self.log_info(f"Updating {update['doctype']}, {update['fields']} for ID {id} with values: {update['values']}", indent=1)
            if len(update['fields']) == 0:
                continue
            self._post(update['doctype'], update['fields'], update['values'], id)

    def sumarize(self, contract):

        self.log_info(f"Sumarizing values", indent=1)
        self._sumarize(contract)

    def update_contract_records(self, contract: str):

        self.log_info(f"Uodating measurement records", indent=1)
        self._update_measurement_records(contract)

    def update_hours_contract_record(self, contract: str):

        self.log_info(f"Updating measurement hours records", indent=1)
        self._update_hours_measurement_records(contract)

    def update_reidi_contract_records(self, contract: str):

        self.log_info(f"Updating measurement REIDI records", indent=1)
        self._update_reidi_measurement_records(contract)

    def apply_contract_performance_conditions(self, contract: str):

        self.log_info(f"Apply contract performance conditions", indent=1)
        self._apply_contract_performance_conditions(contract)

    def apply_contract_items_factor(self, contract: str):

        self.log_info(f"Apply contract performance conditions", indent=1)
        self._apply_contract_items_factor(contract)        

    def create_contract_items_balance(self, contract: str):

        self.log_info(f"Apply contract performance conditions", indent=1)
        self._create_contract_items_balance(contract)     

    def update_cities(self):
        self.log_info(f"Updating cities and highways", indent=1)
        self._update_cities()
