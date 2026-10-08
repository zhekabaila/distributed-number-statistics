"""Logika statistik: bangkitkan data, bagi, hitung parsial, gabungkan."""

import random
from array import array
from dataclasses import dataclass

from src import config


@dataclass
class PartialStats:
    """Hasil statistik parsial dari satu potongan data."""

    count: int
    total: int
    sum_squares: int
    minimum: int
    maximum: int


@dataclass
class FinalStats:
    """Hasil statistik akhir setelah penggabungan, siap lapor."""

    count: int
    total: int
    sum_squares: int
    minimum: int
    maximum: int
    mean: float
    std_dev: float


def generate_data(size: int, seed: int = config.RANDOM_SEED) -> array:
    """Bangkitkan `size` angka bulat acak deterministik pada rentang config."""
    rng = random.Random(seed)
    return array(
        config.ARRAY_TYPECODE,
        (rng.randint(config.VALUE_MIN, config.VALUE_MAX) for _ in range(size)),
    )


def split_data(data: array, parts: int = config.PROCESSORS) -> list[array]:
    """Bagi data menjadi `parts` potongan hampir rata, sisa masuk bagian terakhir."""
    step = len(data) // parts
    pieces = [
        data[index * step : (index + 1) * step] for index in range(parts - 1)
    ]
    pieces.append(data[(parts - 1) * step :])
    return pieces


def compute_stats(data: array) -> PartialStats:
    """Hitung statistik parsial dengan satu loop Python tanpa library numerik."""
    if len(data) == 0:
        return PartialStats(0, 0, 0, 0, 0)
    total = 0
    sum_squares = 0
    minimum = data[0]
    maximum = data[0]
    for value in data:
        if value < minimum:
            minimum = value
        if value > maximum:
            maximum = value
        total += value
        sum_squares += value * value
    return PartialStats(len(data), total, sum_squares, minimum, maximum)


def merge_stats(a: PartialStats, b: PartialStats) -> FinalStats:
    """Gabungkan dua hasil parsial lalu turunkan mean dan std_dev populasi."""
    count = a.count + b.count
    total = a.total + b.total
    sum_squares = a.sum_squares + b.sum_squares
    # Bagian kosong (count 0) punya min/max placeholder 0, jadi diabaikan.
    non_empty = [part for part in (a, b) if part.count]
    minimum = min(part.minimum for part in non_empty) if non_empty else 0
    maximum = max(part.maximum for part in non_empty) if non_empty else 0
    mean = total / count if count else 0.0
    # Varians populasi: E[x^2] - (E[x])^2, dihitung dari agregat agar bisa digabung.
    variance = sum_squares / count - mean * mean if count else 0.0
    return FinalStats(
        count=count,
        total=total,
        sum_squares=sum_squares,
        minimum=minimum,
        maximum=maximum,
        mean=mean,
        std_dev=variance**0.5,
    )
