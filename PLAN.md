# PLAN.md

Rencana kerja untuk AI agent. Baca `AGENTS.md` dulu untuk aturan dan spesifikasi. Kerjakan fase berurutan, centang kotak saat selesai, dan jangan lanjut ke fase berikutnya sebelum kriteria selesai terpenuhi.

**Deadline pengumpulan:** 12 Oktober 2026, 23:55
**Tema:** Distributed Number Statistics (Python socket, tanpa library eksternal)

---

## Fase 0: Persiapan

- [x] Buat struktur folder sesuai `AGENTS.md` bagian 4 (termasuk `__init__.py` kosong di `src/` dan `tests/`).
- [x] Buat `requirements-dev.txt` berisi `pytest`.
- [x] Buat `src/config.py`:
  - `NPM`, `STUDENT_NAME`
  - `DEFAULT_PORT = 5000`, `DEFAULT_HOST = "0.0.0.0"`
  - `DEFAULT_SIZES = (1_000_000, 5_000_000, 10_000_000)`
  - `RANDOM_SEED`, `VALUE_MIN`, `VALUE_MAX`
  - `SOCKET_TIMEOUT_SECONDS`, `PROCESSORS = 2`

**Selesai jika:** `python -c "from src import config"` berjalan tanpa error.

---

## Fase 1: Logika Statistik (`src/stats.py`)

- [x] `PartialStats` dan `FinalStats` (dataclass).
- [x] `generate_data(size, seed)`.
- [x] `split_data(data, parts=2)`.
- [x] `compute_stats(data)` dengan satu loop Python.
- [x] `merge_stats(a, b)` termasuk turunan `mean` dan `std_dev`.
- [x] Tulis `tests/test_stats.py` bersamaan dengan kodenya.

**Selesai jika:** `pytest tests/test_stats.py -v` lulus, termasuk kasus data kosong dan satu elemen. Hasil `merge_stats` dari dua bagian sama dengan `compute_stats` pada data utuh.

---

## Fase 2: Protokol Socket (`src/protocol.py`)

- [x] `send_message(sock, header, payload)`.
- [x] `receive_message(sock)`.
- [x] `_recv_exactly(sock, n)`.
- [x] Tulis `tests/test_protocol.py` memakai `socket.socketpair()`.

**Selesai jika:** `pytest tests/test_protocol.py -v` lulus, termasuk payload besar (minimal 5 MB) dan koneksi putus di tengah pesan.

---

## Fase 3: Worker (`src/worker.py`)

- [x] Parsing argumen `--host`, `--port`.
- [x] Fungsi `handle_task(header, payload) -> (header, payload)` yang murni (tanpa socket) agar mudah di-test.
- [x] Fungsi `serve(host, port, ready_event=None)` yang melayani koneksi berulang dan berhenti pada `SHUTDOWN`.
- [x] Log terminal: alamat master, jumlah data, waktu hitung.

**Selesai jika:** worker bisa dijalankan manual dan menunggu koneksi tanpa error.

---

## Fase 4: Report (`src/report.py`)

- [x] `calculate_speedup`, `calculate_efficiency`.
- [x] Pencetak blok hasil per run (poin 3a sampai 3f di `AGENTS.md`) dan banner identitas.
- [x] Pencetak tabel ringkasan semua ukuran data.
- [x] `write_csv`.
- [x] Tulis `tests/test_report.py`.

**Selesai jika:** `pytest tests/test_report.py -v` lulus.

---

## Fase 5: Master (`src/master.py`)

- [x] Parsing argumen `--worker-ip`, `--port`, `--sizes`, `--mode`, `--timeout`, `--shutdown-worker`.
- [x] `run_sequential(data) -> (FinalStats, seconds)`.
- [x] `run_distributed(data, worker_ip, port) -> hasil lengkap (statistik PC 1, PC 2, gabungan, waktu)`.
- [x] Penanganan error koneksi dengan pesan ramah.
- [x] Loop untuk beberapa ukuran data, cetak tabel ringkasan, simpan `results.csv`.

