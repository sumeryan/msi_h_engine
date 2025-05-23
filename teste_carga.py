#!/usr/bin/env python3
import sys
import json
import requests
import pandas as pd
from urllib.parse import quote

def main():
    # 1) Lê todo stdin e faz parse JSON
    raw_input = sys.stdin.read()
    if not raw_input:
        print("Nenhum dado recebido via stdin", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw_input)
    # espera uma chave "results" no JSON de entrada
    if "results" not in data:
        print("JSON inválido: falta campo 'results'", file=sys.stderr)
        sys.exit(1)

    results = data["results"]

    # 2) Monta a lista de requisições PUT
    BASE = "https://arteris.meb.services/api/resource"
    planned = []
    for entry in results:
        entity_id = entry.get("entity_id")
        for fr in entry.get("formula_results", []):
            if fr.get("status") == "success" and "update" in fr:
                doctype   = fr["update"]["doctype"]
                fieldname = fr["update"]["fieldname"]
                value     = fr["result"]
                url       = f"{BASE}/{quote(doctype, safe='')}/{entity_id}"
                payload   = json.dumps({fieldname: value}, ensure_ascii=False)
                planned.append({"url": url, "payload": payload})

    # 3) Salva preview em CSV
    if planned:
        df_preview = pd.DataFrame(planned)
        df_preview.to_csv("planned_requests.csv", index=False, encoding="utf-8-sig")
        print("Preview salvo em planned_requests.csv")
    else:
        print("Nenhuma requisição planejada (lista vazia)")

    # 4) Configura cabeçalhos da API
    HEADERS = {
        'Authorization': 'token be2ff702de81b65:ba84415a14e57fd',
        'Content-Type': 'application/json'
    }

    # 5) Executa as requisições PUT e registra os resultados
    results_log = []
    for req in planned:
        try:
            resp = requests.put(req["url"], headers=HEADERS, data=req["payload"])
            results_log.append({
                "url": req["url"],
                "payload": req["payload"],
                "status_code": resp.status_code,
                "response_text": resp.text
            })
            print(f"[{resp.status_code}] {req['url']}")
        except Exception as e:
            results_log.append({
                "url": req["url"],
                "payload": req["payload"],
                "status_code": "error",
                "response_text": str(e)
            })
            print(f"[ERROR] {req['url']}  → {e}")

    # 6) Salva log completo em CSV
    if results_log:
        df_log = pd.DataFrame(results_log)
        df_log.to_csv("put_requests_log.csv", index=False, encoding="utf-8-sig")
        print("Log completo salvo em put_requests_log.csv")
    else:
        print("Nenhum log de requisição para salvar")

if __name__ == "__main__":
    main()
