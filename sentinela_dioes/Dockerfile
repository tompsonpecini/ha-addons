ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip tzdata \
    && pip3 install --no-cache-dir --break-system-packages requests pypdf

ENV TZ=America/Sao_Paulo

COPY run.sh /
COPY sentinela.py /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
