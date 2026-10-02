ARG BUILD_FROM
FROM $BUILD_FROM

# A imagem da Evolution e node:24-alpine (Alpine 3.23)
RUN apk add --no-cache postgresql17 jq su-exec

COPY run.sh /run.sh
RUN chmod a+x /run.sh

ENTRYPOINT [ "/run.sh" ]
