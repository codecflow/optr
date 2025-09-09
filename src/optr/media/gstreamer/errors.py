"""GStreamer error classes."""


class GStreamerError(Exception):
    """Base exception for GStreamer-related errors."""

    pass


class ElementCreationError(GStreamerError):
    """Raised when element creation fails."""

    def __init__(self, element_type: str, name: str | None = None):
        self.element_type = element_type
        self.name = name
        super().__init__(
            f"Failed to create element '{element_type}' with name '{name or 'auto'}'"
        )


class PropertyError(GStreamerError):
    """Raised when setting element properties fails."""

    def __init__(
        self,
        element_type: str,
        prop_name: str,
        value: object,
        original_error: Exception,
    ):
        self.element_type = element_type
        self.prop_name = prop_name
        self.value = value
        self.original_error = original_error
        super().__init__(
            f"Failed to set property '{prop_name}' to '{value}' on element '{element_type}': {original_error}"
        )


class PipelineError(GStreamerError):
    """Raised when pipeline operations fail."""

    def __init__(self, operation: str, details: str = ""):
        self.operation = operation
        self.details = details
        super().__init__(
            f"Pipeline {operation} failed{': ' + details if details else ''}"
        )


class BufferError(GStreamerError):
    """Raised when buffer operations fail."""

    def __init__(self, operation: str, details: str = ""):
        self.operation = operation
        self.details = details
        super().__init__(
            f"Buffer {operation} failed{': ' + details if details else ''}"
        )
