"""Тесты device/virtual/max30102.py: VirtualMax30102 — инициализация,
пополнение FIFO, переполнение, разбор FIFO_DATA, пустая очередь, SHDN,
PART_ID, немоделируемые регистры (задача PI-03).

Важный нюанс реализации (см. комментарий в `max30102.py` у
`read_byte_data`/`_REG_FIFO_WR_PTR`): чтение `FIFO_WR_PTR` возвращает
значение указателя ДО попытки пополнения этим же чтением (иначе самый
первый читатель на свежем чипе увидел бы уже продвинутый указатель, что
нарушило бы требование "только что созданный чип -> все указатели
равны 0"). Пополнение всё равно происходит при каждом чтении —
эффект виден на следующем чтении WR_PTR/FIFO_DATA. Тесты ниже написаны с
учётом этого контракта.
"""

from __future__ import annotations

import itertools

from device.virtual.max30102 import VirtualMax30102

_INT_STATUS_UNMODELED = 0x00
_FIFO_WR_PTR = 0x04
_OVF_COUNTER = 0x05
_FIFO_RD_PTR = 0x06
_FIFO_DATA = 0x07
_MODE_CONFIG = 0x09
_PART_ID = 0xFF

_SHDN_BIT = 0x80
_FIFO_DEPTH = 32


def _bytes_for_sample(red: int, ir: int) -> list[int]:
    """6 байт отсчёта в ожидаемом (провизорном) порядке: RED, затем IR,
    big-endian, 18 бит значимых (порядок каналов провизорный, см.
    комментарии у `_BYTES_PER_CHANNEL` в `max30102.py`).
    """
    result: list[int] = []
    for value in (red, ir):
        masked = value & 0x03FFFF
        result.append((masked >> 16) & 0xFF)
        result.append((masked >> 8) & 0xFF)
        result.append(masked & 0xFF)
    return result


def test_initial_state_is_all_zero():
    chip = VirtualMax30102(itertools.repeat((100, 200)))

    assert chip.read_byte_data(_FIFO_WR_PTR) == 0
    assert chip.read_byte_data(_FIFO_RD_PTR) == 0
    assert chip.read_byte_data(_OVF_COUNTER) == 0
    assert chip.read_byte_data(_MODE_CONFIG) == 0


def test_part_id_is_fixed_regardless_of_state():
    chip = VirtualMax30102(itertools.repeat((100, 200)))

    assert chip.read_byte_data(_PART_ID) == 0x15

    chip.write_byte_data(_MODE_CONFIG, _SHDN_BIT)

    assert chip.read_byte_data(_PART_ID) == 0x15


def test_reading_fifo_wr_ptr_enqueues_one_sample_visible_on_next_read():
    chip = VirtualMax30102(itertools.repeat((111, 222)))

    chip.read_byte_data(_FIFO_WR_PTR)  # пополнение: один отсчёт поставлен в очередь

    # Эффект пополнения виден на следующем чтении WR_PTR (указатель
    # продвинулся на 1) — см. контракт "возвращается значение ДО
    # попытки пополнения" в docstring модуля этого файла.
    assert chip.read_byte_data(_FIFO_WR_PTR) == 1
    assert chip.read_byte_data(_FIFO_RD_PTR) == 0


def test_fifo_data_round_trips_one_sample_and_advances_rd_ptr():
    red, ir = 123456, 654321
    chip = VirtualMax30102(itertools.repeat((ir, red)))

    chip.read_byte_data(_FIFO_WR_PTR)  # пополнение: один отсчёт в очереди

    bytes_read = [chip.read_byte_data(_FIFO_DATA) for _ in range(6)]

    assert bytes_read == _bytes_for_sample(red, ir)
    assert chip.read_byte_data(_FIFO_RD_PTR) == 1


def test_fifo_data_on_empty_queue_returns_zero():
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    assert chip.read_byte_data(_FIFO_DATA) == 0


