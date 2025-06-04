FROM python:3.11-slim

# Defina seu workdir
WORKDIR /app

# Copie apenas o requirements para cachear o pip install
COPY requirements.txt ./

# Instale todas as deps e debugpy
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install debugpy

# Agora copie o resto do código
COPY . .

# Exponha as portas
EXPOSE 8000 5678

# Por padrão, o container sobe a API. O worker usará override via docker-compose.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
