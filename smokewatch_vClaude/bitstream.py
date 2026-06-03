"""
Formato de cada registo — 75 bits:

  bits 74..11  →  timestamp Unix em milissegundos  (64 bits)
  bits  10..1  →  valor AO  (10 bits, 0–1023)
  bit       0  →  valor DO  ( 1 bit)

O ficheiro é um bitstream puro (MSB first).
LCM(75, 8) = 600 bits = 75 bytes: de 8 em 8 registos alinha a byte.

Escrita:
  - Calcula write_start_bit = file_bits - (file_bits % 75)
  - Preserva os bits anteriores a write_start_bit no último byte parcial
  - Escreve os novos registos a partir daí, com padding de 0s no final
  - Nunca apaga dados; usa seek+write para sobrescrever apenas o padding

Leitura:
  - N = floor(file_bits / 75)  →  número de registos completos
  - Ignora os últimos (file_bits % 75) bits (padding)
"""

import os

RECORD_BITS = 75
_MASK_64    = (1 << 64) - 1
_MASK_10    = (1 << 10) - 1
_MASK_75    = (1 << 75) - 1


# ── helpers de registo ──────────────────────────────────────────────────────

def encode(timestamp_ms: int, ao: int, do_val: int) -> int:
    """Empacota um registo em 75 bits (inteiro)."""
    return ((timestamp_ms & _MASK_64) << 11) | ((ao & _MASK_10) << 1) | (do_val & 1)


def decode(val: int) -> tuple:
    """Desempacota 75 bits → (timestamp_ms, ao, do_val)."""
    do_val = val & 1
    ao     = (val >> 1)  & _MASK_10
    ts     = (val >> 11) & _MASK_64
    return ts, ao, do_val


# ── escrita ─────────────────────────────────────────────────────────────────

def write_records(filepath: str, records: list):
    """
    Faz append de `records` (lista de (timestamp_ms, ao, do_val)) ao ficheiro.
    Se o ficheiro tiver bits de padding no final, começa a escrever a partir
    do último registo completo, sobrescrevendo o padding.
    """
    if not records:
        return

    # Tamanho atual do ficheiro
    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    file_bits = file_size * 8

    # Onde começa a escrita (descarta bits de padding)
    resto           = file_bits % RECORD_BITS
    write_start_bit = file_bits - resto

    byte_index = write_start_bit // 8   # primeiro byte a escrever
    bit_offset = write_start_bit % 8    # offset dentro desse byte (0 = MSB)

    # Constrói os novos dados como um único inteiro (MSB first)
    new_int = 0
    for ts, ao, do_val in records:
        new_int = (new_int << RECORD_BITS) | encode(ts, ao, do_val)

    new_bits    = len(records) * RECORD_BITS
    total_bits  = bit_offset + new_bits
    total_bytes = (total_bits + 7) // 8
    pad_bits    = total_bytes * 8 - total_bits  # zeros no final

    # Preserva os bits superiores do byte parcial existente (se aplicável)
    if bit_offset > 0 and file_size > byte_index:
        with open(filepath, 'rb') as f:
            f.seek(byte_index)
            existing = f.read(1)[0]
        prefix = existing >> (8 - bit_offset)  # top `bit_offset` bits
    else:
        prefix = 0

    # Combina: prefix | novos dados | padding de 0s
    combined      = (prefix << (new_bits + pad_bits)) | (new_int << pad_bits)
    result_bytes  = combined.to_bytes(total_bytes, 'big')

    # Escreve no ficheiro
    if file_size == 0:
        with open(filepath, 'wb') as f:
            f.write(result_bytes)
    else:
        with open(filepath, 'r+b') as f:
            f.seek(byte_index)
            f.write(result_bytes)


# ── leitura ─────────────────────────────────────────────────────────────────

def read_all_records(filepath: str) -> list:
    """
    Lê todos os registos completos do ficheiro.
    Devolve lista de (timestamp_ms, ao, do_val).
    """
    if not os.path.exists(filepath):
        return []

    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return []

    n = (file_size * 8) // RECORD_BITS
    if n == 0:
        return []

    with open(filepath, 'rb') as f:
        data = f.read()

    file_int  = int.from_bytes(data, 'big')
    total_bits = file_size * 8

    records = []
    for i in range(n):
        shift  = total_bits - (i + 1) * RECORD_BITS
        record = (file_int >> shift) & _MASK_75
        records.append(decode(record))

    return records
