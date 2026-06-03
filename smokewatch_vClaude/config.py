import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERIAL_PORT     = '/dev/ttyACM0'   # alterar para /dev/ttyUSB0 se necessário
BAUD_RATE       = 9600
DATA_FILE       = os.path.join(BASE_DIR, 'data.bin')
FLUSH_THRESHOLD = 300              # registos em RAM antes de escrever no SD
WEB_HOST        = '0.0.0.0'
WEB_PORT        = 5000
SERIAL_TIMEOUT  = 10               # segundos à espera de resposta do Arduino
