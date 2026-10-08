"""Format output terminal, perhitungan speedup/efficiency, dan berkas CSV."""

import csv
from dataclasses import dataclass

from src import config
from src.stats import FinalStats, PartialStats


@dataclass
class RunResult:
    """Hasil lengkap satu percobaan untuk satu ukuran data."""

    size: int
    load_pc1: int = 0
    load_pc2: int = 0
    master_stats: PartialStats | None = None
    worker_stats: PartialStats | None = None
    final_stats: FinalStats | None = None
    sequential_stats: FinalStats | None = None
    master_compute_seconds: float = 0.0
    worker_compute_seconds: float = 0.0
    distributed_seconds: float = 0.0
    sequential_seconds: float = 0.0

    @property
    def speedup(self) -> float:
        """Percepatan distributed terhadap sequential."""
        return calculate_speedup(self.sequential_seconds, self.distributed_seconds)

    @property
    def efficiency(self) -> float:
        """Efficiency dalam persen dengan P = config.PROCESSORS."""
        return calculate_efficiency(self.speedup)

    def to_row(self) -> list[str]:
        """Ubah hasil menjadi baris CSV sesuai urutan config.CSV_HEADER."""
        return [
            str(self.size),
            str(self.load_pc1),
            str(self.load_pc2),
            f"{self.master_compute_seconds:.6f}",
            f"{self.worker_compute_seconds:.6f}",
            f"{self.distributed_seconds:.6f}",
            f"{self.sequential_seconds:.6f}",
            f"{self.speedup:.6f}",
            f"{self.efficiency:.6f}",
        ]


def calculate_speedup(t_seq: float, t_dist: float) -> float:
    """Speedup = T_sequential / T_distributed, 0.0 jika waktu tidak valid."""
    if t_dist <= 0:
        return 0.0
    return t_seq / t_dist


def calculate_efficiency(speedup: float, processors: int = config.PROCESSORS) -> float:
    """Efficiency = Speedup / P x 100 persen; 0.0 bila jumlah prosessor tidak valid."""
    if processors <= 0:
        return 0.0
    return speedup / processors * 100.0


def print_banner() -> None:
    """Cetak banner identitas sekali di awal run master."""
    line = "=" * config.SEPARATOR_WIDTH
    print(line)
    print(" DISTRIBUTED NUMBER STATISTICS")
    print(f" NPM  : {config.NPM}")
    print(f" Nama : {config.STUDENT_NAME}")
    print(line)


def _count(value: int) -> str:
    """Format angka bulat dengan pemisah ribuan."""
    return f"{value:,}"


def _seconds(value: float) -> str:
    """Format detik dengan empat angka desimal."""
    return f"{value:.4f}"


def print_run_result(run: RunResult) -> None:
    """Cetak blok hasil satu run: beban, hasil per PC, hasil akhir, dan waktu."""
    print(f"Jumlah data total        : {_count(run.size)}")
    if run.final_stats is not None:
        _print_distributed_block(run)
    else:
        print("Mode sequential: seluruh data dihitung oleh PC 1 saja.")
        print()
    print(f"Waktu sequential         : {_seconds(run.sequential_seconds)} detik")
    if run.speedup > 0:
        print(f"Speedup                  : {run.speedup:.2f}")
        print(f"Efficiency               : {run.efficiency:.2f} %")
    print()


def _print_distributed_block(run: RunResult) -> None:
    """Cetak beban, hasil parsial tiap PC, hasil gabungan, dan waktu per PC."""
    print(f"Beban PC 1 (Master)      : {_count(run.load_pc1)} data")
    print(f"Beban PC 2 (Worker)      : {_count(run.load_pc2)} data")
    print()
    _print_partial("Hasil PC 1", run.master_stats)
    _print_partial("Hasil PC 2", run.worker_stats)
    print()
    print(f"Hasil akhir (gabungan)   : {_format_final(run.final_stats)}")
    print()
    print(f"Waktu komputasi PC 1     : {_seconds(run.master_compute_seconds)} detik")
    print(f"Waktu komputasi PC 2     : {_seconds(run.worker_compute_seconds)} detik")
    print(f"Waktu distributed total  : {_seconds(run.distributed_seconds)} detik")


def _format_final(final: FinalStats) -> str:
    """Satu baris ringkas statistik akhir lengkap dengan mean dan std."""
    return (
        f"count={_count(final.count)}, sum={_count(final.total)}, "
        f"min={final.minimum}, max={final.maximum}, "
        f"mean={final.mean:.4f}, std={final.std_dev:.4f}"
    )


def _print_partial(label: str, part: PartialStats) -> None:
    """Cetak satu baris hasil parsial milik satu PC."""
    print(
        f"{label} : count={_count(part.count)}, sum={_count(part.total)}, "
        f"min={part.minimum}, max={part.maximum}"
    )


def print_summary_table(runs: list[RunResult]) -> None:
    """Cetak tabel ringkasan semua ukuran data."""
    line = "=" * config.SEPARATOR_WIDTH
    print(line)
    print(" RINGKASAN HASIL")
    print(line)
    header = _summary_row(config.SUMMARY_COLUMNS)
    print(header)
    print("-" * len(header))
    for run in runs:
        cells = [
            _count(run.size),
            _time_or_dash(run.sequential_seconds),
            _time_or_dash(run.distributed_seconds),
            f"{run.speedup:.2f}" if run.speedup else "-",
            f"{run.efficiency:.2f}%" if run.speedup else "-",
        ]
        print(_summary_row(cells))
    print(line)


def _time_or_dash(value: float) -> str:
    """Format waktu tabel, atau '-' bila percobaan tidak menjalankan mode itu."""
    return _seconds(value) if value else "-"


def _summary_row(cells: list[str] | tuple[str, ...]) -> str:
    """Susun satu baris tabel ringkasan dengan lebar kolom dari config."""
    padded = (
        f"{cell:>{width}}"
        for cell, width in zip(cells, config.SUMMARY_COLUMN_WIDTHS)
    )
    return " | ".join(padded)


def write_csv(rows: list[list[str]], path: str) -> None:
    """Simpan baris hasil ke berkas CSV, lengkap dengan header."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(config.CSV_HEADER)
        writer.writerows(rows)
