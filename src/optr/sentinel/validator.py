"""
Generic validator for action parameters
"""

from typing import Any

from ..types import Action


class Validator:
    """Validates action parameters and data"""

    def __init__(self):
        self.schemas = {}

    def register_schema(self, action_type: str, schema: dict[str, Any]):
        """Register validation schema for action type"""
        self.schemas[action_type] = schema

    def validate_action(self, action: Action) -> tuple[bool, str | None]:
        """Validate action parameters against schema"""
        if action.type not in self.schemas:
            # No schema registered, allow by default
            return True, None

        schema = self.schemas[action.type]

        # Check required parameters
        if "required" in schema:
            for param in schema["required"]:
                if param not in action.params:
                    return False, f"Missing required parameter: {param}"

        # Check parameter types
        if "types" in schema:
            for param, expected_type in schema["types"].items():
                if param in action.params:
                    if not isinstance(action.params[param], expected_type):
                        return (
                            False,
                            f"Parameter {param} must be of type {expected_type.__name__}",
                        )

        # Check parameter ranges/constraints
        if "constraints" in schema:
            for param, constraint in schema["constraints"].items():
                if param in action.params:
                    value = action.params[param]
                    if "min" in constraint and value < constraint["min"]:
                        return (
                            False,
                            f"Parameter {param} must be >= {constraint['min']}",
                        )
                    if "max" in constraint and value > constraint["max"]:
                        return (
                            False,
                            f"Parameter {param} must be <= {constraint['max']}",
                        )
                    if "enum" in constraint and value not in constraint["enum"]:
                        return (
                            False,
                            f"Parameter {param} must be one of {constraint['enum']}",
                        )

        return True, None

    def validate_data(
        self, data: Any, schema: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Validate arbitrary data against schema"""
        # Generic data validation
        if "type" in schema:
            if not isinstance(data, schema["type"]):
                return False, f"Data must be of type {schema['type'].__name__}"

        if "properties" in schema and isinstance(data, dict):
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    valid, error = self.validate_data(data[prop], prop_schema)
                    if not valid:
                        return False, f"Property {prop}: {error}"

        return True, None
