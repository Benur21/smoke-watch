import threading
import time
from collections import deque
from pathlib import Path
from typing import List, Tuple

from bitstream import append_records

Record = Tuple[int, int, int]


class FlushWorker(threading.Thread):
    def __init__(
        self,
        queue: deque,
        data_path: str | Path,
        file_lock: threading.Lock,
        stop_event: threading.Event,
        batch_size: int = 300,
        poll_interval: float = 0.5,
    ) -> None:
        super().__init__(daemon=True)
        self.queue = queue
        self.data_path = Path(data_path)
        self.file_lock = file_lock
        self.stop_event = stop_event
        self.batch_size = batch_size
        self.poll_interval = poll_interval

    def run(self) -> None:
        while not self.stop_event.is_set():
            if len(self.queue) < self.batch_size:
                time.sleep(self.poll_interval)
                continue

            records = self._drain_records(self.batch_size)
            if records:
                append_records(self.data_path, records, lock=self.file_lock)

        remaining = self._drain_records(len(self.queue))
        if remaining:
            append_records(self.data_path, remaining, lock=self.file_lock)

    def _drain_records(self, max_records: int) -> List[Record]:
        records: List[Record] = []
        while self.queue and len(records) < max_records:
            records.append(self.queue.popleft())
        return records