**Selesai jika:** worker dan master berjalan di `127.0.0.1` dan menghasilkan output lengkap serta `results.csv`.

---

## Fase 6: Test Integrasi dan Validasi

- [x] `tests/test_integration.py`: jalankan `serve` di thread pada port bebas, master mengirim data kecil (misal 10.000), pastikan hasil distributed sama dengan sequential.
- [x] Tambah kasus ukuran ganjil dan ukuran sangat kecil (misal 1 dan 2 elemen).
- [x] Jalankan `python -m pytest -v` dan pastikan semua lulus.
- [x] Uji lokal manual dengan 3 ukuran (misal 100.000, 500.000, 1.000.000) dan cek tampilan output.

**Selesai jika:** seluruh test lulus dan output manual sesuai format di `AGENTS.md` bagian 6.6.

---

## Fase 7: Dokumentasi Lengkap (Wajib)

Buat `docs/DOKUMENTASI.md` sesuai `AGENTS.md` bagian 8.

- [x] Ringkasan aplikasi dan peran PC.
- [x] Struktur folder (tree) dan fungsi tiap file.
- [x] Diagram alur komunikasi.
- [x] Format protokol pesan.
- [x] Penjelasan setiap file, kelas, dan fungsi (tujuan, parameter, return, cara kerja).
- [x] Penjelasan rumus (statistik gabungan, speedup, efficiency).
- [x] Panduan konfigurasi jaringan dan cara menjalankan.
- [x] Ringkasan hasil `pytest -v`.
- [x] Tabel hasil uji LAN berisi placeholder untuk diisi pengguna.

**Selesai jika:** semua bagian di atas ada dan penjelasannya cukup rinci sehingga pembaca baru memahami seluruh kode.

---

## Fase 8: Pemeriksaan Akhir oleh Agent

- [x] Centang seluruh Definition of Done di `AGENTS.md` bagian 9.
- [x] Pastikan tidak ada dependensi di luar standard library pada `src/`.
- [x] Pastikan tidak ada file sementara atau `__pycache__` yang ikut dilaporkan.
- [x] Berikan ringkasan singkat ke pengguna: apa yang selesai, hasil test, dan langkah manual yang tersisa.

---

## Langkah Manual untuk Pengguna (Setelah Agent Selesai)

| Langkah | Keterangan | Target |
|---------|------------|--------|
| 1 | Hubungkan 2 PC ke LAN yang sama, catat IP masing-masing (`ipconfig` atau `ip a`) | 9 Okt |
| 2 | Pastikan `ping` antar PC berhasil, izinkan port 5000 di firewall PC 2 | 9 Okt |
| 3 | Salin folder proyek ke kedua PC | 9 Okt |
| 4 | Jalankan uji 3 ukuran data atau lebih, simpan `results.csv` dan tangkapan layar | 10 Okt |
| 5 | Rekam video demo MP4 (maks 10 menit) yang menampilkan terminal kedua PC | 10 Okt |
| 6 | Susun laporan PDF (maks 10 halaman) dari `docs/DOKUMENTASI.md` dan hasil uji | 11 Okt |
| 7 | Periksa ulang dan kumpulkan | sebelum 12 Okt 23:55 |

**Isi laporan:** judul, NIM dan nama, konsep distributed memory, arsitektur, konfigurasi jaringan 2 PC, penjelasan kode, hasil pengujian, analisis waktu, perhitungan speedup dan efficiency, kesimpulan.

---

## Catatan Analisis (Bahan Laporan)

- Distributed belum tentu lebih cepat untuk data kecil, karena waktu kirim data lewat LAN bisa lebih besar daripada waktu hitung yang dihemat.
- Speedup ideal adalah 2 dan efficiency ideal 100%. Hasil nyata biasanya di bawah itu karena overhead komunikasi, serialisasi, dan pembagian beban yang tidak sempurna.
- Bandingkan tren speedup terhadap ukuran data: biasanya membaik saat data membesar karena porsi komputasi makin dominan dibanding overhead tetap.
