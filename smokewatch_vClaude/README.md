# SmokeWatch

Monitor de qualidade do ar com FC-22 (MQ-135), Arduino UNO e Raspberry Pi 5.

## Estrutura

```
smokewatch/
├── arduino/
│   └── smokewatch.ino        # sketch do Arduino
├── pi/
│   ├── config.py             # configuração central
│   ├── main.py               # ponto de entrada
│   ├── serial_reader.py      # leitura série → deque
│   ├── flush_worker.py       # deque → data.bin
│   ├── bitstream.py          # leitura/escrita de 75 bits/registo
│   ├── web_server.py         # Flask + gráfico Plotly
│   ├── led.py                # controlo do LED ACT
│   └── templates/
│       └── index.html        # gráfico interativo
├── data.bin                  # gerado em runtime
└── smokewatch.service        # unit do systemd
```

## Ligações físicas

| FC-22 | Arduino UNO |
|-------|-------------|
| VCC   | 5V          |
| GND   | GND         |
| A     | A0          |
| D     | D2          |

O cabo USB do Arduino serve para alimentação e comunicação série com o Pi.

## Instalação no Raspberry Pi

### 1. Copia os ficheiros

```bash
git clone <repo> /home/pi/smokewatch
# ou copia manualmente para /home/pi/smokewatch/
```

### 2. Instala dependências Python

```bash
pip3 install flask pyserial
```

### 3. Ajusta a porta série (se necessário)

Verifica qual a porta do Arduino:
```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

Edita `/home/pi/smokewatch/pi/config.py` se for diferente de `/dev/ttyACM0`.

### 4. Carrega o sketch no Arduino

Abre `arduino/smokewatch.ino` no Arduino IDE e carrega para o UNO.

### 5. Configura o arranque automático

```bash
sudo cp /home/pi/smokewatch/smokewatch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smokewatch
sudo systemctl start smokewatch
```

### Ver logs em tempo real

```bash
sudo journalctl -u smokewatch -f
```

### Parar/reiniciar manualmente

```bash
sudo systemctl stop smokewatch
sudo systemctl restart smokewatch
```

## Acesso ao gráfico

Abre no browser do teu PC (na mesma rede):
```
http://<ip-do-pi>:5000
```

Para descobrir o IP do Pi:
```bash
hostname -I
```

## Formato do ficheiro data.bin

Bitstream puro, 75 bits por registo:
- bits 74..11 — timestamp Unix em milissegundos (64 bits)
- bits 10..1  — valor AO (10 bits, 0–1023)
- bit  0      — valor DO (1 bit)

Armazenamento: ~810 KB/dia, ~288 MB/ano.
