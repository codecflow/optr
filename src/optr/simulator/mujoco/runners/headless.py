"""Headless runner with pipe output."""

import time

from ..outputs.pipe import PipeOutput
from ..outputs.renderer import Renderer


class HeadlessRunner:
    """Runs simulation with headless pipe output."""

    def __init__(self, simulation, config: dict | None = None):
        """Initialize headless runner with simulation and configuration.

        Args:
            simulation: Simulation instance to run
            config: Configuration dict with video/pipe settings
        """
        self.simulation = simulation
        self.config = config or {}
        self.renderer = None
        self.pipe_output = None

        # Timing for outputs (default 30 fps)
        fps = self.config.get('video', {}).get('fps', 30)
        self.frame_duration = 1.0 / fps
        self.last_frame_time = 0.0

    def setup(self) -> None:
        """Setup simulation and outputs."""
        print("Initializing headless simulation...")

        # Setup simulation (simulation instance provided via constructor)
        self.simulation.setup()

        # Setup renderer and pipe output if enabled
        pipe_config = self.config.get('pipe', {})
        if pipe_config.get('enabled', False):
            model = self.simulation.get_model()
            data = self.simulation.get_data()
            video_config = self.config.get('video', {})
            self.renderer = Renderer(model, data, video_config)
            self.pipe_output = PipeOutput(self.renderer, pipe_config)

            print(f"Pipe Output: {pipe_config.get('path', '/tmp/robot.pipe')}")
            width = video_config.get('width', 640)
            height = video_config.get('height', 480)
            print(f"Format: RGB24 {width}x{height}")

    def run(self) -> None:
        """Run headless simulation loop."""
        if not self.simulation:
            raise RuntimeError("Runner not setup. Call setup() first.")

        print("\nStarting headless simulation...")
        print("Press Ctrl+C to stop")

        # Calculate steps per frame for proper timing
        sim_timestep = 0.002  # From OnnxSimulation
        steps_per_frame = int(self.frame_duration / sim_timestep)

        fps = self.config.get('video', {}).get('fps', 30)
        print(f"Steps per frame: {steps_per_frame}")
        print(f"Target FPS: {fps}")

        model = self.simulation.get_model()
        data = self.simulation.get_data()

        try:
            # Run simulation loop
            while True:
                step_start = time.time()

                # Step the simulation
                self.simulation.step(steps_per_frame)

                # Process pipe output at the configured frame rate
                current_time = time.time()
                if current_time - self.last_frame_time >= self.frame_duration:
                    if self.pipe_output:
                        try:
                            self.pipe_output.process(model, data)
                        except Exception as e:
                            print(f"Error processing pipe output: {e}")

                    self.last_frame_time = current_time

                # Maintain proper timing (same as passive runner for consistency)
                time_until_next_step = sim_timestep * steps_per_frame - (
                    time.time() - step_start
                )
                if time_until_next_step > 0:
                    time.sleep(time_until_next_step)

        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up all resources."""
        print("\nCleaning up...")

        # Clean up pipe output
        if self.pipe_output:
            self.pipe_output.close()

        # Clean up renderer
        if self.renderer:
            self.renderer.close()

        # Clean up simulation
        if self.simulation:
            self.simulation.cleanup()

        print("Shutdown complete")
