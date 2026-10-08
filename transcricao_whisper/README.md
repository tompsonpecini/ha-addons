# Transcrição (Whisper)

Transcreve áudios em português com o [faster-whisper](https://github.com/SYSTRAN/faster-whisper), rodando na própria máquina do Home Assistant. Nada sai da rede local, exceto o download do modelo na primeira vez.

## Opções

| Opção | Para quê |
|---|---|
| `chave` | Senha que quem chama a API manda no cabeçalho `x-chave` (mínimo 16 caracteres). |
| `modelo` | `tiny`, `base`, `small` (padrão) ou `medium`. Maior = mais preciso e mais lento. |
| `idioma` | Código do idioma, `pt` por padrão. |
| `threads` | Núcleos de CPU usados na transcrição. |

## Uso

```
POST http://<ip-do-ha>:8087/transcrever
x-chave: <chave>
Content-Type: application/json

{"base64": "<áudio OGG/MP3/WAV/M4A em base64>"}
```

Resposta: `{"texto": "...", "duracao_s": 12.3, "processamento_s": 2.1}`.

O texto transcrito não é gravado em log, só a duração e o tempo de processamento.
