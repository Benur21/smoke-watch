"""
Servidor web Flask.

Rotas:
  GET /        → página do gráfico (index.html)
  GET /data    → todos os registos como JSON
  GET /size    → tamanho atual do data.bin (para detetar novos dados)
"""

import os
import threading
import bitstream
from flask import Flask, jsonify, render_template
from config import DATA_FILE, WEB_HOST, WEB_PORT


def create_app(lock: threading.Lock) -> Flask:
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/size')
    def size():
        try:
            s = os.path.getsize(DATA_FILE) if os.path.exists(DATA_FILE) else 0
        except OSError:
            s = 0
        return jsonify({'size': s})

    @app.route('/data')
    def data():
        with lock:
            records = bitstream.read_all_records(DATA_FILE)

        payload = [
            {'ts': ts, 'ao': ao, 'do': do_val}
            for ts, ao, do_val in records
        ]
        return jsonify(payload)

    return app


def start_web_server(lock: threading.Lock):
    app = create_app(lock)
    print(f'[WebServer] A servir em http://0.0.0.0:{WEB_PORT}')
    app.run(host=WEB_HOST, port=WEB_PORT, use_reloader=False, threaded=True)
