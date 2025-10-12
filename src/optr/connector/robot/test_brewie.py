"""
Test and example usage for Brewie robot connector

This demonstrates how to use the Brewie robot with the optr framework.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from optr.connector.robot import BrewieRobot
from optr.operator import Operator


async def example_basic_control():
    """Basic example: Connect and control Brewie robot"""
    # Initialize robot connector
    robot = BrewieRobot(host="192.168.20.49", port=9090, auto_connect=False)

    try:
        # Connect to robot
        print("Connecting to Brewie robot...")
        connected = await robot.connect()
        if not connected:
            print("Failed to connect to robot")
            return

        print(f"Connected: {robot}")

        # Get current joint positions
        print("\nGetting current joint positions...")
        positions = await robot.get_joint_positions()
        print(f"Current positions: {positions}")

        # Move specific joints to new positions
        print("\nMoving joints to new positions...")
        new_positions = {
            13: 900,
            14: 150,
            15: 800,
        }
        success = await robot.set_joint_positions(new_positions, duration=2.0)
        print(f"Move command sent: {success}")

        # Wait for movement to complete
        await asyncio.sleep(2.5)

        # Read positions again
        print("\nGetting updated joint positions...")
        updated_positions = await robot.get_joint_positions()
        print(f"Updated positions: {updated_positions}")

    finally:
        # Always disconnect
        await robot.disconnect()
        print("\nDisconnected from robot")


async def example_with_context_manager():
    """Example using async context manager for automatic connection handling"""
    async with BrewieRobot(host="192.168.20.49", port=9090) as robot:
        # Robot is automatically connected
        positions = await robot.get_joint_positions()
        print(f"Joint positions: {positions}")

        # Move robot
        await robot.move_joints({13: 500, 14: 500}, duration=1.5)
        await asyncio.sleep(1.5)

    # Robot is automatically disconnected


async def example_with_operator():
    """Example using Brewie robot with Operator class"""
    # Create robot connector
    robot = BrewieRobot(host="192.168.20.49", port=9090, auto_connect=False)

    # Create operator with robot connector
    op = Operator({"brewie": robot})

    try:
        # Connect to robot using operator
        await op.execute_action("connect", connector_name="brewie")

        # Get robot state through operator
        state = await op.get_state("brewie")
        print(f"Robot state: {state.metadata}")

        # Execute move action through operator
        await op.execute_action(
            "move",
            connector_name="brewie",
            positions={13: 876, 14: 125, 15: 810},
            duration=1.0,
        )

        # Wait for movement
        await asyncio.sleep(1.5)

        # Get updated state
        updated_state = await op.get_state("brewie")
        print(f"Updated state: {updated_state.metadata}")

    finally:
        # Disconnect
        await op.execute_action("disconnect", connector_name="brewie")


async def example_single_joint_control():
    """Example: Control individual joints"""
    robot = BrewieRobot(host="192.168.20.49", port=9090, auto_connect=False)

    try:
        await robot.connect()

        # Get position of a specific joint
        joint_13_pos = await robot.get_joint_position(13)
        print(f"Joint 13 position: {joint_13_pos}")

        # Move a single joint
        await robot.set_joint_position(13, 750, duration=1.0)
        print("Moving joint 13 to position 750...")

        await asyncio.sleep(1.5)

        # Verify new position
        new_pos = await robot.get_joint_position(13)
        print(f"Joint 13 new position: {new_pos}")

    finally:
        await robot.disconnect()


async def example_sequential_movements():
    """Example: Perform a sequence of movements"""
    async with BrewieRobot(host="192.168.20.49", port=9090) as robot:
        print("Performing movement sequence...")

        # Step 1: Home position
        print("Step 1: Moving to home position")
        await robot.move_joints(
            {13: 500, 14: 500, 15: 500, 16: 500, 17: 500, 18: 500}, duration=2.0
        )
        await asyncio.sleep(2.5)

        # Step 2: Reach position
        print("Step 2: Extending arm")
        await robot.move_joints({13: 800, 14: 200, 15: 700}, duration=1.5)
        await asyncio.sleep(2.0)

        # Step 3: Grip
        print("Step 3: Closing gripper")
        await robot.move_joints({19: 100}, duration=0.5)
        await asyncio.sleep(1.0)

        # Step 4: Retract
        print("Step 4: Retracting arm")
        await robot.move_joints({13: 500, 14: 500, 15: 500}, duration=1.5)
        await asyncio.sleep(2.0)

        # Step 5: Open gripper
        print("Step 5: Opening gripper")
        await robot.move_joints({19: 500}, duration=0.5)
        await asyncio.sleep(1.0)

        print("Sequence complete!")


async def example_read_all_joints():
    """Example: Read and display all joint positions"""
    async with BrewieRobot(host="192.168.20.49", port=9090) as robot:
        positions = await robot.get_joint_positions()

        print("Brewie Robot Joint Positions:")
        print("-" * 40)
        for joint_id, position in sorted(positions.items()):
            print(f"  Joint {joint_id:2d}: {position:4.0f}")
        print("-" * 40)


# Uncomment the example you want to run
if __name__ == "__main__":
    # Choose one example to run:

    # Example 1: Basic control
    asyncio.run(example_basic_control())

    # Example 2: Context manager
    # asyncio.run(example_with_context_manager())

    # Example 3: Using with Operator
    # asyncio.run(example_with_operator())

    # Example 4: Single joint control
    # asyncio.run(example_single_joint_control())

    # Example 5: Sequential movements
    # asyncio.run(example_sequential_movements())

    # Example 6: Read all joints
    # asyncio.run(example_read_all_joints())

    print("Please uncomment one of the examples to run it.")
    print("Make sure to update the robot IP address and port!")

