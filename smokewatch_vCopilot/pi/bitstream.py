import os
from pathlib import Path
from typing import Iterable, List, Tuple

RECORD_BITS = 75
TIMESTAMP_BITS = 64
AO_BITS = 10
DO_BITS = 1

MAX_AO = (1 << AO_BITS) - 1
MAX_TIMESTAMP = (1 << TIMESTAMP_BITS) - 1

Record = Tuple[int, int, int]


def encode_record(timestamp_ms: int, ao_value: int, do_value: int) -> int:
    if not (0 <= timestamp_ms <= MAX_TIMESTAMP):
        raise ValueError(f"timestamp out of range: {timestamp_ms}")
    if not (0 <= ao_value <= MAX_AO):
        raise ValueError(f"AO value out of range: {ao_value}")
    if do_value not in (0, 1):
        raise ValueError(f"DO value must be 0 or 1: {do_value}")

    return (timestamp_ms << (AO_BITS + DO_BITS)) | (ao_value << DO_BITS) | do_value


def decode_record(record_bits: int) -> Record:
    do_value = record_bits & 1
    ao_value = (record_bits >> DO_BITS) & MAX_AO
    timestamp_ms = record_bits >> (AO_BITS + DO_BITS)
    return timestamp_ms, ao_value, do_value


def _records_to_bitstream(records: Iterable[Record]) -> Tuple[int, int]:
    stream = 0
    count = 0
    for timestamp_ms, ao_value, do_value in records:
        stream = (stream << RECORD_BITS) | encode_record(timestamp_ms, ao_value, do_value)
        count += 1
    return stream, count * RECORD_BITS


def _preserve_prefix_byte(prefix_byte: int, prefix_bits: int) -> int:
    if prefix_bits == 0:
        return 0
    mask = 0xFF & (~((1 << (8 - prefix_bits)) - 1))
    preserved = prefix_byte & mask
    return preserved >> (8 - prefix_bits)


def append_records(data_path: str | Path, records: Iterable[Record], lock=None) -> None:
    if lock is not None:
        with lock:
            _append_records(data_path, records)
    else:
        _append_records(data_path, records)


def _append_records(data_path: str | Path, records: Iterable[Record]) -> None:
    records = list(records)
    if not records:
        return

    data_path = Path(data_path)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    mode = "r+b" if data_path.exists() else "w+b"
    with open(data_path, mode) as handle:
        handle.seek(0, os.SEEK_END)
        file_size_bytes = handle.tell()
        bit_offset = file_size_bytes * 8
        remainder = bit_offset % RECORD_BITS
        start_bit = bit_offset - remainder
        start_byte = start_bit // 8
        start_bit_offset = start_bit % 8

        if start_byte < file_size_bytes:
            handle.seek(start_byte)
            first_byte = handle.read(1)
            prefix_byte = first_byte[0] if first_byte else 0
        else:
            prefix_byte = 0

        record_stream, record_bits = _records_to_bitstream(records)
        total_bits = start_bit_offset + record_bits

        if start_bit_offset > 0:
            prefix = _preserve_prefix_byte(prefix_byte, start_bit_offset)
            stream_value = (prefix << record_bits) | record_stream
        else:
            stream_value = record_stream

        total_bytes = (total_bits + 7) // 8
        aligned_value = stream_value << ((total_bytes * 8) - total_bits)
        output = aligned_value.to_bytes(total_bytes, byteorder="big")

        handle.seek(start_byte)
        handle.write(output)
        handle.flush()
        os.fsync(handle.fileno())
        handle.truncate(start_byte + len(output))


def read_records(data_path: str | Path, lock=None) -> List[Record]:
    if lock is not None:
        with lock:
            return _read_records(data_path)
    return _read_records(data_path)


def _read_records(data_path: str | Path) -> List[Record]:
    data_path = Path(data_path)
    if not data_path.exists():
        return []

    raw = data_path.read_bytes()
    if not raw:
        return []

    total_bits = len(raw) * 8
    num_records = total_bits // RECORD_BITS
    if num_records == 0:
        return []

    all_bits = int.from_bytes(raw, byteorder="big")
    records: List[Record] = []
    for index in range(num_records):
        shift = total_bits - ((index + 1) * RECORD_BITS)
        record_value = (all_bits >> shift) & ((1 << RECORD_BITS) - 1)
        records.append(decode_record(record_value))

    return records
