"""Kirim dan terima pesan socket: header JSON + payload bytes."""

import json
import socket
import struct

from src import config

_PACK = struct.Struct(config.HEADER_STRUCT_FORMAT)


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
    """Baca tepat `n` byte; raise ConnectionError bila koneksi putus lebih awal."""
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(min(remaining, config.RECV_CHUNK_BYTES))
        if not chunk:
            raise ConnectionError(
                "Koneksi terputus saat menunggu data, "
                f"butuh {n} byte dan baru diterima {n - remaining} byte."
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_message(sock: socket.socket, header: dict, payload: bytes = b"") -> None:
    """Kirim satu pesan: dua panjang 4 byte, header JSON, lalu payload mentah."""
    body = json.dumps(header).encode("utf-8")
    sock.sendall(_PACK.pack(len(body), len(payload)))
    if payload:
        sock.sendall(body + payload)
    else:
        sock.sendall(body)


def receive_message(sock: socket.socket) -> tuple[dict, bytes]:
    """Terima satu pesan dan kembalikan (header, payload)."""
    prefix = _recv_exactly(sock, _PACK.size)
    header_len, payload_len = _PACK.unpack(prefix)
    if header_len > config.MAX_HEADER_BYTES:
        raise ConnectionError(
            f"Ukuran header tidak masuk akal: {header_len} byte. "
            "Kemungkinan protokol tidak cocok."
        )
    body = _recv_exactly(sock, header_len + payload_len)
    header = json.loads(body[:header_len].decode("utf-8"))
    return header, body[header_len:]
