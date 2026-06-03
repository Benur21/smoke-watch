"""
Monitoriza o deque partilhado.
Quando acumula FLUSH_THRESHOLD registos, adquire o lock e escreve no data.bin.
"""

import time
import threading
import bitstream
from config import DATA_FILE, FLUSH_THRESHOLD


class FlushWorker:
    def __init__(self, buffer, lock: threading.Lock):
        self._buffer = buffer
        self._lock   = lock

    def run(self):
        print(f'[FlushWorker] A monitorizar buffer (threshold={FLUSH_THRESHOLD})...')

        while True:
            if len(self._buffer) >= FLUSH_THRESHOLD:
                # Recolhe exatamente FLUSH_THRESHOLD registos
                records = []
                for _ in range(FLUSH_THRESHOLD):
                    try:
                        records.append(self._buffer.popleft())
                    except IndexError:
                        break

                if not records:
                    continue

                with self._lock:
                    try:
                        bitstream.write_records(DATA_FILE, records)
                        print(f'[FlushWorker] {len(records)} registos escritos no SD.')
                    except Exception as e:
                        print(f'[FlushWorker] Erro ao escrever: {e}')
            else:
                time.sleep(1)
