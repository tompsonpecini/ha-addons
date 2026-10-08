# Add-ons para Home Assistant

Repositório de add-ons próprios para Home Assistant OS.

## Instalação do repositório

Configurações → Complementos → Loja de complementos → menu ⋮ →
**Repositórios** → cole a URL deste repositório → **Adicionar**.

Os add-ons abaixo passam a aparecer na loja.

## Add-ons

### [Sentinela DIO-ES](./sentinela_dioes)

Monitora o Diário Oficial do Estado do Espírito Santo (Sistema IOES) e envia
notificação quando um termo configurado — nome, matrícula funcional, número de
registro profissional — é publicado.

Consulta a API do portal por data, baixa cada edição nova, extrai o texto e
compara com expressões regulares definidas pelo usuário. Guarda o PDF das
edições com ocorrência como prova datada.

### [Evolution API](./evolution_api)

API de WhatsApp (Evolution API v2) com PostgreSQL embutido. Conecta um número
por QR code e entrega as mensagens recebidas por webhook — feita para o n8n.

### [Transcrição (Whisper)](./transcricao_whisper)

Transcreve áudios em português (OGG do WhatsApp, MP3, M4A, WAV) com o
faster-whisper rodando na própria máquina, por uma API HTTP simples protegida
por chave. Nada sai da rede local além do download do modelo.

## Licença

MIT
