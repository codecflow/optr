"""Test script for GStreamer sinks."""

import time

import numpy as np

from optr.stream.gstreamer import SHMSink, UDPSink, UnixFDSink


def create_test_frame(
    width: int, height: int, channels: int, frame_num: int
) -> np.ndarray:
    """Create a test frame with a gradient pattern."""
    frame = np.zeros((height, width, channels), dtype=np.uint8)

    # Create a gradient that changes with frame number
    for y in range(height):
        for x in range(width):
            # Red channel - horizontal gradient
            frame[y, x, 0] = (x * 255 // width + frame_num * 10) % 256
            # Green channel - vertical gradient
            frame[y, x, 1] = (y * 255 // height + frame_num * 10) % 256
            # Blue channel - diagonal gradient
            if channels > 2:
                frame[y, x, 2] = (
                    (x + y) * 255 // (width + height) + frame_num * 10
                ) % 256

    return frame


def test_shm_sink():
    """Test SHMSink implementation."""
    print("\n=== Testing SHMSink ===")

    sink = SHMSink(
        socket_path="/tmp/test_shm.sock", width=640, height=480, fps=30.0, format="RGB"
    )

    try:
        # Write 10 test frames
        for i in range(10):
            frame = create_test_frame(640, 480, 3, i)
            sink.write(frame)
            print(f"  Written frame {i + 1}/10")
            time.sleep(0.033)  # ~30 FPS

        print("✓ SHMSink test completed successfully")
    finally:
        sink.close()


def test_udp_sink():
    """Test UDPSink implementation."""
    print("\n=== Testing UDPSink ===")

    sink = UDPSink(
        host="127.0.0.1", port=5000, width=640, height=480, fps=30.0, format="RGB"
    )

    try:
        # Write 10 test frames
        for i in range(10):
            frame = create_test_frame(640, 480, 3, i)
            sink.write(frame)
            print(f"  Written frame {i + 1}/10")
            time.sleep(0.033)  # ~30 FPS

        print("✓ UDPSink test completed successfully")
    finally:
        sink.close()


def test_unixfd_sink():
    """Test UnixFDSink implementation."""
    print("\n=== Testing UnixFDSink ===")

    try:
        sink = UnixFDSink(
            socket_path="/tmp/test_unixfd.sock",
            width=640,
            height=480,
            fps=30.0,
            format="RGB",
        )

        # Write 10 test frames
        for i in range(10):
            frame = create_test_frame(640, 480, 3, i)
            sink.write(frame)
            print(f"  Written frame {i + 1}/10")
            time.sleep(0.033)  # ~30 FPS

        print("✓ UnixFDSink test completed successfully")
        sink.close()
    except RuntimeError as e:
        if "unixfd plugin not found" in str(e):
            print(f"⚠ UnixFDSink skipped: {e}")
        else:
            raise


def test_format_support():
    """Test different format support."""
    print("\n=== Testing Format Support ===")

    formats = ["RGB", "RGBA"]

    for fmt in formats:
        channels = 3 if fmt == "RGB" else 4
        print(f"\nTesting {fmt} format...")

        sink = SHMSink(
            socket_path=f"/tmp/test_{fmt.lower()}.sock",
            width=320,
            height=240,
            fps=15.0,
            format=fmt,
        )

        try:
            # Write a few test frames
            for i in range(3):
                frame = create_test_frame(320, 240, channels, i)
                sink.write(frame)

            print(f"  ✓ {fmt} format works")
        finally:
            sink.close()


def test_error_handling():
    """Test error handling."""
    print("\n=== Testing Error Handling ===")

    sink = SHMSink(
        socket_path="/tmp/test_error.sock", width=640, height=480, format="RGB"
    )

    try:
        # Test wrong frame shape
        wrong_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        try:
            sink.write(wrong_frame)
            print("  ✗ Should have raised ValueError for wrong shape")
        except ValueError as e:
            print(f"  ✓ Correctly raised ValueError: {e}")

        # Test correct frame after error
        correct_frame = create_test_frame(640, 480, 3, 0)
        sink.write(correct_frame)
        print("  ✓ Recovery after error works")

    finally:
        sink.close()


def main():
    """Run all tests."""
    print("Starting GStreamer Sink Tests")
    print("=" * 40)

    test_shm_sink()
    test_udp_sink()
    test_unixfd_sink()
    test_format_support()
    test_error_handling()

    print("\n" + "=" * 40)
    print("All tests completed!")


if __name__ == "__main__":
    main()
