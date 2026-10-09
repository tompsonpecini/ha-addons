# Transcrição (Whisper)

Também gera fala com o [Piper](https://github.com/OHF-Voice/piper1-gpl): veja `POST /falar` abaixo.

Transcreve áudios em português com o [faster-whisper](https://github.com/SYSTRAN/faster-whisper), rodando na própria máquina do Home Assistant. Nada sai da rede local, exceto o download do modelo na primeira vez.

## Opções

| Opção | Para quê |
|---|---|
| `chave` | Senha que quem chama a API manda no cabeçalho `x-chave` (mínimo 16 caracteres). |
| `modelo` | `tiny`, `base`, `small` (padrão) ou `medium`. Maior = mais preciso e mais lento. |
| `idioma` | Código do idioma, `pt` por padrão. |
| `threads` | Núcleos de CPU usados na transcrição. |
| `voz` | Voz do Piper, no formato das [piper-voices](https://huggingface.co/rhasspy/piper-voices) (padrão `pt_BR-jeff-medium`). Baixada na primeira vez. |

## Uso

```
POST http://<ip-do-ha>:8087/transcrever
x-chave: <chave>
Content-Type: application/json

{"base64": "<áudio OGG/MP3/WAV/M4A em base64>"}
```

Resposta: `{"texto": "...", "duracao_s": 12.3, "processamento_s": 2.1}`.

### Fala

```
POST http://<ip-do-ha>:8087/falar
x-chave: <chave>
Content-Type: application/json

{"texto": "Boa noite! O Dr. Tompson atende pela Unimed."}
```

Resposta: `{"base64": "<OGG/Opus>", "mimetype": "audio/ogg", "duracao_s": 3.1, "processamento_s": 0.4}`.

Nem o texto transcrito nem o falado são gravados em log, só durações e tempos de processamento.
