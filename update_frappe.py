
import requests
import log
import os
from engine_logger import EngineLogger

class UpdateFrappe(EngineLogger):
    def __init__(self, results: dict, formulas: dict):
        self.api_base_url = os.getenv("ARTERIS_API_URL_UPDATE_DOCKTYPE")
        self.api_token = os.getenv("ARTERIS_API_TOKEN")
        self.results = results
        self.formulas = formulas
        self.logger = log.get_logger("Engine - Update Frappe")

    def _post(self, doctype: str, field: str, id: str, value: any):

        resource_url = f"{self.api_base_url}"
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
        
    def _get_formula(self, path: str):
        for formula in self.formulas['formulas']:
            if formula.get('path') == path:
                return  formula.get('update').get('doctype'), formula.get('update').get('fieldname')

    def update(self):

        for result in self.results:
            id = result.get('id')

            for path_result in result.get('results'):
                doctype, field = self._get_formula(path_result.get('path'))
                try:
                    self.log_info(f"Updating {doctype} {field} for ID {id} with value: {path_result.get('result')}", indent=1)
                    self._post(doctype, field, id, path_result.get('result'))
                except Exception as e:
                    self.log_error(f"Failed to update {doctype} {field} for ID {id}: {e}")
                    continue

        # sum_measurement_orders


