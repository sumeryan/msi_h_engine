#!/usr/bin/env python
"""Script para iniciar o servidor com debugpy habilitado"""

import os
import sys

# Adiciona o diretório do projeto ao PYTHONPATH
sys.path.insert(0, '/app')

# Configura debugpy
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("⏳ Aguardando debugger se conectar na porta 5678...")
debugpy.wait_for_client()
print("✅ Debugger conectado!")

# Inicia o servidor
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=False)