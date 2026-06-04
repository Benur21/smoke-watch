#!/usr/bin/env python3
"""SmokeWatch bootstrapper for Raspberry Pi installs."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


REPO_ROOT = Path(__file__).resolve().parent
SYSTEMD_TARGET = Path("/etc/systemd/system/smokewatch.service")


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    root: Path
    service_template: Path
    systemd_unit_name: str


VARIANTS = {
    "claude": Variant(
        key="claude",
        label="Claude",
        root=REPO_ROOT / "smokewatch_vClaude",
        service_template=REPO_ROOT / "smokewatch_vClaude" / "smokewatch.service",
        systemd_unit_name="smokewatch",
    ),
    "copilot": Variant(
        key="copilot",
        label="Copilot",
        root=REPO_ROOT / "smokewatch_vCopilot",
        service_template=REPO_ROOT / "smokewatch_vCopilot" / "pi" / "smokewatch.service",
        systemd_unit_name="smokewatch.service",
    ),
}


def prompt_variant() -> Variant:
    print("Escolhe a versao a usar:")
    print("1) Claude")
    print("2) Copilot")

    while True:
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            raise SystemExit("Entrada terminada antes de escolher a versao.")

        if choice in {"1", "claude", "vclaude"}:
            return VARIANTS["claude"]
        if choice in {"2", "copilot", "vcopilot"}:
            return VARIANTS["copilot"]

        print("Opcao invalida. Usa 1 ou 2.")


def run_command(command: list[str], cwd: Path | None = None) -> None:
    location = f" (cwd={cwd})" if cwd is not None else ""
    print(f"$ {shlex.join(command)}{location}")
    subprocess.run(command, cwd=cwd, check=True)


def render_service(template_path: Path, working_directory: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    working_directory_text = str(working_directory)
    exec_start_text = f"/usr/bin/python3 {working_directory / 'main.py'}"
    rendered = re.sub(
        r"(?m)^WorkingDirectory=.*$",
        f"WorkingDirectory={working_directory_text}",
        template,
        count=1,
    )
    rendered = re.sub(
        r"(?m)^ExecStart=.*$",
        f"ExecStart={exec_start_text}",
        rendered,
        count=1,
    )
    return rendered


def write_temp_service(content: str) -> Path:
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".service", delete=False) as temp:
        temp.write(content)
        return Path(temp.name)


def sudo_prefix() -> list[str]:
    return [] if os.geteuid() == 0 else ["sudo"]


def main() -> int:
    variant = prompt_variant()

    if not variant.root.exists():
        print(f"Diretorio da variante nao encontrado: {variant.root}", file=sys.stderr)
        return 1
    if not variant.service_template.exists():
        print(f"Template do service nao encontrado: {variant.service_template}", file=sys.stderr)
        return 1

    working_directory = variant.root / "pi"
    main_entrypoint = working_directory / "main.py"
    if not main_entrypoint.exists():
        print(f"Entrada principal nao encontrada: {main_entrypoint}", file=sys.stderr)
        return 1

    rendered_service = render_service(variant.service_template, working_directory)
    temp_service = write_temp_service(rendered_service)
    prefix = sudo_prefix()

    try:
        print()
        print(f"Versao selecionada: {variant.label}")
        print(f"Path do clone: {variant.root}")
        print(f"WorkingDirectory: {working_directory}")
        print(f"ExecStart: /usr/bin/python3 {main_entrypoint}")
        print()

        run_command(prefix + ["cp", str(temp_service), str(SYSTEMD_TARGET)])
        run_command(prefix + ["systemctl", "daemon-reload"])
        run_command(prefix + ["systemctl", "enable", variant.systemd_unit_name])
        run_command(prefix + ["systemctl", "start", variant.systemd_unit_name])

        print()
        print("SmokeWatch instalado e iniciado.")
        print(f"Service instalado em: {SYSTEMD_TARGET}")
        return 0
    finally:
        temp_service.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
