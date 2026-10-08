ARG BUILD_FROM
FROM $BUILD_FROM

# libgomp1: paralelismo do CTranslate2. O PyAV (dependência do faster-whisper) já traz o FFmpeg
# e decodifica OGG/Opus do WhatsApp sem conversão prévia.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir faster-whisper==1.1.1 requests

COPY servidor.py /servidor.py
CMD [ "python", "-u", "/servidor.py" ]
