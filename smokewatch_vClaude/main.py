"""
Ponto de entrada do SmokeWatch.

Arranque:
  1. Tenta ligar ao Arduino (2 tentativas × 10s)
  2. Se falhar → LED ACT apagado → sys.exit(1)
  3. Se suceder → arranca 3 threads: serial_reader, flush_worker, web_server
  4. Bloqueia no join da thread serial_reader
  5. Quando a thread serie terminar (Arduino desligado) → termina tudo
"""

import sys
import time
import threading
from collections import deque

import serial
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
from led import set_act_led, restore_act_led
from serial_reader import SerialReader
from flush_worker import FlushWorker
from web_server import start_web_server


def try_open_serial() -> serial.Serial | None:
    """Tenta abrir a porta série e obter pelo menos uma linha válida."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        print(f'[Main] Porta {SERIAL_PORT} aberta. A aguardar dados...')
        line = ser.readline()
        if line and b',' in line:
            return ser
        ser.close()
        return None
    except serial.SerialException as e:
        print(f'[Main] Erro ao abrir porta série: {e}')
        return None


def main():
    print('[Main] A iniciar SmokeWatch...')

    # Tentativa 1
    ser = try_open_serial()
    if ser is None:
        print(f'[Main] Sem resposta. A aguardar {SERIAL_TIMEOUT}s e a tentar novamente...')
        time.sleep(SERIAL_TIMEOUT)
        # Tentativa 2
        ser = try_open_serial()

    if ser is None:
        print('[Main] Arduino não encontrado após 2 tentativas. A terminar.')
        set_act_led(False)
        sys.exit(1)

    print('[Main] Arduino detetado.')

    # Recursos partilhados
    buffer = deque()
    lock   = threading.Lock()

    # Thread 1 — leitura série
    reader   = SerialReader(ser, buffer)
    t_reader = threading.Thread(target=reader.run, name='serial_reader', daemon=True)

    # Thread 2 — flush para SD
    worker   = FlushWorker(buffer, lock)
    t_worker = threading.Thread(target=worker.run, name='flush_worker', daemon=True)

    # Thread 3 — servidor web
    t_web = threading.Thread(
        target=start_web_server,
        args=(lock,),
        name='web_server',
        daemon=True
    )

    t_reader.start()
    t_worker.start()
    t_web.start()

    # Mantém o programa vivo enquanto a thread série estiver ativa
    try:
        t_reader.join()
    except KeyboardInterrupt:
        print('\n[Main] Interrompido pelo utilizador.')
    finally:
        restore_act_led()
        print('[Main] Programa terminado.')


if __name__ == '__main__':
    main()
