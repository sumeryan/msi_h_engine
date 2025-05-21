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

# Configurações de ambiente
env_rabbit = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
env_db     = os.getenv("POSTGRES_URL", None)

app = FastAPI(title="Motor de Cálculo")

# Inicializa DB se presente
db = None
if env_db:
    db = Database(env_db)
    engine = create_engine(env_db)

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
        # Normaliza payload para motor
        if isinstance(raw_data, list):
            tree_data = {"data": raw_data}
        elif isinstance(raw_data, dict):
            tree_data = raw_data
        else:
            raise ValueError("Envie um objeto JSON ou uma lista de objetos.")

        # Define request_id
        if db:
            # usa fetch_val para retornar escalar
            request_id = await db.fetch_val(
                "INSERT INTO requests(payload) VALUES(CAST(:p AS JSONB)) RETURNING id",
                {"p": json.dumps(raw_data)}
            )
        else:
            request_id = str(uuid.uuid4())

        # Executa motor de cálculo
        extracted = parse_formulas(tree_data)
        processed = process_formula_variables(extracted, tree_data)
        raw_results = eval_formula(processed, extracted)
        clean = convert_numpy(raw_results)

        # Publica no RabbitMQ
        publish_to_queue(
            rabbit_url=env_rabbit,
            queue_name="engine_queue",
            message={"request_id": request_id, "payload": raw_data, "results": clean}
        )

        # Retorna resultados
        return {"results": clean}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
