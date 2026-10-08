"""Program PC 1 (master): bangkitkan data, kirim sebagian, gabungkan, laporkan."""

import argparse
import socket
import time
from array import array

from src import config, protocol, report, stats


def run_sequential(data: array) -> tuple[stats.FinalStats, float]:
    """Hitung seluruh data di satu PC dan ukur waktu komputasinya."""
    start = time.perf_counter()
    part = stats.compute_stats(data)
    elapsed = time.perf_counter() - start
    empty = stats.PartialStats(0, 0, 0, 0, 0)
    return stats.merge_stats(part, empty), elapsed


def run_distributed(
    data: array,
    worker_ip: str,
    port: int,
    timeout: float = config.SOCKET_TIMEOUT_SECONDS,
) -> report.RunResult:
    """Kirim separuh data ke worker, hitung separuhnya di master, gabungkan hasil.

    Waktu yang diukur (`distributed_seconds`) mencakup koneksi, pengiriman data,
    komputasi dua PC, dan penerimaan hasil, sesuai definisi T_distributed.
    """
    started = time.perf_counter()
    parts = stats.split_data(data, config.PROCESSORS)
    with socket.create_connection((worker_ip, port), timeout=timeout) as client:
        header, master_part, master_seconds = _run_two_pcs(client, parts)
    worker_part = partial_from_header(header)
    return report.RunResult(
        size=len(data),
        load_pc1=len(parts[0]),
        load_pc2=len(parts[1]),
        master_stats=master_part,
        worker_stats=worker_part,
        final_stats=stats.merge_stats(master_part, worker_part),
        master_compute_seconds=master_seconds,
        worker_compute_seconds=_result_seconds(header),
        distributed_seconds=time.perf_counter() - started,
    )


def _run_two_pcs(
    client: socket.socket, parts: list[array]
) -> tuple[dict, stats.PartialStats, float]:
    """Kirim bagian worker, hitung bagian master selagi worker bekerja, tunggu hasil."""
    task = {"type": config.MSG_TASK, "count": len(parts[1])}
    protocol.send_message(client, task, parts[1].tobytes())
    compute_start = time.perf_counter()
    master_part = stats.compute_stats(parts[0])
    master_seconds = time.perf_counter() - compute_start
    header, _ = protocol.receive_message(client)
    if header.get("type") != config.MSG_RESULT:
        raise ConnectionError(f"Worker mengirim balasan tak dikenal: {header}")
    return header, master_part, master_seconds


def _result_seconds(header: dict) -> float:
    """Ambil waktu komputasi worker dari header RESULT."""
    return float(header.get("compute_seconds", 0.0))


def partial_from_header(header: dict) -> stats.PartialStats:
    """Ubah header RESULT menjadi PartialStats agar bisa digabungkan."""
    return stats.PartialStats(
        count=int(header["count"]),
        total=int(header["total"]),
        sum_squares=int(header["sum_squares"]),
        minimum=int(header["minimum"]),
        maximum=int(header["maximum"]),
    )


def send_shutdown(worker_ip: str, port: int, timeout: float) -> None:
    """Kirim perintah SHUTDOWN agar worker menutup diri (opsional)."""
    with socket.create_connection((worker_ip, port), timeout=timeout) as client:
        protocol.send_message(client, {"type": config.MSG_SHUTDOWN})


def process_size(data: array, args: argparse.Namespace) -> report.RunResult:
    """Jalankan mode yang diminta untuk satu ukuran data dan kembalikan hasilnya."""
    if args.mode == "sequential":
        final, seconds = run_sequential(data)
        return report.RunResult(
            size=len(data),
            load_pc1=len(data),
            sequential_stats=final,
            sequential_seconds=seconds,
        )
    run = run_distributed(data, args.worker_ip, args.port, args.timeout)
    final, seconds = run_sequential(data)
    run.sequential_stats = final
    run.sequential_seconds = seconds
    return run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Baca argumen baris perintah master."""
    parser = argparse.ArgumentParser(
        description="Master PC 1 - Distributed Number Statistics"
    )
    parser.add_argument(
        "--worker-ip", help="IP PC 2, wajib untuk mode distributed dan both"
    )
    parser.add_argument(
        "--port", type=int, default=config.DEFAULT_PORT, help="port TCP worker"
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=list(config.DEFAULT_SIZES),
        help="satu atau lebih ukuran data yang diuji",
    )
    parser.add_argument(
        "--mode",
        choices=("distributed", "sequential", "both"),
        default="both",
        help="mode perhitungan",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=config.SOCKET_TIMEOUT_SECONDS,
        help="batas waktu operasi socket dalam detik",
    )
    parser.add_argument(
        "--shutdown-worker",
        action="store_true",
        help="irim SHUTDOWN ke worker setelah semua uji selesai",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> str | None:
    """Periksa argumen yang saling bertentangan, kembalikan pesan error atau None."""
    if args.mode != "sequential" and not args.worker_ip:
        return (
            f"Mode '{args.mode}' membutuhkan alamat worker. "
            "Tambahkan --worker-ip 192.168.1.11 misalnya."
        )
    if any(size <= 0 for size in args.sizes):
        return "Ukuran data harus lebih besar dari nol."
    return None


def main(argv: list[str] | None = None) -> int:
    """Titik masuk program master."""
    args = parse_args(argv)
    problem = validate_args(args)
    if problem:
        print(problem)
        return 2
    report.print_banner()
    runs: list[report.RunResult] = []
    for size in args.sizes:
        data = stats.generate_data(size, config.RANDOM_SEED)
        print(f"--- Uji dengan {size:,} data ---")
        try:
            run = process_size(data, args)
        except OSError as exc:
            print(connection_hint(args, exc))
            return 1
        runs.append(run)
        report.print_run_result(run)
    report.print_summary_table(runs)
    report.write_csv([run.to_row() for run in runs], config.RESULT_CSV_FILENAME)
    print(f"Hasil tersimpan di {config.RESULT_CSV_FILENAME}")
    if args.shutdown_worker:
        _try_shutdown(args)
    return 0


def connection_hint(args: argparse.Namespace, exc: OSError) -> str:
    """Ubah kegagalan jaringan menjadi pesan yang mudah dipahami."""
    address = f"{args.worker_ip}:{args.port}"
    if isinstance(exc, ConnectionRefusedError):
        return (
            f"PC 2 menolak koneksi di {address}. Pastikan worker sudah berjalan di "
            f"PC 2 dengan perintah: python -m src.worker --port {args.port}"
        )
    if isinstance(exc, TimeoutError):
        return (
            f"Waktu habis menunggu {address} (timeout {args.timeout:.0f} detik). "
            "Cek PC 2 masih menyala, dan port tidak diblokir firewall."
        )
    return f"Gagal berkomunikasi dengan worker di {address}: {exc}"


def _try_shutdown(args: argparse.Namespace) -> None:
    """Kirim SHUTDOWN dan abaikan bila worker sudah lebih dulu tertutup."""
    try:
        send_shutdown(args.worker_ip, args.port, args.timeout)
        print("Perintah SHUTDOWN terkirim ke worker.")
    except OSError as exc:
        print(f"Worker tidak menerima SHUTDOWN ({exc}); mungkin sudah berhenti.")


if __name__ == "__main__":
    raise SystemExit(main())
