"""
Scanner-specific type definitions
"""

from dataclasses import dataclass
from enum import Enum


class CoordinateFrame(Enum):
    """Coordinate frame reference systems"""

    SCREEN = "screen"
    WINDOW = "window"
    ELEMENT = "element"


@dataclass
class Point:
    """2D point with coordinate frame"""

    x: float
    y: float
    frame: CoordinateFrame = CoordinateFrame.SCREEN


@dataclass
class BoundingBox:
    """Rectangular bounding box"""

    x: int
    y: int
    width: int
    height: int
    frame: CoordinateFrame = CoordinateFrame.SCREEN

    @property
    def center(self) -> Point:
        """Get center point of bounding box"""
        return Point(
            x=self.x + self.width // 2, y=self.y + self.height // 2, frame=self.frame
        )
