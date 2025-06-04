#!/bin/bash

echo "🚀 Iniciando containers em modo debug..."

# Para e remove containers antigos
docker-compose -f docker-compose.debug.yml down

# Reconstrói a imagem para garantir que tem as últimas mudanças
docker-compose -f docker-compose.debug.yml build --no-cache api

# Inicia os containers
docker-compose -f docker-compose.debug.yml up -d

# Aguarda um pouco para os containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 3

# Verifica se a API está rodando
if docker ps | grep -q engine_api_debug; then
    echo "✅ Containers iniciados com sucesso!"
else
    echo "❌ Erro ao iniciar containers. Verifique os logs."
    exit 1
fi

echo ""
echo "📍 Portas disponíveis:"
echo "   - API: http://localhost:8081"
echo "   - Debug API: localhost:5678"
echo "   - RabbitMQ: http://localhost:15672"
echo "   - PgAdmin: http://localhost:5050"
echo ""
echo "🔧 Para depurar no VS Code:"
echo "   1. Coloque breakpoints no código (ex: main.py linha 50)"
echo "   2. Abra Run and Debug (Ctrl+Shift+D)"
echo "   3. Selecione 'Docker: Attach to API'"
echo "   4. Clique em Start Debugging (F5)"
echo "   5. Faça uma requisição para http://localhost:8081/evaluate"
echo ""
echo "📋 Comandos úteis:"
echo "   - Logs da API: docker-compose -f docker-compose.debug.yml logs -f api"
echo "   - Parar tudo: docker-compose -f docker-compose.debug.yml down"
echo "   - Reiniciar API: docker-compose -f docker-compose.debug.yml restart api"