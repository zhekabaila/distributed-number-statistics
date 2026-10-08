# AGENTS.md

Panduan untuk AI agent yang mengerjakan proyek ini. Baca file ini sepenuhnya, lalu ikuti urutan kerja di `PLAN.md`.

## 1. Ringkasan Proyek

**Nama aplikasi:** Distributed Number Statistics (Distributed Memory 2 PC)

**Tujuan:** Aplikasi Python yang membagi sekumpulan angka ke 2 PC lewat jaringan LAN. Tiap PC punya memori sendiri dan menghitung statistik dasar (jumlah, min, max, rata-rata, standar deviasi) pada bagiannya. Hasil kedua PC digabung menjadi hasil akhir.

**Alasan tema ini:** Statistik dasar mudah dipahami, mudah dibagi dua, dan hasil parsial mudah digabung. Tidak butuh library eksternal.

**Peran PC:**

| PC | Peran | Tugas |
|----|-------|-------|
| PC 1 | Master / Coordinator | Bangkitkan data, bagi dua, kirim bagian 2 ke PC 2, hitung bagian 1, terima hasil PC 2, gabungkan |
| PC 2 | Worker / Processor | Menunggu koneksi, terima data, hitung, kirim hasil kembali |

## 2. Persyaratan Tugas (Wajib Terpenuhi)

1. Master membangkitkan data, membaginya minimal 2 bagian, mengirim sebagian ke worker lewat socket.
2. Master dan worker sama-sama menghitung, worker mengirim hasil balik, master menggabungkan.
3. Output program wajib menampilkan:
   - a. Jumlah data yang diproses
   - b. Jumlah data/beban per PC
   - c. Hasil komputasi PC 1
   - d. Hasil komputasi PC 2
   - e. Hasil akhir setelah penggabungan
   - f. Waktu eksekusi
4. Uji minimal 3 ukuran data berbeda (default: 1.000.000, 5.000.000, 10.000.000).
5. Bandingkan mode sequential (1 PC) dengan distributed (2 PC).
6. Hitung `Speedup = T_sequential / T_distributed` dan `Efficiency = Speedup / P x 100%` dengan `P = 2`.
7. Tiap run mencetak banner identitas: NPM `247006111152`, nama `Zheka Baila Arkan` (ambil dari `config.py`, jangan di-hardcode di banyak tempat).

## 3. Batasan Teknis

- Bahasa: Python 3.10 atau lebih baru.
- Komunikasi: modul `socket` bawaan (TCP). Jangan pakai MPI.
- Dependensi runtime: **tidak ada** (hanya standard library). Dependensi dev hanya `pytest`.
- Serialisasi data angka: modul `array` (tipe `'i'`) lalu `.tobytes()`. Jangan kirim list lewat `pickle`.
- Header pesan: JSON. Payload: bytes mentah.
- Dilarang memakai `multiprocessing`, `threading` untuk komputasi, atau `numpy`. Komputasi harus loop Python biasa agar perbandingan adil.
  - Pengecualian: `threading` hanya boleh di test integrasi untuk menjalankan worker lokal.

## 4. Struktur Folder

```
distributed-memory/
├── AGENTS.md
├── PLAN.md
├── requirements-dev.txt        # isi: pytest
├── src/
│   ├── __init__.py
│   ├── config.py               # konstanta: port, ukuran data, seed, identitas
│   ├── protocol.py             # kirim/terima pesan (header JSON + payload bytes)
│   ├── stats.py                # generate_data, split_data, compute_stats, merge_stats
│   ├── worker.py               # program PC 2
│   ├── master.py               # program PC 1 (mode distributed, sequential, both)
│   └── report.py               # format output tabel, speedup, efficiency
├── tests/
│   ├── __init__.py
│   ├── test_stats.py
│   ├── test_protocol.py
│   ├── test_report.py
│   └── test_integration.py     # worker lokal di 127.0.0.1 lewat thread
└── docs/
    └── DOKUMENTASI.md          # dibuat di akhir pekerjaan (lihat bagian 8)
```

## 5. Aturan Gaya Kode

