"""
Main GUI parser combining text and element detection
"""

from typing import Any

from .element_detection import ElementDetector
from .text_detection import TextDetector


class GUIParser:
    """Main GUI parser for extracting UI elements"""

    def __init__(self):
        self.text_detector = TextDetector()
        self.element_detector = ElementDetector()

    async def parse(self, image: bytes) -> dict[str, Any]:
        """Parse GUI elements from screenshot"""
        # Get OCR results
        ocr_result = await self.text_detector.detect_text(image)

        # Detect different element types
        buttons = await self.element_detector.detect_buttons(ocr_result)
        input_fields = await self.element_detector.detect_input_fields(ocr_result)
        clickable_text = await self.element_detector.detect_clickable_text(ocr_result)

        # Combine all elements
        all_elements = buttons + input_fields + clickable_text

        # Group elements by rows
        rows = self.element_detector.group_elements_by_rows(all_elements)

        return {
            "ocr": ocr_result,
            "elements": {
                "buttons": buttons,
                "input_fields": input_fields,
                "clickable_text": clickable_text,
                "all": all_elements,
            },
            "layout": {"rows": rows, "total_elements": len(all_elements)},
        }

    async def find_element_by_text(
        self, image: bytes, text: str
    ) -> list[dict[str, Any]]:
        """Find elements containing specific text"""
        parsed = await self.parse(image)

        matches = []
        for element in parsed["elements"]["all"]:
            if text.lower() in element["name"].lower():
                matches.append(element)

        return matches

    async def get_clickable_elements(self, image: bytes) -> list[dict[str, Any]]:
        """Get all clickable elements"""
        parsed = await self.parse(image)

        clickable = []
        for element in parsed["elements"]["all"]:
            if "click" in element.get("actions", []):
                clickable.append(element)

        return clickable
