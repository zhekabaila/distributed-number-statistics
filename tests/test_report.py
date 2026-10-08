"""Test perhitungan dan pencetak laporan pada src/report.py."""

import pytest

from src import config, report, stats
from src.stats import PartialStats


def test_calculate_speedup_manual_numbers():
    """Speedup memakai angka manual yang mudah diverifikasi."""
    assert report.calculate_speedup(4.0, 1.0) == pytest.approx(4.0)
    assert report.calculate_speedup(3.0, 2.0) == pytest.approx(1.5)


def test_calculate_speedup_zero_distributed_time():
    """Waktu distributed nol atau negatif tidak memicu pembagian nol."""
    assert report.calculate_speedup(4.0, 0.0) == 0.0
    assert report.calculate_speedup(4.0, -1.0) == 0.0


def test_calculate_efficiency_manual_numbers():
    """Efficiency = speedup / P x 100 persen."""
    assert report.calculate_efficiency(2.0, processors=2) == pytest.approx(100.0)
    assert report.calculate_efficiency(1.5, processors=2) == pytest.approx(75.0)


def test_calculate_efficiency_default_processors_follow_config():
    """Tanpa argumen, jumlah prosessor diambil dari config."""
    assert report.calculate_efficiency(1.0) == pytest.approx(
        1.0 / config.PROCESSORS * 100.0
    )


def test_calculate_efficiency_zero_processors():
    """Jumlah prosessor nol ditangani tanpa ZeroDivisionError."""
    assert report.calculate_efficiency(2.0, processors=0) == 0.0


def test_run_result_speedup_and_efficiency_properties():
    """Properti RunResult menghubungkan waktu run dengan rumus laporan."""
    run = report.RunResult(
        size=100, sequential_seconds=8.0, distributed_seconds=4.0
    )
    assert run.speedup == pytest.approx(2.0)
    assert run.efficiency == pytest.approx(100.0)


def test_run_result_row_matches_csv_header_length():
    """Jumlah kolom baris CSV sama dengan jumlah nama header."""
    assert len(report.RunResult(size=1).to_row()) == len(config.CSV_HEADER)


def test_write_csv_creates_header_and_rows(tmp_path):
    """write_csv menghasilkan berkas dengan header lalu baris data."""
    path = tmp_path / "results.csv"
    report.write_csv([["10", "5", "5", "1", "2", "3", "4", "5", "6"]], str(path))
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == ",".join(config.CSV_HEADER)
    assert lines[1] == "10,5,5,1,2,3,4,5,6"


def test_print_banner_contains_identity(capsys):
    """Banner memuat NPM dan nama dari config."""
    report.print_banner()
    output = capsys.readouterr().out
    assert config.NPM in output
    assert config.STUDENT_NAME in output


def test_print_run_result_shows_required_points(capsys):
    """Blok hasil memuat poin a sampai f: beban, hasil per PC, gabungan, waktu."""
    run = report.RunResult(
        size=6,
        load_pc1=3,
        load_pc2=3,
        master_stats=PartialStats(3, 6, 14, 1, 3),
        worker_stats=PartialStats(3, 12, 50, 4, 6),
        final_stats=stats.merge_stats(
            PartialStats(3, 6, 14, 1, 3), PartialStats(3, 12, 50, 4, 6)
        ),
        master_compute_seconds=0.5,
        worker_compute_seconds=0.6,
        distributed_seconds=1.2,
        sequential_seconds=2.4,
    )
    report.print_run_result(run)
    output = capsys.readouterr().out
    for expected in [
        "Jumlah data total        : 6",
        "Beban PC 1 (Master)      : 3 data",
        "Beban PC 2 (Worker)      : 3 data",
        "Hasil PC 1 :",
        "Hasil PC 2 :",
        "Hasil akhir (gabungan)",
        "Waktu komputasi PC 1     : 0.5000 detik",
        "Waktu komputasi PC 2     : 0.6000 detik",
        "Waktu distributed total  : 1.2000 detik",
        "Waktu sequential         : 2.4000 detik",
        "Speedup                  : 2.00",
        "Efficiency               : 100.00 %",
    ]:
        assert expected in output


def test_print_summary_table_lists_every_size(capsys):
    """Tabel ringkasan menampilkan satu baris untuk tiap ukuran data."""
    runs = [
        report.RunResult(size=1000, sequential_seconds=2.0, distributed_seconds=1.0),
        report.RunResult(size=2000, sequential_seconds=4.0),
    ]
    report.print_summary_table(runs)
    output = capsys.readouterr().out
    assert "1,000" in output
    assert "2,000" in output
    assert "RINGKASAN HASIL" in output
