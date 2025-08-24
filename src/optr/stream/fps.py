import math
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Final, Self

ConvertibleToFPS = int | float | tuple[int, int] | Fraction
NTSC: Final = ((24000, 1001), (30000, 1001), (60000, 1001), (120000, 1001))
NTSC_FLOATS: Final = zip(NTSC, tuple(n / d for n, d in NTSC), strict=False)


@lru_cache(maxsize=64)
def parse(value: ConvertibleToFPS) -> tuple[int, int]:
    match value:
        case bool():
            raise TypeError("bool is not a valid FPS")

        case int():
            if value <= 0:
                raise ValueError("FPS must be positive")
            return value, 1

        case float():
            if not (math.isfinite(value) and value > 0):
                raise ValueError("FPS float must be finite and positive")
            for (n, d), v in NTSC_FLOATS:
                if math.isclose(v, value, rel_tol=1e-8, abs_tol=1e-3):
                    return n, d
            f = Fraction.from_float(value).limit_denominator(1_000_000)
            return f.numerator, f.denominator

        case (int(n), int(d)):
            if n <= 0 or d <= 0:
                raise ValueError("FPS values must be positive")
            g = math.gcd(n, d)
            return n // g, d // g

        case Fraction():
            if value <= 0:
                raise ValueError("FPS must be positive")
            return value.numerator, value.denominator

        case _:
            raise TypeError(f"Unsupported FPS type: {type(value)}")


@dataclass(frozen=True, slots=True, init=False)
class FPS:
    num: int
    den: int

    def __init__(self, value: ConvertibleToFPS | Self, den: int | None = None):
        if den is not None:
            if not isinstance(value, int):
                raise TypeError("When den is provided, value must be int")
            n, d = value, den
        else:
            if isinstance(value, FPS):
                n, d = value.num, value.den
            else:
                n, d = parse(value)
        if n <= 0 or d <= 0:
            raise ValueError("FPS must be positive")
        g = math.gcd(n, d)
        object.__setattr__(self, "num", n // g)
        object.__setattr__(self, "den", d // g)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.num, self.den)

    @property
    def tuple(self) -> tuple[int, int]:
        return self.num, self.den

    def __float__(self) -> float:
        return self.num / self.den

    def __str__(self) -> str:
        return f"{self.num}/{self.den}"

    def __iter__(self):
        return iter([self.num, self.den])
