"""API HTTP mínima de transcrição (faster-whisper) e de fala (Piper), tudo local.

POST /transcrever
    Cabeçalho  x-chave: <chave definida nas opções>
    Corpo      JSON {"base64": "<áudio em base64>"}  ou os bytes do áudio direto
    Resposta   {"texto": "...", "duracao_s": 12.3, "processamento_s": 2.1}
POST /falar
    Cabeçalho  x-chave: <chave>
    Corpo      JSON {"texto": "..."}
    Resposta   {"base64": "<OGG/Opus>", "mimetype": "audio/ogg", "duracao_s": 9.8, "processamento_s": 1.2}
GET /saude     {"ok": true, "modelo": "small", "voz": "pt_BR-jeff-medium"}

Nem o texto transcrito nem o texto falado vão para o log: só durações e tamanhos.
"""
import base64
import io
import json
import os
import re
import threading
import time
import urllib.request
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import av
import numpy as np
from faster_whisper import WhisperModel
from num2words import num2words
from piper import PiperVoice

with open('/data/options.json', encoding='utf-8') as f:
    OPC = json.load(f)
CHAVE = OPC.get('chave') or ''
MODELO = OPC.get('modelo') or 'small'
IDIOMA = OPC.get('idioma') or 'pt'
THREADS = int(OPC.get('threads') or 4)
VOZ = OPC.get('voz') or 'pt_BR-jeff-medium'
MAX_BYTES = 25 * 1024 * 1024
PASTA_VOZES = '/data/vozes'

if len(CHAVE) < 16:
    raise SystemExit("[transcricao] Defina 'chave' nas opções do add-on (mínimo 16 caracteres).")

print(f'[transcricao] Carregando modelo {MODELO} (a primeira vez baixa para /data/modelos)...', flush=True)
t0 = time.time()
modelo = WhisperModel(MODELO, device='cpu', compute_type='int8', cpu_threads=THREADS,
                      download_root='/data/modelos')
print(f'[transcricao] Modelo pronto em {time.time() - t0:.0f} s', flush=True)


def baixar_voz(nome):
    """Baixa a voz do Piper (rhasspy/piper-voices) na primeira vez. Ex.: pt_BR-jeff-medium."""
    os.makedirs(PASTA_VOZES, exist_ok=True)
    local, falante, qualidade = nome.split('-')
    base = f'https://huggingface.co/rhasspy/piper-voices/resolve/main/{local.split("_")[0]}/{local}/{falante}/{qualidade}/{nome}'
    for ext in ('onnx', 'onnx.json'):
        destino = f'{PASTA_VOZES}/{nome}.{ext}'
        if not os.path.exists(destino):
            print(f'[fala] Baixando {nome}.{ext}...', flush=True)
            urllib.request.urlretrieve(f'{base}.{ext}', destino + '.tmp')
            os.replace(destino + '.tmp', destino)
    return f'{PASTA_VOZES}/{nome}.onnx'


voz = PiperVoice.load(baixar_voz(VOZ))
print(f'[fala] Voz {VOZ} pronta', flush=True)

trava = threading.Lock()   # um processamento por vez: a CPU é o gargalo


def decodificar(dados):
    """OGG/Opus, MP3, M4A, WAV... -> amostras float32 mono a 16 kHz, como o Whisper espera.
    Feito aqui, e não pelo faster-whisper, porque o decode_audio dele quebra com o PyAV 15+."""
    partes = []
    reamostrar = av.AudioResampler(format='s16', layout='mono', rate=16000)
    with av.open(io.BytesIO(dados)) as cont:
        for quadro in cont.decode(audio=0):
            for q in reamostrar.resample(quadro):
                partes.append(q.to_ndarray().reshape(-1))
    for q in reamostrar.resample(None):
        partes.append(q.to_ndarray().reshape(-1))
    if not partes:
        raise ValueError('áudio sem amostras')
    return np.concatenate(partes).astype(np.float32) / 32768.0


# ---- Texto escrito -> texto para ser falado --------------------------------------------------
ABREVIACOES = [
    (r'\bDr\.(?=\s)', 'Doutor'), (r'\bDra\.(?=\s)', 'Doutora'), (r'\bSr\.(?=\s)', 'Senhor'), (r'\bSra\.(?=\s)', 'Senhora'),
    (r'\bAv\.(?=\s)', 'Avenida'), (r'\bEd\.(?=\s)', 'Edifício'), (r'\bn[ºo°]\.?\s*(?=\d)', 'número '),
    (r'/ES\b', ', Espírito Santo'), (r'\bSAMU\b', 'Samu'), (r'\bHECI\b', ''), (r'\bUNIMED\b', 'Unimed'), (r'\bTRINO\b', 'Trino'),
]


def por_extenso(n):
    return num2words(int(n), lang='pt_BR')


