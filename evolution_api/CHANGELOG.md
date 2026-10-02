# Changelog

## 1.0.1

- Corrige a partida do PostgreSQL: o log ia para `/data`, sem permissão de escrita
  para o usuário `postgres`. Agora fica em `/data/pglog`, e o add-on mostra as
  últimas linhas desse log quando o banco não sobe.

## 1.0.0

- Primeira versão: Evolution API v2.3.7 com PostgreSQL 17 embutido.
- Redis desligado (cache local); telemetria desligada.
- Histórico antigo do aparelho não é importado, a menos que `salvar_historico` seja ligado.