def test_overflow_after_32_unread_samples_drops_sample_and_increments_ovf_counter():
    # Источник бесконечный и невырожденный -- какие именно (ir, red) идут в
    # очередь, здесь не важно, важно только число пополнений.
    chip = VirtualMax30102((i, i + 1) for i in itertools.count())

    for _ in range(_FIFO_DEPTH):
        chip.read_byte_data(_FIFO_WR_PTR)  # 32 успешных пополнения, FIFO полон

    assert chip.read_byte_data(_OVF_COUNTER) == 0

    # 33-е чтение WR_PTR: пополнение отбрасывается, OVF_COUNTER растёт.
    chip.read_byte_data(_FIFO_WR_PTR)

    assert chip.read_byte_data(_OVF_COUNTER) == 1

    # WR_PTR не продвинулся на отброшенной попытке: после 32 пополнений
    # указатель равен 32 % 32 == 0, и остаётся 0 после отброшенной попытки.
    # ПРЕДУПРЕЖДЕНИЕ: это чтение FIFO_WR_PTR само по себе -- 34-я попытка
    # пополнения (очередь всё ещё полна), поэтому оно тоже отбрасывает
    # отсчёт и снова увеличивает OVF_COUNTER (станет 2) как побочный эффект
    # этой проверки. OVF_COUNTER не "застывает" на 1 после этого теста --
    # 1 проверяется только сразу после 33-го чтения выше, до этой строки.
    assert chip.read_byte_data(_FIFO_WR_PTR) == 0


def test_ovf_counter_saturates_at_15_and_does_not_wrap():
    chip = VirtualMax30102((i, i + 1) for i in itertools.count())

    for _ in range(_FIFO_DEPTH):
        chip.read_byte_data(_FIFO_WR_PTR)  # заполнить очередь полностью

    for _ in range(50):  # намного больше, чем нужно для насыщения на 15
        chip.read_byte_data(_FIFO_WR_PTR)

    assert chip.read_byte_data(_OVF_COUNTER) == 15


def test_shdn_blocks_fifo_refill():
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    chip.write_byte_data(_MODE_CONFIG, _SHDN_BIT)
    chip.read_byte_data(_FIFO_WR_PTR)  # попытка пополнения -- должна быть проигнорирована

    assert chip.read_byte_data(_FIFO_WR_PTR) == 0
    assert chip.read_byte_data(_FIFO_DATA) == 0  # очередь так и не пополнилась


def test_exhausted_source_leaves_state_unchanged_without_raising():
    chip = VirtualMax30102(iter([(1, 2)]))

    chip.read_byte_data(_FIFO_WR_PTR)  # consumes the only sample, wr_ptr -> 1

    # Source is now exhausted. Reading FIFO_WR_PTR again must not raise
    # StopIteration, must not drop the queued sample, and must not touch
    # OVF_COUNTER -- refill is simply a no-op this time.
    wr_ptr = chip.read_byte_data(_FIFO_WR_PTR)

    assert wr_ptr == 1
    assert chip.read_byte_data(_FIFO_WR_PTR) == 1
    assert chip.read_byte_data(_OVF_COUNTER) == 0


def test_unmodeled_register_reads_zero_and_write_is_ignored():
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    chip.write_byte_data(_INT_STATUS_UNMODELED, 0xFF)  # не должно падать

    assert chip.read_byte_data(_INT_STATUS_UNMODELED) == 0


def test_block_read_of_contiguous_fifo_status_registers():
    # FIFO_WR_PTR (0x04), OVF_COUNTER (0x05), FIFO_RD_PTR (0x06) идут подряд
    # -- стандартный паттерн драйвера: прочитать все три одной блочной
    # транзакцией вместо трёх отдельных read_byte_data. Регрессионный тест
    # на баг, который был найден до ревью: read_i2c_block_data раньше читал
    # один и тот же reg `length` раз вместо `length` последовательных
    # адресов (reg, reg+1, reg+2, ...).
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    chip.read_byte_data(_FIFO_WR_PTR)  # пополнение: WR_PTR станет 1

    block = chip.read_i2c_block_data(_FIFO_WR_PTR, 3)

    # block[0] = FIFO_WR_PTR (это же чтение заодно пополняет очередь ещё
    # раз -- тот же контракт, что и у прямого read_byte_data(FIFO_WR_PTR)),
    # block[1] = OVF_COUNTER, block[2] = FIFO_RD_PTR -- три РАЗНЫХ регистра,
    # а не три повтора одного и того же значения.
    assert block == [1, 0, 0]


