"""
GUI element detection
"""

from typing import Any


class ElementDetector:
    """Detect GUI elements like buttons, inputs, etc."""

    def __init__(self):
        self.button_patterns = [
            "ok",
            "cancel",
            "submit",
            "save",
            "delete",
            "edit",
            "add",
            "remove",
            "yes",
            "no",
            "apply",
            "close",
            "open",
            "new",
            "create",
            "update",
            "login",
            "logout",
            "sign in",
            "sign up",
            "register",
            "search",
            "next",
            "previous",
            "back",
            "forward",
            "continue",
            "finish",
        ]

        self.input_patterns = [
            "username",
            "password",
            "email",
            "name",
            "address",
            "phone",
            "search",
            "query",
            "message",
            "comment",
            "description",
            "title",
            "subject",
            "content",
            "text",
            "value",
        ]

    async def detect_buttons(self, ocr_result: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect button elements from OCR results"""
        buttons = []

        for text_item in ocr_result["texts"]:
            text = text_item["content"].lower()
            if any(pattern in text for pattern in self.button_patterns):
                buttons.append(
                    {
                        "type": "button",
                        "name": text_item["content"],
                        "rectangle": text_item["bbox"],
                        "confidence": text_item["confidence"],
                        "actions": ["click", "rightClick"],
                    }
                )

        return buttons

    async def detect_input_fields(
        self, ocr_result: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Detect input field labels from OCR results"""
        fields = []

        for text_item in ocr_result["texts"]:
            text = text_item["content"].lower()
            if (
                any(pattern in text for pattern in self.input_patterns)
                or text.endswith(":")
                or text.endswith("*")
            ):
                fields.append(
                    {
                        "type": "input_field",
                        "name": text_item["content"],
                        "rectangle": text_item["bbox"],
                        "confidence": text_item["confidence"],
                        "actions": ["click", "type", "clear"],
                    }
                )

        return fields

    async def detect_clickable_text(
        self, ocr_result: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Detect potentially clickable text elements"""
        clickable = []

        for text_item in ocr_result["texts"]:
            # High confidence text is likely clickable
            if text_item["confidence"] > 0.8:
                clickable.append(
                    {
                        "type": "text",
                        "name": text_item["content"],
                        "rectangle": text_item["bbox"],
                        "confidence": text_item["confidence"],
                        "actions": ["click"],
                    }
                )

        return clickable

    def group_elements_by_rows(
        self, elements: list[dict[str, Any]], y_threshold: int = 15
    ) -> list[list[dict[str, Any]]]:
        """Group elements into rows based on vertical position"""
        if not elements:
            return []

        # Sort by y position
        sorted_elements = sorted(elements, key=lambda x: x["rectangle"][1])

        rows = []
        current_row: list[dict[str, Any]] = []
        previous_y = sorted_elements[0]["rectangle"][1]

        for element in sorted_elements:
            y = element["rectangle"][1]

            # If vertical position differs significantly, start new row
            if abs(y - previous_y) > y_threshold:
                if current_row:
                    # Sort current row by x position
                    current_row.sort(key=lambda x: x["rectangle"][0])
                    rows.append(current_row)
                current_row = []

            current_row.append(element)
            previous_y = y

        # Add last row
        if current_row:
            current_row.sort(key=lambda x: x["rectangle"][0])
            rows.append(current_row)

        return rows
