#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sentinela DIO-ES - add-on local do Home Assistant OS.  (v2.0)

Consulta a API do portal IOES por DATA, em vez de adivinhar numero de edicao.

    /apifront/portal/edicoes/edicoes_from_data/AAAA-MM-DD.json?subtheme=

que devolve, para cada edicao daquela data:

    {"id":11389,"data":"14/08/2026","numero":26789,"tipo_edicao_id":1,
     "tipo_edicao_nome":"Diario Oficial do Espirito Santo","paginas":83}

Dois numeros diferentes convivem no portal e sao facilmente confundidos:
'numero' e o numero PUBLICADO (26789, o do cabecalho impresso) e 'id' e o ID
INTERNO usado nas URLs. Todo o resto do sistema usa o 'id'.

Os IDs sao globais no sistema IOES, que hospeda tambem diarios municipais - por
isso filtramos por 'tipo_edicao_id'. Edicoes extras e suplementos da mesma data
vem na mesma resposta e sao varridos tambem.

  /data/options.json   opcoes do add-on
  /data/estado.json    edicoes ja processadas (persistente)
  /share/sentinela_dioes/achados/   PDF das paginas com ocorrencia
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
import time
import traceback
import unicodedata
from datetime import date, datetime, timedelta

import requests
from pypdf import PdfReader

OPCOES = "/data/options.json"
ESTADO = "/data/estado.json"
ACHADOS = "/share/sentinela_dioes/achados"

SUPERVISOR = "http://supervisor/core/api"
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

BASE = "https://ioes.dio.es.gov.br"
URL_DATA = BASE + "/apifront/portal/edicoes/edicoes_from_data/{data}.json?subtheme="
URL_COMPLETO = BASE + "/portal/edicoes/download/{id}"
URL_PAGINA = BASE + "/apifront/portal/edicoes/pdf_diario/{id}/{pagina}"
URL_LEITURA = BASE + "/portal/visualizacoes/pdf/{id}/#/p:{pagina}/e:{id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) sentinela-dioes/2.0",
    "Referer": BASE + "/portal/visualizacoes/diario_oficial",
}

cfg: dict = {}


