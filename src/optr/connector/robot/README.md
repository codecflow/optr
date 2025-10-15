# Robot Connectors

Physical robot control connectors for the `optr` framework.

## Supported Robots

### Brewie Robot

The `BrewieRobot` connector provides control for Brewie robots via ROS (Robot Operating System) using `roslibpy`.

#### Requirements

```bash
pip install roslibpy
```

#### Quick Start

```python
import asyncio
from optr.connector.robot import BrewieRobot
from optr.operator import Operator

async def control_brewie():
    # Initialize robot with IP and port
    robot = BrewieRobot(host="192.168.1.100", port=9090, auto_connect=False)
    
    # Connect to robot
    await robot.connect()
    
    # Get current joint positions
    positions = await robot.get_joint_positions()
    print(f"Current positions: {positions}")
    
    # Move joints to target positions
    await robot.set_joint_positions(
        positions={13: 800, 14: 200, 15: 700},
        duration=2.0  # seconds
    )
    
    # Disconnect
    await robot.disconnect()

# Run the example
asyncio.run(control_brewie())
```

#### Using with Operator

```python
from optr.operator import Operator
from optr.connector.robot import BrewieRobot

async def main():
    # Create operator with Brewie connector
    op = Operator({"brewie": BrewieRobot(host="192.168.1.100", port=9090)})
    
    # Connect
    await op.execute_action("connect", connector_name="brewie")
    
    # Get robot state
    state = await op.get_state("brewie")
    print(state.metadata["joint_positions"])
    
    # Move robot
    await op.execute_action(
        "move",
        connector_name="brewie",
        positions={13: 500, 14: 500},
        duration=1.5
    )
    
    # Disconnect
    await op.execute_action("disconnect", connector_name="brewie")
```

#### Context Manager

```python
async with BrewieRobot(host="192.168.1.100", port=9090) as robot:
    # Robot automatically connects
    positions = await robot.get_joint_positions()
    await robot.move_joints({13: 500, 14: 500}, duration=1.0)
    # Robot automatically disconnects
```

#### Configuration

**Default Joint IDs:** `[13, 14, 15, 16, 17, 18, 19, 21, 20, 22]`

You can customize the joint IDs during initialization:

```python
robot = BrewieRobot(
    host="192.168.1.100",
    port=9090,
    joint_ids=[13, 14, 15, 16, 17, 18]  # Custom joint set
)
```

#### API Reference

**Key Methods:**

- `connect()` - Establish connection to robot
- `disconnect()` - Close connection
- `get_joint_positions()` - Get all joint positions as dict
- `set_joint_positions(positions, duration)` - Set multiple joint positions
- `get_joint_position(joint_id)` - Get single joint position
- `set_joint_position(joint_id, position, duration)` - Set single joint position
- `move_joints(joint_positions, duration)` - Convenience method for movement
- `is_connected()` - Check connection status

**Actions (via `execute_action`):**

- `"move"` - Move joints to target positions
- `"get_positions"` - Read current positions
- `"connect"` - Establish connection
- `"disconnect"` - Close connection

#### Examples

See `test_brewie.py` for comprehensive examples including:
- Basic control
- Context manager usage
- Integration with Operator
- Single joint control
- Sequential movement sequences
- Reading all joint positions

## Adding New Robot Connectors

To add support for a new robot:

1. Create a new file in `src/optr/connector/robot/` (e.g., `yourrobot.py`)
2. Subclass the `Robot` base class
3. Implement required abstract methods:
   - `connect()`
   - `disconnect()`
   - `get_joint_positions()`
   - `set_joint_positions()`
   - `is_connected()`
4. Add your connector to `__init__.py`
5. Create tests/examples

The base `Robot` class provides default implementations for `get_state()` and `execute_action()` that work with joint positions.

