"""
Controlo do LED ACT (verde) do Raspberry Pi via sysfs.
Deteta em runtime o nome correto do LED (ACT ou led0).
"""
import os

_CANDIDATES = ['ACT', 'led0', 'led1']

def _find():
    for name in _CANDIDATES:
        path = f'/sys/class/leds/{name}'
        if os.path.exists(path):
            return path
    return None

_LED_PATH = _find()


def _write(filename: str, value: str):
    if _LED_PATH is None:
        return
    try:
        with open(os.path.join(_LED_PATH, filename), 'w') as f:
            f.write(value)
    except OSError as e:
        print(f'[LED] Erro em {filename}: {e}')


def set_act_led(state: bool):
    """Acende (True) ou apaga (False) o LED ACT em modo manual."""
    _write('trigger',    'none')
    _write('brightness', '1' if state else '0')


def restore_act_led():
    """Restaura o comportamento padrão (heartbeat) ao sair."""
    _write('trigger', 'heartbeat')
