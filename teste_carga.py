import json
from urllib.parse import quote
import pandas as pd

# Carrega os arquivos JSON
with open('tree_data.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

with open('result.json', 'r', encoding='utf-8') as f:
    results = json.load(f)["results"]

# Função para extrair mapeamento de path -> (doctype, fieldname)
mapping = {}
def scan(node):
    if isinstance(node, dict):
        if "update" in node and "path" in node:
            mapping[node["path"]] = (
                node["update"]["doctype"],
                node["update"]["fieldname"]
            )
        for v in node.values():
            scan(v)
    elif isinstance(node, list):
        for item in node:
            scan(item)

for ref in tree.get("data", []):
    scan(ref)

# Monta lista de requisições PUT previstas
# Monta a lista de requisições PUT previstas
BASE = "https://arteris.meb.services/api/resource"
planned = []
for entry in results:
    entity_id = entry["entity_id"]
    for fr in entry.get("formula_results", []):
        path = fr["formula_path"]
        if fr["status"] == "success" and path in mapping:
            doctype, field = mapping[path]
            url = f"{BASE}/{quote(doctype, safe='')}/{entity_id}"
            payload = {field: fr["result"]}
            planned.append({
                "url": url,
                "payload": json.dumps(payload, ensure_ascii=False)
            })

# Converte para DataFrame
df = pd.DataFrame(planned)

# Salva em arquivo CSV
output_path = 'planned_requests.csv'
df.to_csv(output_path, index=False, encoding='utf-8-sig')