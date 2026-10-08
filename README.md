# Distributed Number Statistics (Distributed Memory 2 PC)

Aplikasi Python yang membagi sekumpulan angka ke 2 PC lewat jaringan LAN. PC 1 sebagai master
(pembangkit data, pembagi, penggabungan hasil) dan PC 2 sebagai worker (hitung bagiannya lalu
kirim hasil balik). Hanya memakai standard library; komunikasi lewat modul `socket` (TCP).

Identitas: NPM `247006111152` — Zheka Baila Arkan (diubah di `src/config.py`).

Dokumentasi lengkap (penjelasan per fungsi, protokol, rumus): `docs/DOKUMENTASI.md`.

---

## 1. Syarat

- Python 3.10 atau lebih baru (cek: `python3 --version`).
- Dua PC pada satu jaringan LAN untuk uji sebenarnya, atau satu mesin untuk uji awal.
- Tidak ada dependensi runtime. `pytest` hanya untuk menjalankan test.

## 2. Masuk ke folder proyek

```bash
cd distributed-number-statistics
```

Ganti nama path sesuai lokasi folder proyek Anda. Semua perintah di README ini dijalankan
dari root proyek (folder yang berisi `AGENTS.md`).

## 3. Membuat dan mengaktifkan virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Bila PowerShell menolak script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser ExecutionPolicy RemoteSigned
```

Windows (CMD):

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

Setelah aktif, prompt terminal diawali `(.venv)` dan perintah `python` menunjuk ke
interpreter di dalam venv. Untuk keluar: `deactivate`.

## 4. Install dependensi dev

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

## 5. Jalankan test

```bash
python -m pytest -v
```

Harapannya: `42 passed`. Test memakai `127.0.0.1` dan port bebas, jadi tidak butuh PC kedua
maupun internet.

## 6. Uji cepat di satu mesin

Jalankan worker di jendela terminal pertama, biarkan tetap hidup:

```bash
python -m src.worker --host 127.0.0.1 --port 5000
```

Lalu di jendela terminal kedua (venv yang sama atau aktif kembali):

```bash
python -m src.master --worker-ip 127.0.0.1 --port 5000 --sizes 100000 500000 1000000
```

Anda akan melihat banner identitas, blok hasil per ukuran data (beban tiap PC, hasil PC 1,
hasil PC 2, hasil gabungan, waktu, speedup, efficiency), tabel ringkasan, dan berkas
`results.csv` di root proyek. Tambahkan `--shutdown-worker` bila ingin worker berhenti
otomatis setelah selesai.

Angka waktu dari satu mesin hanya untuk validasi kebenaran (hasil distributed harus sama
dengan sequential), bukan hasil uji LAN.

## 7. Menjalankan di dua PC (uji sebenarnya)

### 7.1 Siapkan jaringan

Cari IP kedua PC.

| Sistem | Perintah |
|--------|----------|
| Windows | `ipconfig` (lihat IPv4 Address) |
| Linux | `ip a` atau `ifconfig` |
| macOS | `ifconfig` atau System Settings > Network |

Contoh penomoran:

| PC | Peran | IP contoh |
|----|-------|-----------|
| PC 1 | Master | `192.168.1.10` |
| PC 2 | Worker | `192.168.1.11` |

Uji koneksi dari PC 1:

```bash
ping 192.168.1.11
```

### 7.2 Buka port di firewall PC 2

Port 5000/TCP harus diizinkan masuk (inbound) di PC 2.

Windows (PowerShell sebagai Administrator):

```powershell
New-NetFirewallRule -DisplayName "Distributed Stats 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

Linux (ufw):

```bash
sudo ufw allow 5000/tcp
```

Sementara pengujian, Anda juga bisa menjalankan worker pada port lain, misalnya `--port 5055`,
cukup samakan nilainya di kedua PC.

### 7.3 Salin proyek dan pasang venv di kedua PC

Folder proyek harus ada di kedua PC (isi sama persis). Ulangi langkah 3 dan 4 di atas pada
PC 2. Tidak perlu `pip install` selain `requirements-dev.txt`, dan hanya PC 1 yang memakai
pytest bila Anda hanya ingin menjalankan program.

Alternatif tanpa venv di PC 2: `python3 -m src.worker --port 5000` langsung dengan Python
sistem, karena program inti tanpa dependensi.

### 7.4 Jalankan worker di PC 2

```bash
python -m src.worker --host 0.0.0.0 --port 5000
```

