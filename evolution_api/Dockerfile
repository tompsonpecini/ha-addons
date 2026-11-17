ARG BUILD_FROM
FROM $BUILD_FROM

# A imagem da Evolution e node:24-alpine (Alpine 3.23)
RUN apk add --no-cache postgresql17 jq su-exec

COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Ack das stanzas <status> que a Baileys rc.9 ignora (instância "open" que para
# de receber). Ver patch-status.cjs. Falha o build se não achar a Baileys.
COPY patch-status.cjs /tmp/patch-status.cjs
RUN set -e; n=0; \
    for pj in $(find / -path /proc -prune -o -path '*/node_modules/baileys/package.json' -print); do \
      b=$(dirname "$pj"); \
      node /tmp/patch-status.cjs "$b"; \
      node --check "$b/lib/Socket/messages-recv.js"; \
      n=$((n+1)); \
    done; \
    [ "$n" -gt 0 ] || { echo 'Baileys não encontrada'; exit 1; }

ENTRYPOINT [ "/run.sh" ]
