SERVICE ?= smokewatch.service
SUDO ?= sudo

.PHONY: start stop restart logs status

start:
	$(SUDO) systemctl start $(SERVICE)

stop:
	$(SUDO) systemctl stop $(SERVICE)

restart:
	$(SUDO) systemctl restart $(SERVICE)

logs:
	$(SUDO) journalctl -u $(SERVICE) -f

status:
	$(SUDO) systemctl status $(SERVICE)