- Ikuti PEP 8, panjang baris maksimal 88 karakter.
- Semua fungsi memakai **type hints** dan **docstring** singkat berbahasa Indonesia.
- Nama variabel, fungsi, dan file memakai bahasa Inggris (`compute_stats`, `send_message`). Komentar dan docstring memakai bahasa Indonesia.
- Satu fungsi satu tugas, idealnya di bawah 25 baris.
- Tidak ada variabel global yang berubah. Konstanta hanya di `config.py`, ditulis `HURUF_BESAR`.
- Tidak ada angka ajaib (magic number). Pindahkan ke `config.py`.
- Gunakan `dataclass` (atau `TypedDict`) untuk hasil statistik agar jelas isinya.
- Pesan error jelas dan berbahasa Indonesia. Tangani `ConnectionRefusedError` dan `socket.timeout` di master dengan pesan yang ramah.
- Tidak ada `print` tersebar di logika inti. `print` hanya di `master.py`, `worker.py`, dan `report.py`.
- Komentar menjelaskan **kenapa**, bukan mengulang isi baris.
- Tanpa emoji dan tanpa simbol dekoratif di output program.

## 6. Spesifikasi Modul

### 6.1 `stats.py`

- `generate_data(size: int, seed: int) -> array` : angka acak bulat, rentang di `config.py`, deterministik karena seed.
- `split_data(data, parts=2) -> list[array]` : bagi hampir rata, sisa masuk ke bagian terakhir. Total elemen harus tetap sama.
- `compute_stats(data) -> PartialStats` : hitung `count`, `total`, `sum_squares`, `minimum`, `maximum` dengan **satu loop Python**. Data kosong harus ditangani (count 0).
- `merge_stats(a, b) -> FinalStats` : gabungkan hasil parsial, lalu turunkan `mean` dan `std_dev` (populasi) dari `count`, `total`, `sum_squares`.

### 6.2 `protocol.py`

Format pesan: `[4 byte panjang header][4 byte panjang payload][header JSON][payload bytes]`, big-endian (`struct` format `"!II"`).

- `send_message(sock, header: dict, payload: bytes = b"") -> None`
- `receive_message(sock) -> tuple[dict, bytes]`
- `_recv_exactly(sock, n) -> bytes` : ulangi `recv` sampai `n` byte lengkap, raise `ConnectionError` jika koneksi putus.

Tipe pesan (`header["type"]`): `TASK` (master ke worker), `RESULT` (worker ke master), `SHUTDOWN` (master ke worker, opsional).

### 6.3 `worker.py`

- Argumen CLI: `--host` (default `0.0.0.0`), `--port` (default dari config).
- Loop `accept` terus-menerus, jadi bisa melayani banyak ukuran data tanpa restart. Berhenti jika menerima `SHUTDOWN` atau Ctrl+C.
- Untuk tiap `TASK`: ubah payload menjadi `array`, jalankan `compute_stats`, ukur waktu hitung sendiri, kirim `RESULT` berisi statistik parsial, `compute_seconds`, dan `count`.
- Cetak log ke terminal: alamat master, jumlah data diterima, hasil, waktu hitung.

### 6.4 `master.py`

- Argumen CLI: `--worker-ip` (wajib untuk mode distributed), `--port`, `--sizes` (satu atau lebih ukuran), `--mode {distributed,sequential,both}` (default `both`), `--timeout`.
- Alur mode distributed per ukuran data:
  1. Bangkitkan data (waktu pembangkitan **tidak** dihitung).
  2. Mulai timer. Bagi data jadi 2 bagian.
  3. Kirim bagian 2 ke worker.
  4. Hitung bagian 1 di master saat worker bekerja.
  5. Terima hasil worker, gabungkan, hentikan timer. Itu adalah `T_distributed` (sudah termasuk waktu kirim dan terima jaringan).
- Mode sequential: `compute_stats` seluruh data di master, itu adalah `T_sequential`.
- Setelah semua ukuran selesai, cetak tabel ringkasan lalu simpan ke `results.csv`.
- Opsi `--shutdown-worker` mengirim `SHUTDOWN` di akhir.

### 6.5 `report.py`

- `calculate_speedup(t_seq, t_dist) -> float`
- `calculate_efficiency(speedup, processors=2) -> float` (hasil dalam persen)
- Fungsi pencetak: blok hasil per run (poin 3a sampai 3f) dan tabel ringkasan semua ukuran.
- `write_csv(rows, path)` untuk `results.csv`.

### 6.6 Contoh Format Output Master (acuan, boleh disesuaikan sedikit)

```
============================================================
 DISTRIBUTED NUMBER STATISTICS
 NPM  : 247006111152
 Nama : Zheka Baila Arkan
============================================================
Jumlah data total        : 5,000,000
Beban PC 1 (Master)      : 2,500,000 data
Beban PC 2 (Worker)      : 2,500,000 data

Hasil PC 1 : count=..., sum=..., min=..., max=...
Hasil PC 2 : count=..., sum=..., min=..., max=...

Hasil akhir (gabungan)   : count=..., sum=..., min=..., max=..., mean=..., std=...

Waktu komputasi PC 1     : 0.xxxx detik
Waktu komputasi PC 2     : 0.xxxx detik
Waktu distributed total  : 0.xxxx detik
Waktu sequential         : 0.xxxx detik
Speedup                  : x.xx
Efficiency               : xx.xx %
```

