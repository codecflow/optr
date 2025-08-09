"""
Text detection using OCR
"""

import io
from typing import Any

from PIL import Image

from ...types import BoundingBox


class TextDetector:
    """OCR-based text detection"""

    def __init__(self):
        self._ocr_engine = None

    def _init_ocr(self):
        """Initialize OCR engine lazily"""
        if self._ocr_engine is None:
            try:
                import pytesseract

                self._ocr_engine = pytesseract
            except ImportError as e:
                raise RuntimeError("pytesseract required for text detection") from e

    async def detect_text(self, image: bytes) -> dict[str, Any]:
        """Detect all text in image with positions"""
        self._init_ocr()

        img = Image.open(io.BytesIO(image))
        data = self._ocr_engine.image_to_data(
            img, output_type=self._ocr_engine.Output.DICT
        )

        texts = []
        for i, text in enumerate(data["text"]):
            if text.strip():  # Only non-empty text
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]

                if w > 0 and h > 0:  # Valid bounding box
                    texts.append(
                        {
                            "content": text.strip(),
                            "bbox": [x, y, x + w, y + h],
                            "confidence": data["conf"][i] / 100.0,
                        }
                    )

        return {"img_shape": img.size + (3,), "texts": texts}

    async def find_text(self, image: bytes, target: str) -> list[BoundingBox]:
        """Find specific text in image"""
        result = await self.detect_text(image)

        boxes = []
        for text_item in result["texts"]:
            if target.lower() in text_item["content"].lower():
                bbox = text_item["bbox"]
                boxes.append(
                    BoundingBox(
                        x=bbox[0],
                        y=bbox[1],
                        width=bbox[2] - bbox[0],
                        height=bbox[3] - bbox[1],
                    )
                )

        return boxes
