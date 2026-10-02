#!/bin/bash
# Sobe o PostgreSQL local (so em 127.0.0.1) e depois a Evolution API.
set -e
export PATH="/usr/libexec/postgresql17:$PATH"

OPTS=/data/options.json
PGDATA=/data/postgres
PWFILE=/data/db_password

API_KEY=$(jq -r '.api_key // ""' "$OPTS")
if [ -z "$API_KEY" ] || [ ${#API_KEY} -lt 20 ]; then
    echo "[evolution] Defina 'api_key' nas opcoes do add-on (minimo 20 caracteres)." >&2
    exit 1
fi

# --- PostgreSQL ---------------------------------------------------------
mkdir -p /run/postgresql "$PGDATA"
chown postgres:postgres /run/postgresql "$PGDATA"
chmod 700 "$PGDATA"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "[evolution] Inicializando banco em $PGDATA"
    su-exec postgres initdb -D "$PGDATA" -U postgres -E UTF8 \
        --auth-local=trust --auth-host=scram-sha-256 >/dev/null
fi

if [ ! -s "$PWFILE" ]; then
    tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32 >"$PWFILE"
    chmod 600 "$PWFILE"
fi
DB_PW=$(cat "$PWFILE")

su-exec postgres pg_ctl -D "$PGDATA" -w -l /data/postgres.log \
    -o "-c listen_addresses=127.0.0.1" start

stop_pg() { su-exec postgres pg_ctl -D "$PGDATA" -m fast -w stop || true; }

psql_q() { su-exec postgres psql -U postgres -h /run/postgresql -tAc "$1"; }
if [ "$(psql_q "SELECT 1 FROM pg_roles WHERE rolname='evolution'")" != "1" ]; then
    psql_q "CREATE ROLE evolution LOGIN PASSWORD '$DB_PW'"
fi
if [ "$(psql_q "SELECT 1 FROM pg_database WHERE datname='evolution'")" != "1" ]; then
    psql_q "CREATE DATABASE evolution OWNER evolution"
fi

# --- Evolution API ------------------------------------------------------
export SERVER_TYPE=http
export SERVER_PORT=8080
export SERVER_URL=$(jq -r '.server_url' "$OPTS")
export AUTHENTICATION_API_KEY="$API_KEY"
export AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=false
export DEL_INSTANCE=false
export TELEMETRY_ENABLED=false
export LOG_LEVEL=$(jq -r '.log_level' "$OPTS")
export LOG_COLOR=false
export LOG_BAILEYS=error
export LANGUAGE=pt-BR
export CONFIG_SESSION_PHONE_CLIENT="Consultorio"
export CONFIG_SESSION_PHONE_NAME=Chrome

export DATABASE_PROVIDER=postgresql
export DATABASE_CONNECTION_URI="postgresql://evolution:${DB_PW}@127.0.0.1:5432/evolution?schema=evolution_api"
export DATABASE_CONNECTION_CLIENT_NAME=evolution_ha
export DATABASE_SAVE_DATA_INSTANCE=true
export DATABASE_SAVE_DATA_NEW_MESSAGE=true
export DATABASE_SAVE_MESSAGE_UPDATE=true
export DATABASE_SAVE_DATA_CONTACTS=true
export DATABASE_SAVE_DATA_CHATS=true
export DATABASE_SAVE_DATA_LABELS=true
# Historico antigo do aparelho: desligado por padrao (dados de pacientes)
export DATABASE_SAVE_DATA_HISTORIC=$(jq -r '.salvar_historico' "$OPTS")

export CACHE_REDIS_ENABLED=false
export CACHE_LOCAL_ENABLED=true

cd /evolution
. ./Docker/scripts/deploy_database.sh

node dist/main &
PID=$!
trap 'kill -TERM $PID 2>/dev/null; wait $PID; stop_pg; exit 0' TERM INT
set +e
wait $PID
RC=$?
stop_pg
exit $RC
