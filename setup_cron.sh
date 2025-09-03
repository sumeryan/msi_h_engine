#!/bin/bash

# Script para configurar execução automática diária do H Engine via cron
# Configura para execução todos os dias às 01:00

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=== CONFIGURANDO CRON PARA H ENGINE ==="

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_h_engine.sh"

# Verificar se o script existe
if [ ! -f "$RUN_SCRIPT" ]; then
    print_error "Script run_h_engine.sh não encontrado em: $RUN_SCRIPT"
    exit 1
fi

# Verificar se o script é executável
if [ ! -x "$RUN_SCRIPT" ]; then
    print_warning "Tornando run_h_engine.sh executável..."
    chmod +x "$RUN_SCRIPT"
fi

# Configuração do cron job
CRON_TIME="0 1 * * *"  # Todos os dias às 01:00
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/cron_h_engine.log"

# Criar diretório de logs se não existir
if [ ! -d "$LOG_DIR" ]; then
    print_info "Criando diretório de logs: $LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# Cron job completo com redirecionamento de logs
CRON_JOB="$CRON_TIME $RUN_SCRIPT >> $LOG_FILE 2>&1"

print_info "Configuração do cron job:"
print_info "Horário: Todos os dias às 01:00"
print_info "Script: $RUN_SCRIPT"
print_info "Logs: $LOG_FILE"

# Verificar se o cron job já existe
if crontab -l 2>/dev/null | grep -q "$RUN_SCRIPT"; then
    print_warning "Cron job já existe para este script"
    print_info "Removendo configuração anterior..."
    crontab -l 2>/dev/null | grep -v "$RUN_SCRIPT" | crontab -
fi

# Adicionar novo cron job
print_info "Adicionando novo cron job..."
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# Verificar se foi adicionado corretamente
if crontab -l 2>/dev/null | grep -q "$RUN_SCRIPT"; then
    print_info "Cron job configurado com sucesso!"
    echo ""
    print_info "=== CONFIGURAÇÃO ATUAL DO CRON ==="
    crontab -l | grep "$RUN_SCRIPT"
    echo ""
    print_info "O H Engine será executado todos os dias às 01:00"
    print_info "Logs serão salvos em: $LOG_FILE"
    print_info "Para remover a configuração, execute: ./remove_cron.sh"
else
    print_error "Erro ao configurar cron job"
    exit 1
fi

print_info "=== CONFIGURAÇÃO CONCLUÍDA ==="