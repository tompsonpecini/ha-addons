# Changelog

## 1.0.1
- Imagem base declarada no Dockerfile. O build.yaml com `python:3.12-slim-bookworm` era recusado pelo Supervisor, que caía na imagem Alpine padrão (sem apt-get) e o build falhava.

## 1.0.0
- Primeira versão: API HTTP de transcrição com faster-whisper (modelo `small`, int8, CPU), na porta 8087.
