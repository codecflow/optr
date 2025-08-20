"""
Tests for MuJoCo camera utilities
"""

from unittest.mock import Mock

import pytest

from .camera import Camera, find, list, resolve


class MockModel:
    """Mock MuJoCo model for testing."""

    def __init__(self, cameras):
        """Initialize with list of camera names."""
        self.cameras = cameras
        self.ncam = len(cameras)

    def cam(self, index):
        """Return mock camera object."""
        if 0 <= index < len(self.cameras):
            mock_cam = Mock()
            mock_cam.name = self.cameras[index]
            return mock_cam
        raise IndexError("Camera index out of range")


def test_camera_namedtuple():
    """Test Camera namedtuple creation."""
    camera = Camera(id=0, name="front_camera")
    assert camera.id == 0
    assert camera.name == "front_camera"


def test_list_cameras():
    """Test listing all cameras in model."""
    model = MockModel(["front", "back", "side"])
    cameras = list(model)

    assert len(cameras) == 3
    assert cameras[0] == Camera(id=0, name="front")
    assert cameras[1] == Camera(id=1, name="back")
    assert cameras[2] == Camera(id=2, name="side")


def test_list_empty_cameras():
    """Test listing cameras when model has none."""
    model = MockModel([])
    cameras = list(model)
    assert len(cameras) == 0


def test_find_existing_camera():
    """Test finding camera by name."""
    model = MockModel(["front", "back", "side"])
    
    assert find(model, "front") == 0
    assert find(model, "back") == 1
    assert find(model, "side") == 2


def test_find_nonexistent_camera():
    """Test finding camera that doesn't exist."""
    model = MockModel(["front", "back"])
    
    assert find(model, "nonexistent") is None
    assert find(model, "top") is None


def test_find_case_sensitive():
    """Test that camera name search is case-sensitive."""
    model = MockModel(["Front", "BACK"])
    
    assert find(model, "Front") == 0
    assert find(model, "front") is None
    assert find(model, "BACK") == 1
    assert find(model, "back") is None


def test_resolve_with_string():
    """Test resolving camera name to ID."""
    model = MockModel(["front", "back", "side"])
    
    assert resolve(model, "front") == 0
    assert resolve(model, "back") == 1
    assert resolve(model, "nonexistent") is None


def test_resolve_with_int():
    """Test resolving camera ID (passthrough)."""
    model = MockModel(["front", "back"])
    
    assert resolve(model, 0) == 0
    assert resolve(model, 1) == 1
    assert resolve(model, 5) == 5  # Should pass through even if invalid


def test_resolve_with_none():
    """Test resolving None identifier."""
    model = MockModel(["front", "back"])
    
    assert resolve(model, None) is None


def test_resolve_with_invalid_type():
    """Test resolving with invalid identifier type."""
    model = MockModel(["front", "back"])
    
    # Should pass through non-string types as-is
    assert resolve(model, 3.14) == 3.14
    assert resolve(model, []) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
