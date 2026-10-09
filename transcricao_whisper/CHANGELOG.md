# Changelog

## 1.1.0
- Fala: `POST /falar` gera OGG/Opus (mensagem de voz do WhatsApp) com o Piper, voz `pt_BR-jeff-medium` por padrão (opção `voz`). Antes de falar, o texto é adaptado: "Dr." vira "Doutor", valores, horas, datas e telefones ficam por extenso, links e CEP não são lidos.

## 1.0.1
- Imagem base declarada no Dockerfile. O build.yaml com `python:3.12-slim-bookworm` era recusado pelo Supervisor, que caía na imagem Alpine padrão (sem apt-get) e o build falhava.

## 1.0.0
- Primeira versão: API HTTP de transcrição com faster-whisper (modelo `small`, int8, CPU), na porta 8087.
