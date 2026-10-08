"""Konstanta konfigurasi aplikasi. Satu-satunya tempat angka dan identitas proyek."""

# Identitas mahasiswa (dipakai banner laporan, jangan di-hardcode di file lain).
NPM = "247006111152"
STUDENT_NAME = "Zheka Baila Arkan"

# Jaringan.
DEFAULT_PORT = 5000
DEFAULT_HOST = "0.0.0.0"
SOCKET_TIMEOUT_SECONDS = 600.0
LISTENER_BACKLOG = 5

# Ukuran data untuk uji default (jumlah elemen).
DEFAULT_SIZES = (1_000_000, 5_000_000, 10_000_000)

# Pembangkitan data acak.
RANDOM_SEED = 42
VALUE_MIN = 1
VALUE_MAX = 1000

# Jumlah prosessor (PC) pada perhitungan efficiency.
PROCESSORS = 2

# Serialisasi data angka: array bertipe 'i' (int 32 bit) lalu .tobytes().
ARRAY_TYPECODE = "i"

# Protokol pesan: [4 byte panjang header][4 byte panjang payload] big-endian.
HEADER_STRUCT_FORMAT = "!II"
RECV_CHUNK_BYTES = 65536
MAX_HEADER_BYTES = 1_048_576

# Tipe pesan.
MSG_TASK = "TASK"
MSG_RESULT = "RESULT"
MSG_SHUTDOWN = "SHUTDOWN"

# Format output.
SEPARATOR_WIDTH = 60
SUMMARY_COLUMNS = ("Size", "T sequential", "T distributed", "Speedup", "Efficiency")
SUMMARY_COLUMN_WIDTHS = (12, 13, 14, 8, 10)
RESULT_CSV_FILENAME = "results.csv"
CSV_HEADER = (
    "size",
    "load_pc1",
    "load_pc2",
    "master_compute_seconds",
    "worker_compute_seconds",
    "distributed_seconds",
    "sequential_seconds",
    "speedup",
    "efficiency_percent",
)
