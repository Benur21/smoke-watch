"""
Lê linhas do Arduino via porta série.
Cada linha tem o formato "AO,DO\n" (ex: "523,0\n").
Adiciona registos ao deque partilhado com o FlushWorker.
Controla o LED ACT do Pi: aceso = ligado, apagado = desligado.
"""

import time
import serial
from led import set_act_led


class SerialReader:
    def __init__(self, ser: serial.Serial, buffer):
        """
        ser    — objeto serial já aberto e validado
        buffer — collections.deque partilhado com o FlushWorker
        """
        self._ser    = ser
        self._buffer = buffer

    def run(self):
        """Loop principal (corre numa thread dedicada)."""
        set_act_led(True)
        print('[SerialReader] A ler dados do Arduino...')

        try:
            while True:
                raw = self._ser.readline()
                if not raw:
                    continue

                line = raw.decode('utf-8', errors='ignore').strip()
                parts = line.split(',')
                if len(parts) != 2:
                    continue

                try:
                    ao     = int(parts[0])
                    do_val = int(parts[1])
                except ValueError:
                    continue

                if not (0 <= ao <= 1023) or do_val not in (0, 1):
                    continue

                ts_ms = int(time.time() * 1000)
                self._buffer.append((ts_ms, ao, do_val))

        except serial.SerialException as e:
            print(f'[SerialReader] Ligação série perdida: {e}')
        except Exception as e:
            print(f'[SerialReader] Erro inesperado: {e}')
        finally:
            set_act_led(False)
            try:
                self._ser.close()
            except Exception:
                pass
            print('[SerialReader] Thread terminada.')
