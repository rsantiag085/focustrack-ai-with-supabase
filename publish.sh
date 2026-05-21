#!/bin/bash
set -e

# ── Configuração ──────────────────────────────────────────────────────────────
DO_USER="root"
DO_HOST="${1:-}"    # uso: bash publish.sh <IP_DO_DROPLET>
APP_DIR="/opt/focustrack"
# ─────────────────────────────────────────────────────────────────────────────

if [[ -z "$DO_HOST" ]]; then
    echo "Uso: bash publish.sh <IP_DO_DROPLET>"
    echo "Exemplo: bash publish.sh 123.45.67.89"
    exit 1
fi

echo "==> Fazendo push do código para o GitHub..."
git push origin main

echo "==> Conectando ao Droplet $DO_HOST..."
ssh "$DO_USER@$DO_HOST" bash <<EOF
    set -e

    if ! command -v docker &>/dev/null; then
        echo "Instalando Docker..."
        curl -fsSL https://get.docker.com | sh
    fi

    if [ ! -d "$APP_DIR" ]; then
        git clone git@github.com:rsantiag085/focustrack-ai-with-supabase.git $APP_DIR
    fi

    cd $APP_DIR
    git pull origin main

    if [ ! -f ".env" ]; then
        echo "AVISO: arquivo .env não encontrado em $APP_DIR no servidor."
        echo "Crie o .env antes de continuar. Abortando."
        exit 1
    fi

    docker compose down --remove-orphans
    docker compose build --no-cache
    docker compose up -d

    echo "Deploy concluído. Containers rodando:"
    docker compose ps
EOF

echo ""
echo "✅ FocusTrack AI publicado em http://$DO_HOST"
