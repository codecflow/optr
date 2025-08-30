from __future__ import annotations

import struct
import time
from multiprocessing.shared_memory import SharedMemory

BytesLike = bytes | bytearray | memoryview

# Header layout (little-endian, uint64) - 64 bytes (cache-line aligned):
#   [0] MAGIC
#   [1] VERSION
#   [2] NBYTES
#   [3] SEQ        (even -> stable, odd -> writing)
#   [4] ACTIVE_IDX {0,1}
#   [5] RESERVED1  (future use)
#   [6] RESERVED2  (future use)
#   [7] RESERVED3  (future use)


class SharedFrame:
    """
    Lock-free shared memory with dual-frame buffering (single-writer, multi-reader).

    Uses seqlock pattern: seq odd during writes, even when stable.
    Writer alternates between two frames while readers get consistent snapshots.
    """

    # Class constants
    MAGIC = int.from_bytes(b"SHFRAME\x00", "little")  # 8 ascii bytes
    VERSION = 1
    HEADER_FORMAT = "<QQQQQQQQ"
    HEADER_BYTES = struct.calcsize(HEADER_FORMAT)  # 64
    SPIN_YIELD_EVERY = 16384

    def __init__(self, shm: SharedMemory, nbytes: int | None = None):
        self.shm = shm
        self._buf = memoryview(shm.buf)

        if len(self._buf) < self.HEADER_BYTES:
            raise ValueError(
                f"SharedMemory too small: {len(self._buf)} < {self.HEADER_BYTES}"
            )

        # Header views
        self._hdr_view = self._buf[: self.HEADER_BYTES]
        self._hdr_magic = self._hdr_view[0:8]
        self._hdr_ver = self._hdr_view[8:16]
        self._hdr_nbytes = self._hdr_view[16:24]
        self._hdr_seq = self._hdr_view[24:32]
        self._hdr_idx = self._hdr_view[32:40]

        # Read and validate header - inline for one-time use
        magic = struct.unpack("<Q", self._hdr_magic)[0]
        version = struct.unpack("<Q", self._hdr_ver)[0]
        h_nbytes = struct.unpack("<Q", self._hdr_nbytes)[0]
        seq, idx = self._read_seq_idx()

        if magic == 0 and version == 0 and h_nbytes == 0:
            # Initialize new segment
            if nbytes is None or nbytes <= 0:
                raise ValueError("nbytes required for initialization")

            expected = self.HEADER_BYTES + 2 * nbytes
            if len(self._buf) < expected:
                raise ValueError(
                    f"SharedMemory size {len(self._buf)} < expected {expected}"
                )

            # Zero frames
            f0 = self._buf[self.HEADER_BYTES : self.HEADER_BYTES + nbytes]
            f1 = self._buf[self.HEADER_BYTES + nbytes : self.HEADER_BYTES + 2 * nbytes]
            f0[:] = b"\x00" * nbytes
            f1[:] = b"\x00" * nbytes

            # Initialize header: idx first, then seq, then identity
            self._write_idx(0)
            self._write_seq(0)
            struct.pack_into("<Q", self._hdr_magic, 0, self.MAGIC)
            struct.pack_into("<Q", self._hdr_ver, 0, self.VERSION)
            struct.pack_into("<Q", self._hdr_nbytes, 0, nbytes)

            self.nbytes = nbytes
        else:
            # Validate existing segment
            if magic != self.MAGIC:
                raise ValueError("Invalid SharedFrame magic number")
            if version != self.VERSION:
                raise ValueError(
                    f"Unsupported version {version}, expected {self.VERSION}"
                )
            if h_nbytes <= 0:
                raise ValueError("Invalid nbytes in header")
            if nbytes is not None and nbytes != h_nbytes:
                raise ValueError(
                    f"nbytes mismatch: header={h_nbytes}, requested={nbytes}"
                )

            self.nbytes = h_nbytes

        # Create frame views
        off = self.HEADER_BYTES
        self._f0 = self._buf[off : off + self.nbytes]
        self._f1 = self._buf[off + self.nbytes : off + 2 * self.nbytes]

    def _read_seq_idx(self) -> tuple[int, int]:
        """Read synchronization fields (seq, idx) from header."""
        return (
            struct.unpack("<Q", self._hdr_seq)[0],
            struct.unpack("<Q", self._hdr_idx)[0],
        )

    def _write_seq(self, seq: int) -> None:
        struct.pack_into("<Q", self._hdr_seq, 0, seq)

    def _write_idx(self, idx: int) -> None:
        struct.pack_into("<Q", self._hdr_idx, 0, idx)

    def write(self, src: BytesLike) -> None:
        """Write data to inactive frame and flip active index."""
        src_mv = memoryview(src)
        if src_mv.nbytes != self.nbytes:
            raise ValueError(f"src length {src_mv.nbytes} != nbytes {self.nbytes}")

        seq, active_idx = self._read_seq_idx()
        next_idx = 1 - active_idx

        # Signal write in progress (odd seq)
        self._write_seq(seq + 1)

        # Copy to inactive frame
        dst = self._f1 if next_idx == 1 else self._f0
        dst[:] = src_mv

        # Publish: idx first, then seq even
        self._write_idx(next_idx)
        self._write_seq(seq + 2)

    def read(
        self, dst: BytesLike | None = None, timeout: float | None = None
    ) -> BytesLike:
        """
        Read stable snapshot into dst buffer.
        If dst is None, creates and returns a new bytearray.
        Always returns the destination buffer.
        """
        # Create dst if not provided
        if dst is None:
            dst = bytearray(self.nbytes)

        # Validate dst
        dst_mv = memoryview(dst)
        if dst_mv.nbytes != self.nbytes:
            raise ValueError(f"dst length {dst_mv.nbytes} != nbytes {self.nbytes}")
        if getattr(dst_mv, "readonly", False):
            raise ValueError("dst must be writable")

        deadline = None if timeout is None else time.monotonic() + timeout
        spins = 0

        while True:
            s1, idx = self._read_seq_idx()

            if s1 & 1:  # Writer in progress
                spins += 1
                if spins % self.SPIN_YIELD_EVERY == 0:
                    time.sleep(0)
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError("Read timeout: writer in progress")
                continue

            # Copy from active frame
            src = self._f1 if idx == 1 else self._f0
            dst_mv[:] = src

            # Verify no write occurred during copy
            s2, _ = self._read_seq_idx()
            if s1 == s2 and (s2 & 1) == 0:
                return dst

            spins += 1
            if spins % self.SPIN_YIELD_EVERY == 0:
                time.sleep(0)
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("Read timeout: no stable snapshot")

    @property
    def name(self) -> str:
        return self.shm.name

    @staticmethod
    def create(nbytes: int, name: str | None = None) -> SharedFrame:
        """Create new SharedFrame with specified size."""
        total_bytes = SharedFrame.HEADER_BYTES + 2 * nbytes
        shm = SharedMemory(create=True, size=total_bytes, name=name)
        return SharedFrame(shm, nbytes)

    @staticmethod
    def attach(name: str, nbytes: int | None = None) -> SharedFrame:
        """Attach to existing SharedFrame. nbytes taken from header if not provided."""
        shm = SharedMemory(name=name, create=False)
        return SharedFrame(shm, nbytes)

    def __enter__(self) -> SharedFrame:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Close shared memory (does not unlink)."""
        # Release memoryviews to avoid BufferError
        for mv in (
            self._f0,
            self._f1,
            self._hdr_magic,
            self._hdr_ver,
            self._hdr_nbytes,
            self._hdr_seq,
            self._hdr_idx,
            self._hdr_view,
            self._buf,
        ):
            try:
                mv.release()
            except Exception:
                pass
        self.shm.close()

    def unlink(self) -> None:
        """Destroy shared memory segment."""
        try:
            self.shm.unlink()
        except FileNotFoundError:
            pass