def texto_para_fala(t):
    t = re.sub(r'[\U0001F000-\U0001FAFF☀-➿️‍]', '', t)       # emojis (inclusive o 🤖)
    t = re.sub(r'^\s*:\s*', '', t)                                              # o ":" que sobra de "🤖:"
    t = re.sub(r'https?://\S+', 'o link está na mensagem escrita', t)
    t = re.sub(r'\(?\b(?:CEP\s*)?\d{2}\.?\d{3}-\d{3}\)?', '', t)                  # CEP não se fala
    for padrao, troca in ABREVIACOES:
        t = re.sub(padrao, troca, t)
    t = re.sub(r'R\$\s*(\d{1,3}(?:\.\d{3})*),00\b', lambda m: por_extenso(m.group(1).replace('.', '')) + ' reais', t)
    t = re.sub(r'R\$\s*(\d+)', lambda m: por_extenso(m.group(1)) + ' reais', t)
    # telefone (28) 3515-0919 -> dígitos um a um
    t = re.sub(r'\(?(\d{2})\)?\s*(9?\d{4})-(\d{4})',
               lambda m: ', '.join(' '.join(por_extenso(c) for c in g) for g in m.groups()), t)
    # horas: 8h, 14h30, 8:00
    t = re.sub(r'\b(\d{1,2})[h:](\d{2})\b', lambda m: f'{por_extenso(m.group(1))} e {por_extenso(m.group(2))}'
               if m.group(2) != '00' else f'{por_extenso(m.group(1))} horas', t)
    t = re.sub(r'\b(\d{1,2})h\b', lambda m: por_extenso(m.group(1)) + (' hora' if m.group(1) in ('1', '01') else ' horas'), t)
    t = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', lambda m: f'{por_extenso(m.group(1))} do {por_extenso(m.group(2))}', t)
    t = re.sub(r'\b\d+\b', lambda m: por_extenso(m.group(0)), t)
    t = re.sub(r'\s*\n+\s*', '. ', t)
    t = re.sub(r'\s{2,}', ' ', t).replace(' ,', ',')
    t = re.sub(r'[,\s]+([.!?])', r'\1', t).replace('..', '.')
    return t.strip()


def falar(texto):
    """Texto -> OGG/Opus mono 48 kHz (o formato da mensagem de voz do WhatsApp)."""
    wav = io.BytesIO()
    with wave.open(wav, 'wb') as w:
        voz.synthesize_wav(texto_para_fala(texto), w)
    wav.seek(0)
    saida = io.BytesIO()
    with av.open(wav) as ent, av.open(saida, 'w', format='ogg') as sai:
        fluxo = sai.add_stream('libopus', rate=48000)
        fluxo.layout = 'mono'
        reamostrar = av.AudioResampler(format='s16', layout='mono', rate=48000)
        amostras = 0
        for quadro in ent.decode(audio=0):
            for q in reamostrar.resample(quadro):
                amostras += q.samples
                for p in fluxo.encode(q):
                    sai.mux(p)
        for q in reamostrar.resample(None):
            amostras += q.samples
            for p in fluxo.encode(q):
                sai.mux(p)
        for p in fluxo.encode(None):
            sai.mux(p)
    return saida.getvalue(), amostras / 48000


class Handler(BaseHTTPRequestHandler):
    def _responder(self, codigo, dados):
        corpo = json.dumps(dados, ensure_ascii=False).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path == '/saude':
            return self._responder(200, {'ok': True, 'modelo': MODELO, 'voz': VOZ})
        self._responder(404, {'erro': 'não encontrado'})

    def do_POST(self):
        if self.path not in ('/transcrever', '/falar'):
            return self._responder(404, {'erro': 'não encontrado'})
        if self.headers.get('x-chave') != CHAVE:
            return self._responder(401, {'erro': 'chave inválida'})
        n = int(self.headers.get('Content-Length') or 0)
        if not 0 < n <= MAX_BYTES:
            return self._responder(413, {'erro': 'corpo vazio ou grande demais'})
        bruto = self.rfile.read(n)
        if self.path == '/falar':
            return self._falar(bruto)
        try:
            if 'json' in (self.headers.get('Content-Type') or ''):
                audio = base64.b64decode(json.loads(bruto)['base64'])
            else:
                audio = bruto
            t0 = time.time()
            with trava:
                segs, info = modelo.transcribe(decodificar(audio), language=IDIOMA, vad_filter=True, beam_size=5)
                texto = ' '.join(s.text.strip() for s in segs).strip()
            proc = time.time() - t0
        except Exception as e:  # áudio corrompido, formato desconhecido etc.
            print(f'[transcricao] falha: {type(e).__name__}', flush=True)
            return self._responder(422, {'erro': f'não foi possível transcrever ({type(e).__name__})'})
        print(f'[transcricao] {len(audio) // 1024} KB, {info.duration:.0f} s de áudio, {proc:.1f} s de processamento',
              flush=True)
        self._responder(200, {'texto': texto, 'duracao_s': round(info.duration, 1), 'processamento_s': round(proc, 1)})

    def _falar(self, bruto):
        try:
            texto = str(json.loads(bruto)['texto'])[:3000]
            if not texto.strip():
                raise ValueError('texto vazio')
            t0 = time.time()
            with trava:
                ogg, dur = falar(texto)
            proc = time.time() - t0
        except Exception as e:
            print(f'[fala] falha: {type(e).__name__}', flush=True)
            return self._responder(422, {'erro': f'não foi possível gerar a fala ({type(e).__name__})'})
        print(f'[fala] {len(texto)} caracteres, {dur:.0f} s de áudio, {proc:.1f} s de processamento', flush=True)
        self._responder(200, {'base64': base64.b64encode(ogg).decode(), 'mimetype': 'audio/ogg',
                              'duracao_s': round(dur, 1), 'processamento_s': round(proc, 1)})

    def log_message(self, *args):   # sem log de acesso padrão
        pass


ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
