"""Program PC 2 (worker): tunggu koneksi, terima data, hitung, kirim hasil."""

from __future__ import annotations

import argparse
import socket
import time
from array import array
from typing import TYPE_CHECKING

from src import config, protocol, stats

if TYPE_CHECKING:  # hanya untuk type hint, tidak dipakai saat runtime
    import threading


def handle_task(header: dict, payload: bytes) -> tuple[dict, bytes]:
    """Hitung statistik bagian data dan siapkan pesan RESULT tanpa menyentuh socket."""
    data = array(config.ARRAY_TYPECODE)
    data.frombytes(payload)
    start = time.perf_counter()
    part = stats.compute_stats(data)
    elapsed = time.perf_counter() - start
    reply = {
        "type": config.MSG_RESULT,
        "count": part.count,
        "total": part.total,
        "sum_squares": part.sum_squares,
        "minimum": part.minimum,
        "maximum": part.maximum,
        "compute_seconds": elapsed,
    }
    return reply, b""


def serve_connection(conn: socket.socket, peer: tuple[str, int]) -> bool:
    """Layani satu koneksi master; kembalikan True bila perintah berhenti tiba.

    Koneksi dipertahankan agar master bisa mengirim beberapa ukuran data berurutan.
    """
    print(f"[worker] koneksi masuk dari {peer[0]}:{peer[1]}")
    while True:
        try:
            header, payload = protocol.receive_message(conn)
        except ConnectionError as exc:
            print(f"[worker] sesi dengan master berakhir: {exc}")
            return False
        message_type = header.get("type")
        if message_type == config.MSG_SHUTDOWN:
            print("[worker] perintah SHUTDOWN diterima, worker berhenti.")
            return True
        if message_type != config.MSG_TASK:
            print(f"[worker] pesan tak dikenal diabaikan: {message_type}")
            continue
        reply, reply_payload = handle_task(header, payload)
        protocol.send_message(conn, reply, reply_payload)
        print(
            f"[worker] count={reply['count']:,} sum={reply['total']:,} "
            f"min={reply['minimum']} max={reply['maximum']} "
            f"compute={reply['compute_seconds']:.4f}s"
        )


def serve(
    host: str = config.DEFAULT_HOST,
    port: int = config.DEFAULT_PORT,
    ready_event: threading.Event | None = None,
) -> None:
    """Dengarkan terus-menerus dan layani setiap koneksi master."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((host, port))
    listener.listen(config.LISTENER_BACKLOG)
    print(f"[worker] mendengarkan di {host}:{listener.getsockname()[1]}")
    if ready_event is not None:
        ready_event.set()
    try:
        _accept_loop(listener)
    except KeyboardInterrupt:
        print("\n[worker] dihentikan lewat Ctrl+C.")
    finally:
        listener.close()


def _accept_loop(listener: socket.socket) -> None:
    """Terima koneksi berulang sampai ada perintah berhenti."""
    while True:
        conn, peer = listener.accept()
        with conn:
            if serve_connection(conn, peer):
                return


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Baca argumen baris perintah worker."""
    parser = argparse.ArgumentParser(
        description="Worker PC 2 - Distributed Number Statistics"
    )
    parser.add_argument(
        "--host", default=config.DEFAULT_HOST, help="alamat yang dipantau"
    )
    parser.add_argument(
        "--port", type=int, default=config.DEFAULT_PORT, help="port TCP"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Titik masuk program worker."""
    args = parse_args(argv)
    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
