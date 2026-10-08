"""Test protokol pesan pada src/protocol.py memakai socketpair."""

import socket
import threading

import pytest

from src import config, protocol

BIG_PAYLOAD_SIZE = 5_000_000
TEST_TIMEOUT_SECONDS = 15.0


@pytest.fixture
def pair():
    """Sepasang socket terhubung untuk uji kirim/terima tanpa jaringan."""
    sockets = socket.socketpair()
    for sock in sockets:
        sock.settimeout(TEST_TIMEOUT_SECONDS)
    try:
        yield sockets
    finally:
        for sock in sockets:
            sock.close()


def receive_in_thread(receiver: socket.socket) -> tuple[dict, bytes]:
    """Terima pesan pada thread bantu.

    Hanya memindahkan byte, tanpa komputasi, jadi aturan larangan threading untuk
    komputasi tetap utuh. Diperlukan karena sendall payload 5 MB akan menggantung
    bila tidak ada pembaca yang berjalan bersamaan.
    """
    box = []

    def worker():
        try:
            box.append(protocol.receive_message(receiver))
        except OSError as exc:  # disimpan agar bisa di-assert di thread utama
            box.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    return box, thread


def test_send_then_receive_round_trip(pair):
    """Header dan payload diterima kembali sama persis."""
    sender, receiver = pair
    header = {"type": config.MSG_TASK, "count": 3}
    payload = bytes([1, 2, 3, 250])
    protocol.send_message(sender, header, payload)
    got_header, got_payload = protocol.receive_message(receiver)
    assert got_header == header
    assert got_payload == payload


def test_receive_empty_payload(pair):
    """Payload kosong sah dan dikembalikan sebagai b''."""
    sender, receiver = pair
    protocol.send_message(sender, {"type": config.MSG_SHUTDOWN})
    header, payload = protocol.receive_message(receiver)
    assert header == {"type": config.MSG_SHUTDOWN}
    assert payload == b""


def test_large_payload_round_trip(pair):
    """Payload besar (>= 5 MB) terkirim utuh walau melampaui buffer socket."""
    sender, receiver = pair
    payload = bytes(range(256)) * (BIG_PAYLOAD_SIZE // 256)
    box, thread = receive_in_thread(receiver)
    protocol.send_message(
        sender, {"type": config.MSG_TASK, "count": len(payload)}, payload
    )
    thread.join(TEST_TIMEOUT_SECONDS)
    assert not thread.is_alive(), "receive_message menggantung"
    header, got_payload = box[0]
    assert header["count"] == len(payload)
    assert len(got_payload) == len(payload)
    assert got_payload == payload


def test_several_messages_keep_boundaries(pair):
    """Batas pesan terjaga walau diterima berturut-turut dalam satu aliran byte."""
    sender, receiver = pair
    for index in range(3):
        protocol.send_message(
            sender, {"type": config.MSG_RESULT, "index": index}, b"x" * index
        )
    received = [protocol.receive_message(receiver) for _ in range(3)]
    assert [(h["index"], len(p)) for h, p in received] == [(0, 0), (1, 1), (2, 2)]


def test_receive_raises_connection_error_when_peer_closes(pair):
    """Koneksi putus di tengah pesan memunculkan ConnectionError."""
    sender, receiver = pair
    sender.sendall(b"\x00\x00\x00\x08")
    sender.close()
    with pytest.raises(ConnectionError):
        protocol.receive_message(receiver)


def test_recv_exactly_returns_requested_bytes(pair):
    """_recv_exactly mengumpulkan byte yang datang mencicil menjadi satu blok."""
    sender, receiver = pair
    payload = b"abc"
    sender.sendall(payload)
    sender.close()
    assert protocol._recv_exactly(receiver, 3) == payload


def test_header_is_json_utf8(pair):
    """Header UTF-8 non-ASCII tetap terbaca utuh sebagai JSON di sisi penerima."""
    sender, receiver = pair
    protocol.send_message(sender, {"type": config.MSG_TASK, "note": "dua ribu"}, b"")
    header, _ = protocol.receive_message(receiver)
    assert header == {"type": config.MSG_TASK, "note": "dua ribu"}
