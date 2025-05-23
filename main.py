import os
import json
import uuid
from fastapi import FastAPI, HTTPException, Body
from typing import Any
import numpy as np
from databases import Database
from sqlalchemy import create_engine
from publisher import publish_to_queue

from app.engine_parser import parse_formulas
from app.engine_pre_processor import process_formula_variables
from app.engine_eval import eval_formula

app = FastAPI(title="Motor de Cálculo")

# Ambiente
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
DB_URL     = os.getenv("POSTGRES_URL", None)

# Configura DB opcional
db = None
if DB_URL:
    db = Database(DB_URL)
    engine = create_engine(DB_URL)

    @app.on_event("startup")
    async def startup():
        await db.connect()

    @app.on_event("shutdown")
    async def shutdown():
        await db.disconnect()


def convert_numpy(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, list):
        return [convert_numpy(v) for v in obj]
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    return obj


@app.post("/evaluate")
async def evaluate_endpoint(raw_data: Any = Body(...)):
    try:
        # 1) normaliza payload
        if isinstance(raw_data, list):
            tree_data = {"data": raw_data}
        elif isinstance(raw_data, dict):
            tree_data = raw_data
        else:
            raise ValueError("Envie um JSON ou lista")

        # 2) salva request_id
        if db:
            request_id = await db.fetch_val(
                "INSERT INTO requests(payload) VALUES(CAST(:p AS JSONB)) RETURNING id",
                {"p": json.dumps(raw_data)}
            )
        else:
            request_id = str(uuid.uuid4())

        # 3) executa o motor
        extracted   = parse_formulas(tree_data)
        processed   = process_formula_variables(extracted, tree_data)
        raw_results = eval_formula(processed, extracted)
        clean       = convert_numpy(raw_results)

        # opcional: atualiza tree_data com resultados
        for idx, node in enumerate(tree_data.get("data", [])):
            node["result"] = clean[idx]

        # 4) publica na fila do motor
        publish_to_queue(
            rabbit_url = RABBIT_URL,
            queue_name = "engine_queue",
            message    = {
                "request_id": request_id,
                "payload":    tree_data,
                "results":    clean
            }
        )

        # 5) publica na fila de carga
        publish_to_queue(
            rabbit_url = RABBIT_URL,
            queue_name = "carga_queue",
            message    = {
                "request_id": request_id,
                "results":    clean
            }
        )

        # 6) retorna imediatamente
        return {"results": clean}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