Terminal menampilkan `[worker] mendengarkan di 0.0.0.0:5000` dan menunggu koneksi. Biarkan
terbuka selama pengujian. Ctrl+C untuk menghentikan.

### 7.5 Jalankan master di PC 1

```bash
python -m src.master --worker-ip 192.168.1.11 --port 5000 \
    --sizes 1000000 5000000 10000000 --mode both --shutdown-worker
```

Perintah di atas memakai 3 ukuran data default. Simpan `results.csv` dan tangkapan layar
terminal kedua PC untuk laporan.

### 7.6 Cara membaca hasil

| Istilah | Arti |
|---------|------|
| `T sequential` | waktu master menghitung seluruh data sendirian |
| `T distributed total` | waktu dari mulai kirim sampai hasil worker diterima (termasuk jaringan) |
| `Speedup` | `T_sequential / T_distributed`, ideal 2 |
| `Efficiency` | `Speedup / P x 100%` dengan `P = 2` |

`results.csv` berisi kolom: `size, load_pc1, load_pc2, master_compute_seconds,
worker_compute_seconds, distributed_seconds, sequential_seconds, speedup,
efficiency_percent`.

## 8. Opsi baris perintah

Worker (`python -m src.worker`):

| Opsi | Default | Arti |
|------|---------|------|
| `--host` | `0.0.0.0` | alamat yang didengarkan |
| `--port` | `5000` | port TCP |

Master (`python -m src.master`):

| Opsi | Default | Arti |
|------|---------|------|
| `--worker-ip` | wajib untuk mode `distributed`/`both` | IP PC 2 |
| `--port` | `5000` | port PC 2 |
| `--sizes` | `1000000 5000000 10000000` | satu atau lebih ukuran data |
| `--mode` | `both` | `distributed`, `sequential`, atau `both` |
| `--timeout` | `600` | batas detik operasi socket |
| `--shutdown-worker` | mati | kirim `SHUTDOWN` setelah semua uji selesai |

Konfigurasi lain (identitas, seed, rentang nilai, ukuran data default) ada di `src/config.py`.

## 9. Bila terjadi masalah

| Pesan / gejala | Penyebab | Solusi |
|----------------|----------|--------|
| `PC 2 menolak koneksi di 192.168.1.11:5000` | worker belum jalan atau port tidak sama | jalankan worker di PC 2, samakan `--port` |
| `Waktu habis menunggu ...` | port diblokir firewall, PC 2 mati, atau beda jaringan | buka inbound TCP port tersebut, nyalakan PC 2, cek `ping` |
| `ping` gagal | beda subnet / terhubung ke Wi-Fi berbeda | samakan jaringan, cek IP dengan `ipconfig` / `ip a` |
| Transfer data besar terputus | koneksi Wi-Fi tidak stabil | pakai kabel LAN, atau uji dengan ukuran lebih kecil dulu |
| `ModuleNotFoundError: No module named 'src'` | perintah dijalankan bukan dari root proyek | `cd` ke folder proyek, atau aktifkan venv lebih dulu |
| pytest tidak ditemukan | dependensi dev belum terpasang | `pip install -r requirements-dev.txt` |

## 10. Struktur folder

```
distributed-number-statistics/
├── AGENTS.md              spesifikasi dan aturan pengerjaan
├── PLAN.md                urutan fase kerja
├── README.md              dokumen ini
├── requirements-dev.txt   dependensi dev (pytest)
├── src/
│   ├── config.py          semua konstanta (identitas, port, ukuran data, seed)
│   ├── protocol.py        kemas/urai pesan socket (header JSON + payload bytes)
│   ├── stats.py           generate_data, split_data, compute_stats, merge_stats
│   ├── worker.py          program PC 2
│   ├── master.py          program PC 1 (mode distributed / sequential / both)
│   └── report.py          speedup, efficiency, format output, results.csv
├── tests/                 42 test: stats, protocol, report, integrasi worker+master
└── docs/DOKUMENTASI.md    penjelasan detail per fungsi, protokol, rumus
```

## 11. Ringkasan perintah (versi pendek)

```bash
# kedua PC
cd distributed-number-statistics
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# PC 2
python -m src.worker --host 0.0.0.0 --port 5000

# PC 1
python -m src.master --worker-ip 192.168.1.11 --port 5000 --sizes 1000000 5000000 10000000 --mode both

# satu mesin (validasi)
python -m src.worker --host 127.0.0.1 --port 5000 &
python -m src.master --worker-ip 127.0.0.1 --port 5000 --sizes 100000 500000 1000000

# test
python -m pytest -v
```
