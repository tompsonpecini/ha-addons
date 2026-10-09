# Imagem base declarada aqui (o build.yaml está obsoleto e não aceita o nome curto python:...)
FROM docker.io/library/python:3.12-slim-bookworm

# libgomp1: paralelismo do CTranslate2 e do ONNX Runtime (Piper). O PyAV (dependência do faster-whisper) já traz o FFmpeg
# e decodifica OGG/Opus do WhatsApp sem conversão prévia.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir faster-whisper==1.1.1 requests piper-tts==1.8.0 num2words

COPY servidor.py /servidor.py
CMD [ "python", "-u", "/servidor.py" ]
