#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

bashio::log.info "Iniciando Sentinela DIO-ES..."
exec python3 -u /sentinela.py
