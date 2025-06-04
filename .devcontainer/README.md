# Dev Container Setup

Este repositório inclui uma configuração completa de Dev Container para desenvolvimento do Hierarchical Engine.

## Funcionalidades

- **Container Python 3.11** com todas as dependências instaladas
- **Debugger configurado** com debugpy na porta 5678
- **Auto-reload** para desenvolvimento ágil
- **Extensões VS Code** pré-configuradas (Python, Pylance, Black, Ruff)
- **Serviços de apoio**: PostgreSQL, RabbitMQ, pgAdmin

## Estrutura

- `devcontainer.json` - Configuração principal do Dev Container
- `docker-compose.devcontainer.yml` - Override para desenvolvimento
- `validate_setup.sh` - Script de validação da configuração
- `README.md` - Este arquivo

## Como usar

1. **Instale a extensão Dev Containers no VS Code**
   - Abra o VS Code
   - Vá em Extensions (Ctrl+Shift+X)
   - Procure por "Dev Containers"
   - Instale a extensão da Microsoft

2. **Abra o projeto no container**
   - Abra o VS Code na pasta do projeto
   - Pressione `Ctrl+Shift+P` (ou `Cmd+Shift+P` no Mac)
   - Digite "Dev Containers: Reopen in Container"
   - Aguarde o container ser criado (primeira vez demora mais)

3. **Desenvolvimento**
   - O VS Code abrirá DENTRO do container
   - Todas as dependências estarão instaladas
   - Use o terminal integrado para executar comandos

## Serviços disponíveis

- **API**: http://localhost:8081
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **pgAdmin**: http://localhost:5050
- **PostgreSQL**: localhost:5432
- **Debug Port**: localhost:5678

## Comandos úteis

### Iniciar API:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8081
```

### Iniciar API com debug:
```bash
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn main:app --reload --host 0.0.0.0 --port 8081
```

### Rodar testes:
```bash
python -m pytest
```

### Validar configuração:
```bash
/app/.devcontainer/validate_setup.sh
```

### Instalar nova dependência:
```bash
pip install <package>
pip freeze > requirements.txt
```

## Troubleshooting

Se o container não iniciar:

1. Verifique se o Docker está rodando
2. Execute `docker-compose down` para limpar containers antigos
3. Tente reconstruir o container: "Dev Containers: Rebuild Container"

### Problemas comuns:

**Container sai imediatamente:**
- Verifique se não há conflitos de porta
- O container deve usar o comando `while sleep 1000; do :; done` para manter-se ativo

**Debugger não conecta:**
- Verifique se a porta 5678 está disponível
- Use o comando de debug fornecido acima

**Volumes não funcionam:**
- Certifique-se de que o Docker tem permissão para acessar o diretório do projeto