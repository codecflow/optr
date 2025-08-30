import struct
import time
from multiprocessing import Process
from multiprocessing.shared_memory import SharedMemory

import pytest

from optr.core.ipc.sharedframe import SharedFrame


def _writer_counter(name: str, nbytes: int, count: int = 500):
    sf = SharedFrame.attach(name)
    try:
        for i in range(count):
            # Put i at both ends; middle zeros
            buf = bytearray(nbytes)
            struct.pack_into("<Q", buf, 0, i)
            struct.pack_into("<Q", buf, nbytes - 8, i)
            sf.write(buf)
    finally:
        sf.close()


def _reader_validate(name: str, nbytes: int, samples: int = 500):
    sf = SharedFrame.attach(name)
    try:
        prev = -1
        tmp = bytearray(nbytes)
        for _ in range(samples):
            sf.read(tmp)
            head = struct.unpack_from("<Q", tmp, 0)[0]
            tail = struct.unpack_from("<Q", tmp, nbytes - 8)[0]
            assert head == tail, "Frame torn (head != tail)"
            assert head >= prev, "Sequence decreased"
            prev = head
    finally:
        sf.close()


def test_create_roundtrip_basic():
    nbytes = 256
    with SharedFrame.create(nbytes) as sf:
        assert sf.nbytes == nbytes
        b1 = bytes([7]) * nbytes
        dst = bytearray(nbytes)

        sf.write(b1)
        result = sf.read(dst)
        assert result is dst
        assert bytes(dst) == b1

        b2 = bytes([123]) * nbytes
        sf.write(b2)
        result = sf.read(dst)
        assert result is dst
        assert bytes(dst) == b2


def test_read_bytes_convenience():
    nbytes = 64
    with SharedFrame.create(nbytes) as sf:
        payload = bytes([42]) * nbytes
        sf.write(payload)
        snap = sf.read()
        assert snap == payload
        assert isinstance(snap, bytearray)


def test_read_into_requires_writable():
    nbytes = 32
    with SharedFrame.create(nbytes) as sf:
        with pytest.raises(ValueError):
            sf.read(bytes(nbytes))  # readonly


def test_attach_size_validation_and_magic():
    nbytes = 128
    sf = SharedFrame.create(nbytes)
    try:
        # Attaching with wrong nbytes should error because header carries size.
        with pytest.raises(ValueError):
            SharedFrame.attach(sf.name, nbytes=nbytes * 2)

        # Attaching without specifying nbytes uses header value
        sf2 = SharedFrame.attach(sf.name)
        try:
            assert sf2.nbytes == nbytes
        finally:
            sf2.close()
    finally:
        # Clean
        name = sf.name
        sf.close()
        sf.unlink()
        # Ensure unlink did not break attach
        with pytest.raises(FileNotFoundError):
            SharedMemory(name=name, create=False)


def test_try_read_timeout_when_writer_odd_seq():
    nbytes = 64
    sf = SharedFrame.create(nbytes)
    try:
        # Force odd seq (simulate writer in progress)
        seq, _ = sf._read_seq_idx()
        sf._write_seq(seq | 1)

        dst = bytearray(nbytes)
        with pytest.raises(TimeoutError):
            sf.read(dst, timeout=0.02)
    finally:
        # restore even seq to avoid hang in close scenarios
        seq, _ = sf._read_seq_idx()
        if seq & 1:
            sf._write_seq(seq + 1)
        sf.close()
        sf.unlink()


def test_multiprocess_writer_reader():
    nbytes = 128
    sf = SharedFrame.create(nbytes)
    try:
        name = sf.name
        writer = Process(target=_writer_counter, args=(name, nbytes, 600))
        reader = Process(target=_reader_validate, args=(name, nbytes, 400))
        writer.start()
        reader.start()
        writer.join(timeout=5)
        reader.join(timeout=5)
        assert writer.exitcode == 0
        assert reader.exitcode == 0
    finally:
        sf.close()
        sf.unlink()


# Additional critical test cases


def test_zero_size_buffer_error():
    """Test that zero-size buffer raises appropriate error."""
    with pytest.raises(ValueError, match="nbytes required"):
        SharedFrame.create(0)


def test_minimum_viable_size():
    """Test with minimum viable size (1 byte)."""
    with SharedFrame.create(1) as sf:
        assert sf.nbytes == 1
        sf.write(b"\x42")
        result = sf.read()
        assert result == bytearray(b"\x42")


def test_invalid_magic_number():
    """Test behavior when magic number is corrupted."""
    nbytes = 64
    sf = SharedFrame.create(nbytes)
    try:
        name = sf.name
        # Corrupt magic number
        struct.pack_into("<Q", sf._hdr_magic, 0, 0xDEADBEEF)
        sf.close()

        # Attempt to attach should fail
        with pytest.raises(ValueError, match="Invalid SharedFrame magic"):
            SharedFrame.attach(name)
    finally:
        sf.unlink()


def test_version_mismatch():
    """Test version incompatibility handling."""
    nbytes = 64
    sf = SharedFrame.create(nbytes)
    try:
        name = sf.name
        # Set unsupported version
        struct.pack_into("<Q", sf._hdr_ver, 0, 999)
        sf.close()

        # Attempt to attach should fail
        with pytest.raises(ValueError, match="Unsupported version"):
            SharedFrame.attach(name)
    finally:
        sf.unlink()