def log(nivel: str, msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {nivel} {msg}", flush=True)


def le_json(caminho: str, padrao: dict) -> dict:
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def salva_estado(e: dict) -> None:
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(e, f, ensure_ascii=False, indent=2)


def normaliza(texto: str) -> str:
    """Sem acento, MAIUSCULO, espacos colapsados, hifenizacao de linha desfeita.

    A hifenizacao importa: o Diario e diagramado em colunas estreitas e parte
    palavras (e nomes) no fim da linha.
    """
    texto = texto.replace("\u00ad", "")
    texto = re.sub(r"-\s*\n\s*", "", texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).upper()


# -------------------------------------------------------------- notificacao

def notifica(titulo: str, mensagem: str, url: str | None = None,
             critico: bool = False) -> None:
    log("INFO", f"NOTIFICA | {titulo} | {mensagem[:200]!r}")
    if not TOKEN:
        log("ERRO", "sem SUPERVISOR_TOKEN; alerta so no log")
        return

    cab = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    extra: dict = {}
    if url:
        extra["url"] = url
    if critico:
        extra["push"] = {"interruption-level": "time-sensitive", "sound": "default"}

    tentativas = []
    servico = cfg.get("notify_service", "")
    if servico:
        tentativas.append((f"{SUPERVISOR}/services/notify/{servico}",
                           {"title": titulo, "message": mensagem[:3500],
                            **({"data": extra} if extra else {})}))
    entidade = cfg.get("notify_entity", "")
    if entidade:
        tentativas.append((f"{SUPERVISOR}/services/notify/send_message",
                           {"entity_id": entidade, "title": titulo,
                            "message": mensagem[:3500]}))

    for endpoint, payload in tentativas:
        try:
            r = requests.post(endpoint, headers=cab, json=payload, timeout=20)
            if r.status_code < 300:
                return
            log("AVISO", f"{endpoint} respondeu HTTP {r.status_code}: {r.text[:200]}")
        except requests.RequestException as exc:
            log("AVISO", f"falha em {endpoint}: {exc}")
    log("ERRO", "nenhum canal de notificacao funcionou")


# ------------------------------------------------------------------- portal

def edicoes_da_data(sessao: requests.Session, dia: date) -> list[dict]:
    """Edicoes publicadas naquela data, ja filtradas pelo tipo de diario."""
    url = URL_DATA.format(data=dia.isoformat())
    tipo = cfg.get("tipo_edicao_id", 1)
    for i in range(1, 4):
        try:
            r = sessao.get(url, headers=HEADERS, timeout=45)
            r.raise_for_status()
            dados = r.json()
        except (requests.RequestException, ValueError) as exc:
            log("AVISO", f"consulta de {dia} tentativa {i}: {exc}")
            time.sleep(2 * i)
            continue
        if dados.get("erro"):
            msg = str(dados.get("msg") or "")
            # Fim de semana e feriado nao tem edicao: e resposta normal, nao falha.
            nivel = "INFO" if "exist" in msg.lower() else "AVISO"
            log(nivel, f"{dia}: {msg}")
            return []
        return [it for it in (dados.get("itens") or [])
                if it.get("tipo_edicao_id") == tipo]
    log("ERRO", f"nao consegui consultar a data {dia} apos 3 tentativas")
    return []


def baixa(sessao: requests.Session, url: str) -> bytes | None:
    """Baixa um PDF. Erro de rede e repetido; HTML (ID inexistente) nao.

    O portal responde HTTP 200 com pagina HTML quando o recurso nao existe, em
    vez de 404 - insistir nesse caso seria so barulho no log.
    """
    for i in range(1, 4):
        try:
            r = sessao.get(url, headers=HEADERS, timeout=120)
        except requests.RequestException as exc:
            log("AVISO", f"rede em {url} tentativa {i}: {exc}")
            time.sleep(2 * i)
            continue
        if r.status_code == 404:
            return None
        if r.status_code == 200:
            if r.content.startswith(b"%PDF"):
                return r.content
            if "html" in r.headers.get("Content-Type", "").lower():
                return None
        log("AVISO", f"resposta inesperada em {url} "
                     f"(HTTP {r.status_code}, {len(r.content)} bytes) tentativa {i}")
        time.sleep(2 * i)
    return None


def textos_por_pagina(sessao: requests.Session,
                      item: dict) -> tuple[list[tuple[int, str, bytes | None]], bytes | None]:
    """((numero_da_pagina, texto, pdf_da_pagina), pdf_da_edicao_inteira).

    Tenta primeiro a edicao completa num unico download; se o portal recusar,
    cai para uma requisicao por pagina. No primeiro caso o PDF individual da
    pagina nao existe, e a prova gravada em achados/ e a edicao inteira.
    """
    eid = item["id"]
    total = int(item.get("paginas") or 0)

    if cfg.get("usar_download_completo", True):
        inteiro = baixa(sessao, URL_COMPLETO.format(id=eid))
        if inteiro:
            try:
                leitor = PdfReader(io.BytesIO(inteiro))
                log("INFO", f"edicao {eid}: baixada inteira ({len(leitor.pages)} paginas, "
                            f"{len(inteiro)//1024} KB)")
                return ([(n, p.extract_text() or "", None)
                         for n, p in enumerate(leitor.pages, start=1)], inteiro)
            except Exception as exc:
                log("AVISO", f"edicao {eid}: PDF completo ilegivel ({exc}); "
                             "caindo para pagina a pagina")

    log("INFO", f"edicao {eid}: baixando pagina a pagina ({total} paginas)")
    pausa = cfg.get("pausa_segundos", 0.4)
    saida = []
    for n in range(1, total + 1):
        dados = baixa(sessao, URL_PAGINA.format(id=eid, pagina=n))
        time.sleep(pausa)
        if dados is None:
            log("AVISO", f"edicao {eid}: pagina {n} nao veio")
            continue
        try:
            texto = "\n".join((p.extract_text() or "")
                              for p in PdfReader(io.BytesIO(dados)).pages)
        except Exception as exc:
            log("ERRO", f"edicao {eid} pagina {n}: {exc}")
            texto = ""
        saida.append((n, texto, dados))
    return saida, None


# -------------------------------------------------------------------- ciclo

def processa_edicao(sessao: requests.Session, item: dict) -> dict:
    padroes = [(t, re.compile(t)) for t in cfg["termos"]]
    eid = item["id"]
    achados: list[dict] = []
    paginas, inteiro = textos_por_pagina(sessao, item)
    vazias = 0
    salvou_inteiro = False

    for numero, bruto, pdf in paginas:
        if len(bruto.strip()) < 40:
            vazias += 1
        texto = normaliza(bruto)
        for origem, padrao in padroes:
            for m in padrao.finditer(texto):
                ini, fim = max(0, m.start() - 300), min(len(texto), m.end() + 300)
                os.makedirs(ACHADOS, exist_ok=True)
                if pdf is not None:
                    caminho = os.path.join(ACHADOS, f"ed{eid}_p{numero:03d}.pdf")
                    with open(caminho, "wb") as f:
                        f.write(pdf)
                elif inteiro is not None and not salvou_inteiro:
                    caminho = os.path.join(ACHADOS, f"ed{eid}_completo.pdf")
                    with open(caminho, "wb") as f:
                        f.write(inteiro)
                    salvou_inteiro = True
                    log("INFO", f"prova gravada em {caminho}")
                achados.append({
                    "edicao": eid, "numero": item.get("numero"), "data": item.get("data"),
                    "pagina": numero, "termo": origem, "trecho": texto[ini:fim].strip(),
                    "link": URL_LEITURA.format(id=eid, pagina=numero)})
    return {"achados": achados, "paginas": len(paginas), "vazias": vazias}


def rotulo_do_termo(termo: str) -> str:
    """Versao legivel do regex, para a notificacao: \bPECINI\b -> PECINI."""
    r = termo.replace("\\b", "").replace("\\s+", " ").replace("\\s*", " ")
    r = re.sub(r"[\\^$()\[\]?*+|]", "", r)
    return r.strip() or termo


def monta_alerta(achados: list[dict]) -> tuple[str, str, str | None]:
    """(titulo, mensagem, url) - curto por padrao: termo e onde saiu."""
    por_termo: dict[str, list[dict]] = {}
    for a in achados:
        por_termo.setdefault(rotulo_do_termo(a["termo"]), []).append(a)

    linhas = []
    for rotulo, itens in por_termo.items():
        locais = "; ".join(f"ed. {i['numero']} de {i['data']}, pág. {i['pagina']}"
                           for i in itens[:5])
        if len(itens) > 5:
            locais += f" (+{len(itens) - 5})"
        linhas.append(f"{rotulo} — {locais}")

    nomes = ", ".join(por_termo)
    titulo = f"DOE-ES: {nomes}" if len(nomes) <= 60 else \
             f"DOE-ES: {len(achados)} ocorrência(s)"
    mensagem = "\n".join(linhas)

    if cfg.get("incluir_trecho", False):
        mensagem += "\n\n" + "\n\n".join(
            f"pág. {a['pagina']}: ...{a['trecho'][:300]}..." for a in achados[:5])

    url = achados[0]["link"] if cfg.get("incluir_link", False) else None
    return titulo, mensagem, url


def ciclo() -> None:
    estado = le_json(ESTADO, {"processadas": []})

    # Se os termos mudaram, o que ja foi lido precisa ser lido de novo: caso
    # contrario um termo acrescentado hoje nunca seria procurado nas edicoes
    # da janela retroativa.
    assinatura = hashlib.sha1("\n".join(cfg["termos"]).encode()).hexdigest()[:12]
    if estado.get("termos_hash") != assinatura:
        if estado.get("termos_hash"):
            log("INFO", "termos mudaram; reprocessando a janela inteira")
        estado["processadas"] = []
        estado["termos_hash"] = assinatura
        salva_estado(estado)

    processadas = set(estado.get("processadas", []))
    sessao = requests.Session()
    hoje = date.today()
    dias = cfg.get("dias_retroativos", 7)

    achados: list[dict] = []
    suspeitas: list[str] = []
    vistas = 0

    for delta in range(dias, -1, -1):          # do mais antigo para o mais novo
        dia = hoje - timedelta(days=delta)
        for item in edicoes_da_data(sessao, dia):
            vistas += 1
            eid = item["id"]
            if eid in processadas:
                continue
            log("INFO", f"edicao {eid} (n. {item.get('numero')}, {item.get('data')}, "
                        f"{item.get('paginas')} pag.) ainda nao processada")
            res = processa_edicao(sessao, item)
            log("INFO", f"edicao {eid}: {res['paginas']} paginas lidas, "
                        f"{res['vazias']} sem texto, {len(res['achados'])} ocorrencia(s)")
            achados.extend(res["achados"])

            esperadas = int(item.get("paginas") or 0)
            if esperadas and res["paginas"] < esperadas * 0.9:
                suspeitas.append(f"Edicao {item.get('numero')}: li {res['paginas']} de "
                                 f"{esperadas} paginas anunciadas.")
            if res["paginas"] and res["vazias"] > res["paginas"] * 0.5:
                suspeitas.append(f"Edicao {item.get('numero')}: {res['vazias']}/"
                                 f"{res['paginas']} paginas sem camada de texto "
                                 "(o PDF pode ter virado imagem).")

            processadas.add(eid)
            estado["processadas"] = sorted(processadas)[-200:]
            estado["ultima_edicao_em"] = hoje.isoformat()
            salva_estado(estado)
        time.sleep(0.3)

    if achados:
        titulo, mensagem, url = monta_alerta(achados)
        notifica(titulo, mensagem, url=url, critico=True)

    if suspeitas:
        notifica("DOE-ES: leitura suspeita", "\n".join(suspeitas), critico=True)

    # Dead-man switch: o portal nao devolver nenhuma edicao na janela inteira
    # e quase sempre defeito (API mudou, DNS, rede), nao ausencia de publicacao.
    if vistas == 0 and estado.get("alerta_silencio_em") != hoje.isoformat():
        notifica("DOE-ES: monitor em silencio",
                 f"O portal nao devolveu nenhuma edicao nos ultimos {dias} dias. "
                 "Provavelmente a API mudou ou o add-on perdeu acesso a rede.",
                 critico=True)
        estado["alerta_silencio_em"] = hoje.isoformat()

    estado["ultima_execucao_ok"] = datetime.now().isoformat(timespec="seconds")
    salva_estado(estado)
    log("INFO", f"ciclo concluido: {vistas} edicao(oes) na janela, "
                f"{len(achados)} ocorrencia(s)")


def proximo_horario() -> datetime:
    agora = datetime.now()
    candidatos = []
    for h in cfg.get("horarios", ["07:00"]):
        try:
            hh, mm = (int(x) for x in h.split(":"))
        except ValueError:
            log("AVISO", f"horario invalido ignorado: {h}")
            continue
        alvo = agora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if alvo <= agora:
            alvo += timedelta(days=1)
        candidatos.append(alvo)
    return min(candidatos) if candidatos else agora + timedelta(hours=6)


def main() -> int:
    global cfg
    cfg = le_json(OPCOES, {})
    if not cfg.get("termos"):
        log("ERRO", "nenhum termo configurado; nada a fazer")
        return 1
    for t in cfg["termos"]:
        try:
            re.compile(t)
        except re.error as exc:
            log("ERRO", f"termo invalido {t!r}: {exc}")
            return 1
    log("INFO", f"{len(cfg['termos'])} termo(s); janela de "
                f"{cfg.get('dias_retroativos', 7)} dias; "
                f"horarios: {', '.join(cfg.get('horarios', []))}")

    primeira = True
    while True:
        if not primeira:
            alvo = proximo_horario()
            log("INFO", f"proxima varredura em {alvo:%d/%m %H:%M}")
            time.sleep(max(30, (alvo - datetime.now()).total_seconds()))
        primeira = False
        try:
            ciclo()
        except Exception:
            detalhe = traceback.format_exc()
            log("ERRO", f"falha nao tratada:\n{detalhe}")
            try:
                notifica("DOE-ES: monitor falhou",
                         detalhe.strip().splitlines()[-1][:300], critico=True)
            except Exception:
                pass
            time.sleep(300)


if __name__ == "__main__":
    sys.exit(main())
