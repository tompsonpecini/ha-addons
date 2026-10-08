"""API HTTP mínima de transcrição com faster-whisper.

POST /transcrever
    Cabeçalho  x-chave: <chave definida nas opções>
    Corpo      JSON {"base64": "<áudio em base64>"}  ou os bytes do áudio direto
    Resposta   {"texto": "...", "duracao_s": 12.3, "processamento_s": 2.1}
GET /saude     {"ok": true, "modelo": "small"}

O texto transcrito nunca vai para o log: só durações e tamanhos.
"""
import base64
import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import av
import numpy as np
from faster_whisper import WhisperModel

with open('/data/options.json', encoding='utf-8') as f:
    OPC = json.load(f)
CHAVE = OPC.get('chave') or ''
MODELO = OPC.get('modelo') or 'small'
IDIOMA = OPC.get('idioma') or 'pt'
THREADS = int(OPC.get('threads') or 4)
MAX_BYTES = 25 * 1024 * 1024

if len(CHAVE) < 16:
    raise SystemExit("[transcricao] Defina 'chave' nas opções do add-on (mínimo 16 caracteres).")

print(f'[transcricao] Carregando modelo {MODELO} (a primeira vez baixa para /data/modelos)...', flush=True)
t0 = time.time()
modelo = WhisperModel(MODELO, device='cpu', compute_type='int8', cpu_threads=THREADS,
                      download_root='/data/modelos')
print(f'[transcricao] Modelo pronto em {time.time() - t0:.0f} s', flush=True)
trava = threading.Lock()   # uma transcrição por vez: a CPU é o gargalo


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
            return self._responder(200, {'ok': True, 'modelo': MODELO})
        self._responder(404, {'erro': 'não encontrado'})

    def do_POST(self):
        if self.path != '/transcrever':
            return self._responder(404, {'erro': 'não encontrado'})
        if self.headers.get('x-chave') != CHAVE:
            return self._responder(401, {'erro': 'chave inválida'})
        n = int(self.headers.get('Content-Length') or 0)
        if not 0 < n <= MAX_BYTES:
            return self._responder(413, {'erro': 'corpo vazio ou grande demais'})
        bruto = self.rfile.read(n)
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

    def log_message(self, *args):   # sem log de acesso padrão
        pass


ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
