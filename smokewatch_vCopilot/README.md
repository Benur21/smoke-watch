# SmokeWatch

Sistema de vigilância de qualidade do ar com Arduino + Raspberry Pi + browser.

## Objetivo
- Ler o sensor MQ-135 via Arduino.
- Guardar cada registo em RAM e, a cada 300 leituras, fazer append em `data.bin` como bitstream de 75 bits/registo.
- Servir um gráfico histórico interativo pelo browser na rede local.
- LED ACT do Pi acende enquanto a ligação série está ativa.

## Estrutura

- `arduino/smokewatch.ino` - código Arduino que envia `AO,DO\n` a 9600 baud e espelha `DO` no LED 13.
- `pi/main.py` - arranca threads, gere o ciclo de vida e controla a recuperação.
- `pi/serial_reader.py` - lê a série, atualiza o `deque` e acende o LED ACT.
- `pi/flush_worker.py` - grava `data.bin` em blocos de 300 registos.
- `pi/bitstream.py` - manipula leitura/escrita de registros de 75 bits.
- `pi/web_server.py` - serve Flask + Plotly.
- `pi/templates/index.html` - interface web do gráfico.

## Ligações do sensor

Ligações do MQ-135 ao Arduino:

- `VCC` → `5V`
- `GND` → `GND`
- `AO`  → `A0`
- `DO`  → `D2`

O `LED` interno do Arduino no pino `13` é usado como espelho direto de `DO`.

## Instalação

```bash
cd smokewatch
python3 -m pip install -r requirements.txt
```

## Execução

```bash
cd smokewatch/pi
python3 main.py
```

### Variáveis de ambiente
- `SMOKEWATCH_SERIAL_PORT` - porta série do Arduino (padrão `/dev/ttyACM0`).
- `SMOKEWATCH_ALERT_THRESHOLD` - limiar do valor AO que dispara a notificação no telefone (padrão `120`).
- `SMOKEWATCH_NTFY_TOPIC` - tópico do `ntfy.sh` para onde o alerta é enviado. Se estiver vazio, as notificações ficam desativadas.
- `SMOKEWATCH_NTFY_SERVER` - servidor `ntfy` a usar, por omissão `https://ntfy.sh`.
- `SMOKEWATCH_NTFY_TITLE` - título mostrado na notificação.

### Ficheiro `.env`

O `SmokeWatch` carrega automaticamente `smokewatch_vCopilot/pi/.env` quando arranca.

Exemplo:

```env
SMOKEWATCH_SERIAL_PORT=/dev/ttyACM0
SMOKEWATCH_ALERT_THRESHOLD=120
SMOKEWATCH_NTFY_TOPIC=meu-topico
SMOKEWATCH_NTFY_SERVER=https://ntfy.sh
SMOKEWATCH_NTFY_TITLE=SmokeWatch alerta
```

Formato suportado:
- `CHAVE=valor`
- `export CHAVE=valor`
- linhas vazias e comentários com `#`

## systemd

O ficheiro de serviço já está disponível em `pi/smokewatch.service`.

Para instalar no Raspberry Pi, copie-o para `/etc/systemd/system/` e recarregue o daemon:

```bash
sudo cp pi/smokewatch.service /etc/systemd/system/smokewatch.service
sudo systemctl daemon-reload
sudo systemctl enable smokewatch.service
sudo systemctl start smokewatch.service
```