def test_double_close_unlink():
    """Test calling close() and unlink() multiple times."""
    nbytes = 32
    sf = SharedFrame.create(nbytes)

    # Multiple closes should not error
    sf.close()
    sf.close()

    # Multiple unlinks should not error
    sf.unlink()
    sf.unlink()  # Should handle FileNotFoundError gracefully


def test_large_buffer_stress():
    """Test with large buffer to verify memory handling."""
    nbytes = 1024 * 1024  # 1MB
    with SharedFrame.create(nbytes) as sf:
        assert sf.nbytes == nbytes

        # Create pattern data
        pattern = bytes(range(256)) * (nbytes // 256)
        if len(pattern) < nbytes:
            pattern += bytes(range(nbytes - len(pattern)))

        sf.write(pattern)
        result = sf.read()
        assert bytes(result) == pattern


def test_crash_recovery_odd_seq():
    """Test attaching to segment left in odd seq state (simulated crash)."""
    nbytes = 64
    sf = SharedFrame.create(nbytes)
    try:
        name = sf.name

        # Write some data first
        sf.write(b"A" * nbytes)

        # Force odd seq (simulate writer crash mid-write)
        seq, _ = sf._read_seq_idx()
        sf._write_seq(seq | 1)
        sf.close()

        # Attach should work, but reads should timeout quickly
        sf2 = SharedFrame.attach(name)
        try:
            with pytest.raises(TimeoutError):
                sf2.read(timeout=0.01)
        finally:
            # Clean up odd seq for proper cleanup
            seq, _ = sf2._read_seq_idx()
            if seq & 1:
                sf2._write_seq(seq + 1)
            sf2.close()
    finally:
        sf.unlink()


def test_buffer_type_compatibility():
    """Test writing different buffer types."""
    nbytes = 32
    with SharedFrame.create(nbytes) as sf:
        # Test bytes
        data_bytes = bytes([1, 2, 3] * (nbytes // 3) + [1] * (nbytes % 3))
        sf.write(data_bytes)
        result1 = sf.read()
        assert bytes(result1) == data_bytes

        # Test bytearray
        data_bytearray = bytearray([4, 5, 6] * (nbytes // 3) + [4] * (nbytes % 3))
        sf.write(data_bytearray)
        result2 = sf.read()
        assert bytes(result2) == bytes(data_bytearray)

        # Test memoryview
        data_mv = memoryview(bytearray([7, 8, 9] * (nbytes // 3) + [7] * (nbytes % 3)))
        sf.write(data_mv)
        result3 = sf.read()
        assert bytes(result3) == bytes(data_mv)


def test_wrong_size_write():
    """Test writing buffer of wrong size."""
    nbytes = 64
    with SharedFrame.create(nbytes) as sf:
        # Too small
        with pytest.raises(ValueError, match="src length"):
            sf.write(b"A" * (nbytes - 1))

        # Too large
        with pytest.raises(ValueError, match="src length"):
            sf.write(b"A" * (nbytes + 1))


def test_wrong_size_read_buffer():
    """Test reading into buffer of wrong size."""
    nbytes = 64
    with SharedFrame.create(nbytes) as sf:
        sf.write(b"A" * nbytes)

        # Too small
        with pytest.raises(ValueError, match="dst length"):
            sf.read(bytearray(nbytes - 1))

        # Too large
        with pytest.raises(ValueError, match="dst length"):
            sf.read(bytearray(nbytes + 1))


def _multiple_readers(name: str, nbytes: int, samples: int = 100):
    """Helper for testing multiple concurrent readers."""
    sf = SharedFrame.attach(name)
    try:
        dst = bytearray(nbytes)
        for _ in range(samples):
            sf.read(dst)
            # Verify data integrity (all bytes should be same value)
            first_byte = dst[0]
            assert all(b == first_byte for b in dst), "Data corruption detected"
    finally:
        sf.close()


def test_multiple_concurrent_readers():
    """Test multiple readers don't interfere with each other."""
    nbytes = 128
    sf = SharedFrame.create(nbytes)
    try:
        name = sf.name

        # Write initial data
        sf.write(bytes([42]) * nbytes)

        # Start multiple readers
        readers = []
        for _ in range(5):
            p = Process(target=_multiple_readers, args=(name, nbytes, 50))
            readers.append(p)
            p.start()

        # Keep writing while readers are active
        for i in range(100):
            sf.write(bytes([i % 256]) * nbytes)
            time.sleep(0.001)  # Small delay

        # Wait for all readers
        for p in readers:
            p.join(timeout=3)
            assert p.exitcode == 0

    finally:
        sf.close()
        sf.unlink()


def test_header_alignment():
    """Verify header is cache-line aligned (64 bytes)."""
    assert SharedFrame.HEADER_BYTES == 64, (
        "Header should be 64 bytes for cache alignment"
    )

    # Verify struct format matches expected size
    expected_fields = (
        8  # magic, version, nbytes, seq, idx, reserved1, reserved2, reserved3
    )
    assert SharedFrame.HEADER_FORMAT == "<" + "Q" * expected_fields
    assert struct.calcsize(SharedFrame.HEADER_FORMAT) == 64