def test_direct_write_to_fifo_wr_ptr_sets_value_masked_to_5_bits():
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    chip.write_byte_data(_FIFO_WR_PTR, 0xFF)

    assert chip.read_byte_data(_FIFO_WR_PTR) == 0x1F


def test_direct_write_to_fifo_rd_ptr_sets_value_masked_to_5_bits():
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    chip.write_byte_data(_FIFO_RD_PTR, 0xFF)

    assert chip.read_byte_data(_FIFO_RD_PTR) == 0x1F


def test_direct_write_to_ovf_counter_sets_value_masked_to_4_bits():
    chip = VirtualMax30102(itertools.repeat((1, 2)))

    chip.write_byte_data(_OVF_COUNTER, 0xFF)

    assert chip.read_byte_data(_OVF_COUNTER) == 0x0F


def test_clearing_shdn_resumes_fifo_refill():
    chip = VirtualMax30102(itertools.repeat((111, 222)))

    chip.write_byte_data(_MODE_CONFIG, _SHDN_BIT)
    chip.read_byte_data(_FIFO_WR_PTR)  # пополнение заблокировано SHDN=1
    assert chip.read_byte_data(_FIFO_WR_PTR) == 0

    chip.write_byte_data(_MODE_CONFIG, 0x00)  # SHDN снова 0
    chip.read_byte_data(_FIFO_WR_PTR)  # теперь пополнение должно пройти

    assert chip.read_byte_data(_FIFO_WR_PTR) == 1


def test_shdn_does_not_block_draining_already_buffered_samples():
    chip = VirtualMax30102(itertools.repeat((111, 222)))

    chip.read_byte_data(_FIFO_WR_PTR)  # один отсчёт уже в очереди, SHDN=0

    chip.write_byte_data(_MODE_CONFIG, _SHDN_BIT)  # выключаем чип ПОСЛЕ пополнения

    # SHDN гейтит только _maybe_enqueue (попытку пополнения); вычитывание
    # уже накопленных отсчётов через FIFO_DATA не должно быть заблокировано.
    bytes_read = [chip.read_byte_data(_FIFO_DATA) for _ in range(6)]

    assert bytes_read != [0, 0, 0, 0, 0, 0]
    assert chip.read_byte_data(_FIFO_RD_PTR) == 1


def test_fifo_data_byte_order_matches_hand_computed_sequence():
    # Независимая от _bytes_for_sample/_encode_sample проверка: байты
    # посчитаны вручную для конкретной пары (red, ir), чтобы общая ошибка
    # в порядке байт/маскировании в производственном коде и в тестовом
    # хелпере не осталась незамеченной round-trip-тестом (который использует
    # тот же алгоритм с обеих сторон).
    #
    # red = 0x010203 = 66051, ir = 0x030405 = 197637 -- оба заведомо меньше
    # 0x40000 (18-битный максимум + 1), т.е. маскирование на 18 бит их не
    # меняет. Ожидаем big-endian по 3 байта на канал, RED, затем IR:
    # [0x01, 0x02, 0x03, 0x03, 0x04, 0x05].
    red = 0x010203
    ir = 0x030405
    chip = VirtualMax30102(itertools.repeat((ir, red)))

    chip.read_byte_data(_FIFO_WR_PTR)  # пополнение: один отсчёт в очереди
    bytes_read = [chip.read_byte_data(_FIFO_DATA) for _ in range(6)]

    assert bytes_read == [0x01, 0x02, 0x03, 0x03, 0x04, 0x05]
