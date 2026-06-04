# SmokeWatch

SmokeWatch é uma pilha local de monitorização da qualidade do ar baseada num Arduino UNO, num sensor MQ-135 e num Raspberry Pi. O Arduino lê o sensor a cada segundo e envia leituras `AO,DO` por série. O Pi assinala essas leituras com um carimbo temporal, guarda-as em RAM, escreve-as em `data.bin` como registos compactos de 75 bits e publica um painel histórico no navegador da rede local.

## Estrutura do repositório

Este repositório contém duas implementações independentes do mesmo projeto:

- `smokewatch_vCopilot/` - versão reestruturada com subpasta `pi/` e `requirements.txt`.
  <img src="assets/copilot-dashboard.png" alt="Painel SmokeWatch vCopilot" width="900" />
- `smokewatch_vClaude/` - versão anterior com estrutura plana e o mesmo fluxo principal.
  <img src="assets/claude-dashboard.png" alt="Painel SmokeWatch vClaude" width="900" />

Cada variante tem o seu próprio `README.md` com notas específicas.

## Ligações do hardware

MQ-135 para Arduino UNO:

- `VCC` -> `5V`
- `GND` -> `GND`
- `AO` -> `A0`
- `DO` -> `D2`

O sketch do Arduino também espelha `DO` no LED embutido do pino `13`.

## Fluxo de execução

1. O Arduino lê as saídas analógica e digital do sensor e envia-as a `9600` baud.
2. O Pi lê cada linha série, valida os valores e adiciona um timestamp em milissegundos.
3. A tarefa de descarga mantém as leituras em RAM e acrescenta-as a `data.bin` em lotes de 300 registos.
4. A aplicação Flask expõe um painel em `/` e dados JSON em `/data` para a interface do navegador.
5. O LED ACT do Pi fica aceso enquanto a ligação série estiver saudável.

## Formato dos dados

Cada registo em `data.bin` usa 75 bits:

- 64 bits - timestamp Unix em milissegundos
- 10 bits - valor analógico (`AO`)
- 1 bit - valor digital (`DO`)

Este formato compacto reduz o espaço ocupado sem perder o histórico completo.

## Requisitos

- Python 3.10 ou mais recente
- `Flask`
- `pyserial`
- Arduino IDE para carregar o sketch

## Arranque rápido

### `smokewatch_vCopilot`

```bash
cd smokewatch_vCopilot
python3 -m pip install -r requirements.txt
python3 pi/main.py
```

Se precisares de uma porta série diferente:

```bash
export SMOKEWATCH_SERIAL_PORT=/dev/ttyACM0
```

### `smokewatch_vClaude`

```bash
cd smokewatch_vClaude
python3 -m pip install flask pyserial
python3 main.py
```

Se o Arduino não estiver em `/dev/ttyACM0`, ajusta `config.py` antes de arrancares a aplicação.

## Painel web

Abre o Pi num navegador na mesma rede:

```text
http://<ip-do-pi>:5000
```

Rota útil:

- `GET /data` - devolve timestamps, valores AO, valores DO, contagem de registos, tamanho do ficheiro e a hora da última atualização.

Para descobrir o IP do Pi:

```bash
hostname -I
```

## systemd

Cada variante inclui uma unidade `smokewatch.service`. Antes de a ativares, atualiza os caminhos rígidos de `WorkingDirectory` e `ExecStart` para corresponderem ao local do checkout.

Exemplo para a estrutura `smokewatch_vCopilot`:

```bash
sudo cp smokewatch_vCopilot/pi/smokewatch.service /etc/systemd/system/smokewatch.service
sudo systemctl daemon-reload
sudo systemctl enable smokewatch.service
sudo systemctl start smokewatch.service
```

## Documentação das variantes

- [smokewatch_vCopilot/README.md](smokewatch_vCopilot/README.md)
- [smokewatch_vClaude/README.md](smokewatch_vClaude/README.md)

##

Este README.md foi escrito por Codex.