## 7. Aturan Unit Test

- Framework: `pytest`. Jalankan dari root proyek: `python -m pytest -v`.
- Test tidak boleh bergantung pada jaringan eksternal atau PC kedua. Test integrasi memakai `127.0.0.1` dan port bebas (bind ke port `0`, lalu baca port yang diberikan OS).
- Cakupan minimum:
  - `test_stats.py`: split (genap, ganjil, ukuran kecil), compute_stats (nilai dikenal, data kosong, satu elemen), merge_stats (hasil gabungan sama dengan compute_stats pada data utuh), generate_data (deterministik, jumlah benar).
  - `test_protocol.py`: kirim lalu terima kembali sama persis (pakai `socket.socketpair()`), payload kosong, payload besar, koneksi putus memunculkan `ConnectionError`.
  - `test_report.py`: speedup dan efficiency dengan angka manual, pembagian nol ditangani.
  - `test_integration.py`: worker di thread, master mengirim data kecil, hasil distributed harus sama dengan sequential.
- Nama test deskriptif, contoh `test_merge_stats_equals_full_computation`.
- Semua test harus lulus sebelum pekerjaan dinyatakan selesai.

## 8. Dokumentasi Akhir (Wajib)

Setelah **semua** kode dan test selesai dan lulus, buat file baru `docs/DOKUMENTASI.md` berbahasa Indonesia. Isi minimal:

1. **Ringkasan aplikasi**: tujuan, tema, peran PC 1 dan PC 2.
2. **Struktur folder lengkap** dalam bentuk tree, lengkap dengan satu kalimat fungsi tiap file.
3. **Diagram alur komunikasi** (teks atau Mermaid): master, socket, worker, hasil, penggabungan.
4. **Format protokol pesan**: tabel field, ukuran byte, dan contoh header.
5. **Penjelasan kode per file, per fungsi dan kelas**: tujuan, parameter, nilai kembali, dan cara kerja langkah demi langkah. Untuk blok yang penting, kutip potongan kodenya lalu jelaskan baris demi baris.
6. **Penjelasan rumus**: statistik gabungan (mean dan std dari count, sum, sum_squares), speedup, efficiency.
7. **Cara menjalankan**: instalasi, konfigurasi IP PC 1 dan PC 2 (contoh `192.168.1.10` dan `192.168.1.11`), perintah worker, perintah master, cara menjalankan test, dan masalah umum (firewall, port, beda subnet).
8. **Hasil test**: salin ringkasan output `pytest -v`.
9. **Catatan hasil pengujian**: kosongkan tabel hasil dengan placeholder untuk diisi pengguna setelah uji di 2 PC sungguhan (jangan mengarang angka waktu).

Dokumentasi harus cukup lengkap sehingga orang yang belum pernah melihat kode bisa memahaminya tanpa membuka source.

## 9. Definition of Done

- [x] Semua modul di bagian 6 ada dan sesuai spesifikasi.
- [x] `python -m pytest -v` lulus semua.
- [x] Menjalankan worker dan master di `127.0.0.1` berhasil dan hasil distributed sama dengan sequential.
- [x] Output master memuat poin 3a sampai 3f, banner identitas, speedup, efficiency.
- [x] `results.csv` terbentuk.
- [x] `docs/DOKUMENTASI.md` selesai sesuai bagian 8.
- [x] Tidak ada dependensi runtime di luar standard library.

## 10. Hal yang Tidak Dikerjakan Agent

- Laporan PDF, video demo, dan pengujian di 2 PC fisik dikerjakan oleh pengguna.
- Jangan mengarang data hasil uji LAN. Hanya boleh menjalankan uji lokal untuk validasi kebenaran, dan beri label jelas bahwa itu hasil lokal.
- Jangan menambah fitur di luar spesifikasi (GUI, database, autentikasi, dan sejenisnya).

## 11. Perintah Cepat

```bash
# Pasang dependensi dev
pip install -r requirements-dev.txt

# Jalankan test
python -m pytest -v

# PC 2 (worker)
python -m src.worker --port 5000

# PC 1 (master)
python -m src.master --worker-ip 192.168.1.11 --port 5000 --sizes 1000000 5000000 10000000 --mode both

# Uji lokal satu mesin
python -m src.worker --host 127.0.0.1 &
python -m src.master --worker-ip 127.0.0.1 --sizes 100000 500000 1000000
```
