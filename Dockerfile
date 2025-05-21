FROM python:3.11-slim

# Defina seu workdir
WORKDIR /app

# Copie apenas o requirements para cachear o pip install
COPY requirements.txt ./

# Instale todas as deps
RUN pip install --no-cache-dir -r requirements.txt

# Agora copie o resto do código
COPY . .

# Exponha a porta (opcional)
EXPOSE 8000

# Por padrão, o container sobe a API. O worker usará override via docker-compose.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
