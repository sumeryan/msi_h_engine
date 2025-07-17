import requests
import log
import os
from engine_logger import EngineLogger

class UpdateFrappe(EngineLogger):
    def __init__(self):
        self.api_token = os.getenv("ARTERIS_API_TOKEN")
        self.api_update_doctype = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.engine.update_doctype"
        self.api_sumarize = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.measurement.sumarize_measurements"
        self.api_update_measurement_records = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.measurement.update_contract_measurement_records"
        self.api_update_hours_measurement_records = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.measurement.update_contract_hours_measurement_records"
        self.api_update_reidi_measurement_records = f"{os.getenv('ARTERIS_API_BASE_URL')}/method/arteris_app.api.measurement.update_reidi_measurement_records"
        self.logger = log.get_logger("Engine - Update Frappe")

    def _update_measurement_records(self, contract: str):

        resource_url = f"{self.api_update_measurement_records}"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def _update_hours_measurement_records(self, contract: str):

        resource_url = f"{self.api_update_hours_measurement_records}"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            

    def _update_reidi_measurement_records(self, contract: str):

        resource_url = f"{self.api_update_reidi_measurement_records}"
        params = {
            "contract": contract
        }
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None            
        
    def _sumarize(self):

        resource_url = f"{self.api_sumarize}"
        params = {}
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, timeout=30)
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def _post(self, doctype: str, field: str, id: str, value: any):

        resource_url = f"{self.api_update_doctype}"
        params = {}
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }

        body = {
            "doctype": doctype,
            "field": field,
            "id": id,
            "value": value
        }

        try:

            response = requests.post(resource_url, headers=headers, params=params, json=body, timeout=30)
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

        for result in results:
            id = result.get('id')

            for path_result in result.get('results'):
                if path_result.get('status') == 'error':
                    continue
                doctype, field = self._get_formula(path_result.get('path'), formulas)
                if not doctype or not field:
                    continue
                try:
                    self.log_info(f"Updating {doctype} {field} for ID {id} with value: {path_result.get('result')}", indent=1)
                    self._post(doctype, field, id, path_result.get('result'))
                except Exception as e:
                    self.log_error(f"Failed to update {doctype} {field} for ID {id}: {e}")
                    continue

    def sumarize(self):

        self.log_info(f"Sumarizing values", indent=1)
        self._sumarize()

    def update_measurement_records(self, contract: str):

        self.log_info(f"Uodating measurement records", indent=1)
        self._update_measurement_records(contract)

    def update_hours_measurement_record(self, contract: str):

        self.log_info(f"Updating measurement hours records", indent=1)
        self._update_hours_measurement_records(contract)

    def update_reidi_measurement_records(self, contract: str):

        self.log_info(f"Updating measurement REIDI records", indent=1)
        self._update_reidi_measurement_records(contract)
