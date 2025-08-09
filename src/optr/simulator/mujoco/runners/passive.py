"""Passive viewer runner with pipe output."""

import time

import mujoco

from ..outputs.pipe import PipeOutput
from ..outputs.renderer import Renderer


class PassiveRunner:
    """Runs simulation with passive viewer and pipe output."""

    def __init__(self, simulation, config: dict | None = None):
        """Initialize passive runner with simulation and configuration.

        Args:
            simulation: Simulation instance to run
            config: Configuration dict with video/pipe settings
        """
        self.simulation = simulation
        self.config = config or {}
        self.renderer = None
        self.pipe_output = None
        self.viewer = None
        self.running = False

        # Timing for outputs (default 30 fps)
        fps = self.config.get('video', {}).get('fps', 30)
        self.frame_duration = 1.0 / fps
        self.last_frame_time = 0.0

    def setup(self) -> None:
        """Setup simulation and outputs."""
        print("Initializing passive viewer with pipe output...")

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
        """Run passive viewer with outputs."""
        if not self.simulation:
            raise RuntimeError("Runner not setup. Call setup() first.")

        print("\nStarting passive viewer with pipe output...")
        print("Press Ctrl+C to stop")

        # Calculate steps per frame for proper timing
        # Get the actual simulation timestep
        model = self.simulation.get_model()
        sim_timestep = model.opt.timestep
        steps_per_frame = int(self.frame_duration / sim_timestep)

        fps = self.config.get('video', {}).get('fps', 30)
        print(f"Steps per frame: {steps_per_frame}")
        print(f"Target FPS: {fps}")

        model = self.simulation.get_model()
        data = self.simulation.get_data()

        try:
            # Create passive viewer - this gives us control over the simulation loop
            with mujoco.viewer.launch_passive(model, data) as viewer:
                print("\nPassive Viewer Started")
                print("=" * 50)
                print(
                    "Controls: Mouse (rotate), Scroll (zoom), Space (pause), Backspace (reset), Esc (quit)"
                )
                print("Robot: W/S (forward/back), A/D (strafe), Q/E (rotate)")
                print("Socket commands:")
                print("  echo 'PRESS:w' | nc -U /tmp/robot/keyboard.sock")
                print("  echo 'RELEASE:all' | nc -U /tmp/robot/keyboard.sock")
                print("=" * 50)
                print(
                    "Note: On macOS, use 'mjpython main.py passive' instead of 'python main.py passive'"
                )

                self.viewer = viewer
                self.running = True

                # Run our own simulation loop with viewer updates
                while self.running and viewer.is_running():
                    step_start = time.time()

                    # Step the simulation
                    self.simulation.step(steps_per_frame)

                    # Sync viewer with new simulation state
                    viewer.sync()

                    # Process pipe output at the configured frame rate
                    current_time = time.time()
                    if current_time - self.last_frame_time >= self.frame_duration:
                        if self.pipe_output:
                            try:
                                self.pipe_output.process(model, data)
                            except Exception as e:
                                print(f"Error processing pipe output: {e}")

                        self.last_frame_time = current_time

                    # Maintain proper timing
                    time_until_next_step = sim_timestep * steps_per_frame - (
                        time.time() - step_start
                    )
                    if time_until_next_step > 0:
                        time.sleep(time_until_next_step)

        except KeyboardInterrupt:
            print("\nShutdown requested...")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
        finally:
            self.running = False
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
