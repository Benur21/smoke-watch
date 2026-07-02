from __future__ import annotations

from urllib import error, parse, request


class NtfyNotifier:
    def __init__(
        self,
        topic: str | None,
        server: str = "https://ntfy.sh",
        title: str = "SmokeWatch alerta",
        timeout: float = 5.0,
    ) -> None:
        self.topic = topic.strip() if topic else ""
        self.server = server.rstrip("/")
        self.title = title
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.topic)

    def send(self, message: str, title: str | None = None) -> bool:
        if not self.enabled:
            return False

        url = f"{self.server}/{parse.quote(self.topic, safe='')}"
        data = message.encode("utf-8")
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "Title": title or self.title,
            "Priority": "default",
        }
        req = request.Request(url, data=data, headers=headers, method="POST")

        try:
            with request.urlopen(req, timeout=self.timeout):
                return True
        except error.URLError as exc:
            print(f"[ntfy] Falha ao enviar notificação: {exc}")
            return False
