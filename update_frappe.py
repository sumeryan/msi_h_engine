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

    def _call_post(self, url: str, contract):
        resource_url = f"{self.api_base_url}/method/arteris_app.api.{url}"
        params = {}
        if contract:
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

        self.log_info(f"Totalizando medição", indent=1)
        self._call_post('measurement.update_contract_productivity', contract)

    def update_contract_records(self, contract: str):

        self.log_info(f"Atualizando os registros de medição", indent=1)
        self._call_post('measurement.update_contract_measurement_records', contract)

    def update_hours_contract_record(self, contract: str):

        self.log_info(f"Atualizando os registros de horas da medição", indent=1)
        self._call_post('measurement.update_hours_contract_records', contract)

    def update_reidi_contract_records(self, contract: str):

        self.log_info(f"Calculandop os valores de REIDI para a medição", indent=1)
        self._call_post('measurement.update_reidi_contract_records', contract)

    def apply_contract_performance_conditions(self, contract: str):

        self.log_info(f"Aplicando as condições de produtividade compensatoria para a medição", indent=1)
        self._call_post('apply_contract_performance_conditions', contract)

    def apply_contract_items_factor(self, contract: str):

        self.log_info(f"Aplicando condições de fator de produtividade para a medição", indent=1)
        self._call_post('measurement.apply_contract_items_factor', contract)        

    def create_contract_items_balance(self, contract: str):

        self.log_info(f"Criando registros de saldo de pagamento de itens contratuais para a medição", indent=1)
        self._call_post('measurement.create_contract_items_balance', contract)     

    def update_cities(self):
        self.log_info(f"Atualizando registro de cidades e rodovias", indent=1)
        self._call_post('measurement.update_cities', None)

    def update_contract_productivity(self, contract: str):

        self.log_info(f"Atualizando registros de produtividade compensatoria", indent=1)
        self._call_post('measurement.update_contract_productivity', contract)

    def create_contract_sap_orders_records(self, contract: str):

        self.log_info(f"Criando registros de pedidos SAP para a medição", indent=1)
        self._call_post('measurement.create_contract_sap_orders_records', contract)

    def update_sap_orders_balance(self, contract: str):

        self.log_info(f"Atualizando saldo dos pedidos SAP", indent=1)
        self._call_post('measurement.update_sap_orders_balance')
