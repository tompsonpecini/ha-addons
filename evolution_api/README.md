# Evolution API

[Evolution API](https://github.com/EvolutionAPI/evolution-api) v2 empacotada
como add-on, com PostgreSQL embutido. Conecta um número de WhatsApp por QR code
e expõe uma API HTTP e webhooks — pensada para ser usada pelo n8n.

> A Evolution usa o protocolo do WhatsApp Web; não é a API oficial da Meta.
> O número pode ser bloqueado pelo WhatsApp. Use um número dedicado.

## Configuração

| Opção | Descrição |
|---|---|
| `api_key` | Chave global da API (mínimo 20 caracteres). Vai no header `apikey`. |
| `server_url` | Endereço pelo qual a API é alcançada (usado em links de mídia). |
| `log_level` | Níveis de log, separados por vírgula. |
| `salvar_historico` | Importa o histórico antigo de conversas do aparelho ao conectar. |

## Uso

1. Defina a `api_key` e inicie o add-on.
2. Abra o painel em `http://<ip-do-ha>:8086/manager`, entre com a `api_key`.
3. Crie uma instância e leia o QR code no WhatsApp do número dedicado.
4. Configure o webhook da instância apontando para o n8n.

O banco fica em `/data/postgres` e entra no backup do add-on. A senha do banco é
gerada na primeira execução e guardada em `/data/db_password`; o PostgreSQL só
escuta em `127.0.0.1`.
