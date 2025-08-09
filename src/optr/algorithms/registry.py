"""
Registry for managing available algorithms
"""

from .base import Algorithm


class Registry:
    """
    Central registry for algorithms
    """

    def __init__(self):
        self._algorithms: dict[str, type[Algorithm]] = {}
        self._instances: dict[str, Algorithm] = {}

    def register(
        self, name: str, algorithm_class: type[Algorithm], override: bool = False
    ):
        """
        Register an algorithm class

        Args:
            name: Name to register algorithm under
            algorithm_class: Algorithm class (must inherit from Algorithm)
            override: Whether to override existing registration
        """
        if not issubclass(algorithm_class, Algorithm):
            raise ValueError(f"{algorithm_class} must inherit from Algorithm")

        if name in self._algorithms and not override:
            raise ValueError(f"Algorithm '{name}' already registered")

        self._algorithms[name] = algorithm_class

    def create(
        self,
        name: str,
        config: dict | None = None,
        instance_name: str | None = None,
    ) -> Algorithm:
        """
        Create an instance of a registered algorithm

        Args:
            name: Name of registered algorithm
            config: Configuration for the algorithm
            instance_name: Optional name to store instance under

        Returns:
            Algorithm instance
        """
        if name not in self._algorithms:
            raise ValueError(f"Algorithm '{name}' not registered")

        algorithm_class = self._algorithms[name]
        instance = algorithm_class(config)

        if instance_name:
            self._instances[instance_name] = instance

        return instance

    def get_instance(self, name: str) -> Algorithm | None:
        """
        Get a stored algorithm instance

        Args:
            name: Instance name

        Returns:
            Algorithm instance or None
        """
        return self._instances.get(name)

    def list_algorithms(self) -> list[str]:
        """List all registered algorithm names"""
        return list(self._algorithms.keys())

    def list_instances(self) -> list[str]:
        """List all stored instance names"""
        return list(self._instances.keys())

    def unregister(self, name: str):
        """
        Unregister an algorithm

        Args:
            name: Algorithm name to unregister
        """
        if name in self._algorithms:
            del self._algorithms[name]

    def clear_instances(self):
        """Clear all stored instances"""
        self._instances.clear()

    def get_info(self) -> dict:
        """Get registry information"""
        return {
            "registered_algorithms": self.list_algorithms(),
            "active_instances": self.list_instances(),
            "instance_details": {
                name: instance.get_info() for name, instance in self._instances.items()
            },
        }
