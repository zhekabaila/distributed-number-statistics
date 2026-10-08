"""Test logika statistik pada src/stats.py."""

import pytest
from array import array

from src import config, stats


def test_generate_data_has_correct_size_and_range():
    """Data bangkitan punya jumlah elemen dan rentang nilai sesuai config."""
    data = stats.generate_data(1000)
    assert len(data) == 1000
    assert all(config.VALUE_MIN <= v <= config.VALUE_MAX for v in data)


def test_generate_data_is_deterministic():
    """Seed yang sama menghasilkan data yang sama persis."""
    assert list(stats.generate_data(500, seed=7)) == list(
        stats.generate_data(500, seed=7)
    )


def test_split_data_even_size():
    """Ukuran genap terbagi rata tanpa sisa."""
    data = stats.generate_data(100)
    parts = stats.split_data(data)
    assert [len(p) for p in parts] == [50, 50]
    assert sum(len(p) for p in parts) == len(data)


def test_split_data_odd_size_remainder_goes_to_last_part():
    """Sisa pembagian masuk ke bagian terakhir."""
    data = stats.generate_data(11)
    parts = stats.split_data(data)
    assert [len(p) for p in parts] == [5, 6]


@pytest.mark.parametrize("size", [0, 1, 2, 3])
def test_split_data_keeps_total_for_small_sizes(size):
    """Total elemen tetap sama dan data utuh tersusun dari potongan."""
    data = stats.generate_data(size)
    parts = stats.split_data(data)
    assert len(parts) == config.PROCESSORS
    assert sum(len(p) for p in parts) == size
    assert list(data) == [v for part in parts for v in part]


def test_compute_stats_known_values():
    """Statistik parsial cocok dengan hitungan manual."""
    result = stats.compute_stats(array("i", [2, 4, 6, 8]))
    assert result.count == 4
    assert result.total == 20
    assert result.sum_squares == 4 + 16 + 36 + 64
    assert result.minimum == 2
    assert result.maximum == 8


def test_compute_stats_empty_data():
    """Data kosong menghasilkan count nol tanpa error."""
    result = stats.compute_stats(array("i"))
    assert result.count == 0
    assert result.total == 0
    assert result.minimum == 0
    assert result.maximum == 0


def test_compute_stats_single_element():
    """Satu elemen menjadi min sekaligus max."""
    result = stats.compute_stats(array("i", [9]))
    assert result.count == 1
    assert result.total == 9
    assert result.minimum == 9
    assert result.maximum == 9


def test_merge_stats_equals_full_computation():
    """Gabungan hasil parsial sama dengan hasil pada data utuh."""
    data = stats.generate_data(5000)
    parts = stats.split_data(data)
    merged = stats.merge_stats(
        stats.compute_stats(parts[0]), stats.compute_stats(parts[1])
    )
    full = stats.compute_stats(data)
    assert merged.count == full.count
    assert merged.total == full.total
    assert merged.sum_squares == full.sum_squares
    assert merged.minimum == full.minimum
    assert merged.maximum == full.maximum
    expected_mean = full.total / full.count
    assert merged.mean == pytest.approx(expected_mean)
    expected_std = (full.sum_squares / full.count - expected_mean**2) ** 0.5
    assert merged.std_dev == pytest.approx(expected_std, rel=1e-9)


def test_merge_stats_with_empty_part():
    """Bagian kosong tidak mengubah hasil gabungan."""
    data = stats.generate_data(100)
    one = stats.compute_stats(data)
    empty = stats.compute_stats(array("i"))
    merged = stats.merge_stats(one, empty)
    assert merged.count == one.count
    assert merged.total == one.total
    assert merged.minimum == one.minimum
    assert merged.maximum == one.maximum
    assert merged.mean == pytest.approx(one.total / one.count)


def test_merge_stats_both_empty():
    """Dua bagian kosong menghasilkan statistik nol tanpa pembagian nol."""
    empty = stats.compute_stats(array("i"))
    merged = stats.merge_stats(empty, empty)
    assert merged.count == 0
    assert merged.mean == 0.0
    assert merged.std_dev == 0.0
