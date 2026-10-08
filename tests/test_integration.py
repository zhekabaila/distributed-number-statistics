"""Test integrasi: worker di thread pada 127.0.0.1 bertemu logika master."""

import socket
import threading
from array import array

import pytest

from src import config, master, stats, worker

START_TIMEOUT_SECONDS = 10.0


def free_port() -> int:
    """Ambil satu port TCP yang sedang bebas di 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def live_worker():
    """Jalankan worker di thread pada port bebas, lalu hentikan saat selesai."""
    port = free_port()
    ready = threading.Event()
    thread = threading.Thread(
        target=worker.serve, args=("127.0.0.1", port, ready), daemon=True
    )
    thread.start()
    assert ready.wait(START_TIMEOUT_SECONDS), "worker gagal memulai"
    try:
        yield port
    finally:
        _stop_worker(port)
        thread.join(START_TIMEOUT_SECONDS)
        assert not thread.is_alive(), "worker tidak berhenti setelah SHUTDOWN"


def _stop_worker(port: int) -> None:
    """Kirim SHUTDOWN lewat koneksi terpisah agar loop accept selesai."""
    try:
        master.send_shutdown("127.0.0.1", port, START_TIMEOUT_SECONDS)
    except OSError:
        pass


def test_handle_task_computes_partial_stats_from_payload():
    """handle_task mengubah payload bytes menjadi statistik parsial."""
    data = array(config.ARRAY_TYPECODE, [5, 7, 9])
    header, payload = worker.handle_task({"type": config.MSG_TASK}, data.tobytes())
    assert payload == b""
    assert header["type"] == config.MSG_RESULT
    assert (header["count"], header["total"], header["minimum"]) == (3, 21, 5)
    assert header["maximum"] == 9
    assert header["sum_squares"] == 25 + 49 + 81


def test_distributed_matches_sequential_on_ten_thousand(live_worker):
    """Hasil distributed sama persis dengan hasil sequential untuk 10.000 data."""
    data = stats.generate_data(10_000)
    run = master.run_distributed(data, "127.0.0.1", live_worker)
    sequential, _ = master.run_sequential(data)
    assert run.final_stats.count == sequential.count
    assert run.final_stats.total == sequential.total
    assert run.final_stats.sum_squares == sequential.sum_squares
    assert run.final_stats.minimum == sequential.minimum
    assert run.final_stats.maximum == sequential.maximum
    assert run.final_stats.mean == pytest.approx(sequential.mean)
    assert run.final_stats.std_dev == pytest.approx(sequential.std_dev, rel=1e-9)
    assert run.load_pc1 + run.load_pc2 == len(data)


@pytest.mark.parametrize("size", [1, 2, 3, 7])
def test_distributed_handles_tiny_and_odd_sizes(live_worker, size):
    """Ukuran sangat kecil dan ganjil tetap menghasilkan statistik yang benar."""
    data = stats.generate_data(size)
    run = master.run_distributed(data, "127.0.0.1", live_worker)
    sequential, _ = master.run_sequential(data)
    assert run.final_stats.total == sequential.total
    assert run.final_stats.count == size
    assert run.final_stats.minimum == sequential.minimum
    assert run.final_stats.maximum == sequential.maximum


def test_one_worker_serves_several_sizes_without_restart(live_worker):
    """Satu proses worker melayani beberapa ukuran data secara berurutan."""
    for size in (100, 251, 4096):
        data = stats.generate_data(size)
        run = master.run_distributed(data, "127.0.0.1", live_worker)
        assert run.final_stats.count == size
        assert run.final_stats.total == stats.compute_stats(data).total


def test_master_end_to_end_writes_results_csv(
    live_worker, tmp_path, monkeypatch, capsys
):
    """Perintah master lengkap mencetak laporan dan menyimpan results.csv."""
    monkeypatch.chdir(tmp_path)
    code = master.main(
        [
            "--worker-ip",
            "127.0.0.1",
            "--port",
            str(live_worker),
            "--sizes",
            "500",
            "999",
            "--mode",
            "both",
            "--shutdown-worker",
        ]
    )
    assert code == 0
    output = capsys.readouterr().out
    assert config.NPM in output
    assert "Hasil akhir (gabungan)" in output
    assert "Speedup" in output
    assert "Efficiency" in output
    written = (tmp_path / config.RESULT_CSV_FILENAME).read_text(encoding="utf-8")
    assert ",".join(config.CSV_HEADER) in written
    assert len(written.strip().splitlines()) == 3


def test_master_reports_friendly_error_without_worker(tmp_path, monkeypatch, capsys):
    """Master memberi pesan ramah ketika worker sama sekali tidak ada."""
    monkeypatch.chdir(tmp_path)
    code = master.main(
        ["--worker-ip", "127.0.0.1", "--port", str(free_port()), "--sizes", "100"]
    )
    assert code == 1
    output = capsys.readouterr().out
    assert "menolak koneksi" in output
    assert "python -m src.worker" in output


def test_master_requires_worker_ip_for_distributed_mode(capsys):
    """Mode distributed tanpa --worker-ip ditolak sebelum koneksi dibuat."""
    assert master.main(["--mode", "distributed"]) == 2
    assert "--worker-ip" in capsys.readouterr().out
