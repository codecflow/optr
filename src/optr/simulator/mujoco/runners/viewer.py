"""Interactive viewer runner using managed viewer (viewer-only, no outputs)."""

import mujoco
import mujoco.viewer


class ViewerRunner:
    """Runs simulation with interactive managed viewer (no outputs)."""

    def __init__(self, simulation, config: dict | None = None):
        """Initialize viewer runner with simulation and configuration.

        Args:
            simulation: Simulation instance to run
            config: Configuration dict (currently unused for viewer-only mode)
        """
        self.simulation = simulation
        self.config = config or {}

    def setup(self) -> None:
        """Setup simulation."""
        print("Initializing interactive viewer...")

        # Setup simulation (simulation instance provided via constructor)
        self.simulation.setup()

    def run(self) -> None:
        """Run interactive managed viewer."""
        if not self.simulation:
            raise RuntimeError("Runner not setup. Call setup() first.")

        print("\nStarting interactive viewer...")

        model = self.simulation.get_model()
        data = self.simulation.get_data()

        def loader():
            print("\nInteractive Viewer Started")
            print("=" * 50)
            print(
                "Controls: Mouse (rotate), Scroll (zoom), Space (pause), Backspace (reset), Esc (quit)"
            )
            print("Robot: W/S (forward/back), A/D (strafe), Q/E (rotate)")
            print("Socket commands:")
            print("  echo 'PRESS:w' | nc -U /tmp/robot/keyboard.sock")
            print("  echo 'RELEASE:all' | nc -U /tmp/robot/keyboard.sock")
            print("=" * 50)
            print("Note: This is managed viewer mode - no streaming/recording")
            print("      Use 'passive' mode for streaming/recording support")

            return model, data

        try:
            # Launch managed viewer - this blocks and handles everything
            mujoco.viewer.launch(loader=loader)
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up all resources."""
        print("\nCleaning up...")

        # Clean up simulation
        if self.simulation:
            self.simulation.cleanup()

        print("Shutdown complete")
