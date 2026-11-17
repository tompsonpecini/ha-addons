# Changelog

## 1.0.2

- Corrige a instância que fica "open" mas para de receber mensagens. A Baileys 7.0.0-rc.9, que vem na Evolution 2.3.7, não confirma as stanzas `<status>` que o WhatsApp manda desde set/2026. O build aplica um ack para elas (`patch-status.cjs`) e falha se a versão da Baileys mudar. Ref.: evolution-foundation/evolution-api#2778, WhiskeySockets/Baileys#2858.

## 1.0.1

- Corrige a partida do PostgreSQL: o log ia para `/data`, sem permissão de escrita
  para o usuário `postgres`. Agora fica em `/data/pglog`, e o add-on mostra as
  últimas linhas desse log quando o banco não sobe.

## 1.0.0

- Primeira versão: Evolution API v2.3.7 com PostgreSQL 17 embutido.
- Redis desligado (cache local); telemetria desligada.
- Histórico antigo do aparelho não é importado, a menos que `salvar_historico` seja ligado.
