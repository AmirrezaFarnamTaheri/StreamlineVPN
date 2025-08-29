from __future__ import annotations

import math
import hashlib
from typing import Iterable


class BloomFilter:
    """Simple Bloom filter without external dependencies.

    Uses k hash functions derived from SHA256 salting over a bit array.
    """

    def __init__(self, capacity: int = 1_000_000, error_rate: float = 0.01):
        self.capacity = max(1, int(capacity))
        self.error_rate = max(1e-6, float(error_rate))
        m = -capacity * math.log(self.error_rate) / (math.log(2) ** 2)
        k = (m / capacity) * math.log(2)
        self.m = int(m)  # number of bits
        self.k = max(1, int(k))
        self.bits = bytearray((self.m + 7) // 8)

    def _hashes(self, data: bytes) -> Iterable[int]:
        for i in range(self.k):
            h = hashlib.sha256(i.to_bytes(2, 'little') + data).digest()
            yield int.from_bytes(h[:8], 'little') % self.m

    def add(self, item: str) -> None:
        b = item.encode('utf-8', 'ignore')
        for idx in self._hashes(b):
            self.bits[idx >> 3] |= (1 << (idx & 7))

    def __contains__(self, item: str) -> bool:  # pragma: no cover
        b = item.encode('utf-8', 'ignore')
        for idx in self._hashes(b):
            if not (self.bits[idx >> 3] & (1 << (idx & 7))):
                return False
        return True

