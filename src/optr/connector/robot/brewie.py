"""
Brewie robot connector using ROS (roslibpy)
"""

import asyncio
from typing import Any

try:
    import roslibpy
except ImportError:
    roslibpy = None  # type: ignore

from .base import Robot


class BrewieRobot(Robot):
    """
    Connector for Brewie robot via ROS bridge
    
    Brewie uses ROS services and topics for control:
    - Service: /ros_robot_controller/bus_servo/get_position
    - Topic: /ros_robot_controller/bus_servo/set_position
    
    Default joint IDs: [13, 14, 15, 16, 17, 18, 19, 21, 20, 22]
    """

    def __init__(
        self,
        host: str,
        port: int = 9090,
        joint_ids: list[int] | None = None,
        auto_connect: bool = True,
    ):
        """
        Initialize Brewie robot connector
        
        Args:
            host: IP address of the ROS bridge
            port: Port number of the ROS bridge (default: 9090)
            joint_ids: List of servo joint IDs to control
                      (default: [13, 14, 15, 16, 17, 18, 19, 21, 20, 22])
            auto_connect: Automatically connect on initialization
        """
        if roslibpy is None:
            raise RuntimeError(
                "roslibpy is required for Brewie robot control. "
                "Install it with: pip install roslibpy"
            )

        self.host = host
        self.port = port
        self.joint_ids = joint_ids or [13, 14, 15, 16, 17, 18, 19, 21, 20, 22]

        self._ros_client: roslibpy.Ros | None = None
        self._get_servo_service: roslibpy.Service | None = None
        self._write_servo_topic: roslibpy.Topic | None = None
        self._connected = False

        if auto_connect:
            # Note: Synchronous init, user should call connect() explicitly
            # or use as async context manager
            pass

    async def connect(self) -> bool:
        """
        Establish connection to Brewie robot via ROS bridge
        
        Returns:
            True if connection successful
        """
        if self._connected and self._ros_client and self._ros_client.is_connected:
            return True

        try:
            # Create ROS client
            self._ros_client = roslibpy.Ros(host=self.host, port=self.port)

            # Run connection in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._ros_client.run)

            # Wait a moment for connection to establish
            await asyncio.sleep(0.5)

            if not self._ros_client.is_connected:
                return False

            # Initialize service for getting servo positions
            self._get_servo_service = roslibpy.Service(
                self._ros_client,
                "/ros_robot_controller/bus_servo/get_position",
                "ros_robot_controller/GetBusServosPosition",
            )

            # Initialize topic for setting servo positions
            self._write_servo_topic = roslibpy.Topic(
                self._ros_client,
                "/ros_robot_controller/bus_servo/set_position",
                "ros_robot_controller/SetBusServosPosition",
            )

            self._connected = True
            return True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Brewie robot: {e}") from e

    async def disconnect(self) -> None:
        """Close connection to Brewie robot"""
        if self._ros_client and self._ros_client.is_connected:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._ros_client.terminate)

        self._ros_client = None
        self._get_servo_service = None
        self._write_servo_topic = None
        self._connected = False

    async def is_connected(self) -> bool:
        """Check if robot is connected"""
        return (
            self._connected
            and self._ros_client is not None
            and self._ros_client.is_connected
        )

    async def get_joint_positions(self) -> dict[int, float]:
        """
        Get current positions of all configured joints
        
        Returns:
            Dictionary mapping joint ID to position value
            
        Raises:
            ConnectionError: If robot is not connected
            RuntimeError: If service call fails
        """
        if not await self.is_connected():
            raise ConnectionError("Robot is not connected")

        try:
            # Create service request with joint IDs
            request = roslibpy.ServiceRequest({"id": self.joint_ids})

            # Call service in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._get_servo_service.call, request
            )

            # Parse response
            if not result.get("success"):
                raise RuntimeError("Failed to get joint positions from robot")

            # Convert list of {id, position} to dict
            positions = {}
            for joint_data in result.get("position", []):
                joint_id = joint_data.get("id")
                position = joint_data.get("position")
                if joint_id is not None and position is not None:
                    positions[joint_id] = float(position)

            return positions

        except Exception as e:
            raise RuntimeError(f"Error getting joint positions: {e}") from e

    async def set_joint_positions(
        self, positions: dict[int, float], duration: float = 1.0
    ) -> bool:
        """
        Set target positions for specified joints
        
        Args:
            positions: Dictionary mapping joint IDs to target positions
            duration: Time in seconds to reach target (default: 1.0)
            
        Returns:
            True if command was published successfully
            
        Raises:
            ConnectionError: If robot is not connected
            ValueError: If positions format is invalid
        """
        if not await self.is_connected():
            raise ConnectionError("Robot is not connected")

        if not positions:
            raise ValueError("Positions dictionary cannot be empty")

        try:
            # Convert dict to list format expected by ROS
            position_list = [
                {"id": joint_id, "position": int(position)}
                for joint_id, position in positions.items()
            ]

            # Create message
            message = roslibpy.Message(
                {"duration": float(duration), "position": position_list}
            )

            # Publish message in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._write_servo_topic.publish, message
            )

            return True

        except Exception as e:
            raise RuntimeError(f"Error setting joint positions: {e}") from e

    async def move_joints(
        self, joint_positions: dict[int, float], duration: float = 1.0
    ) -> bool:
        """
        Convenience method to move specific joints to target positions
        
        Args:
            joint_positions: Dictionary of joint_id: position
            duration: Movement duration in seconds
            
        Returns:
            True if successful
        """
        return await self.set_joint_positions(joint_positions, duration)

    async def get_joint_position(self, joint_id: int) -> float:
        """
        Get position of a single joint
        
        Args:
            joint_id: ID of the joint
            
        Returns:
            Current position value
        """
        positions = await self.get_joint_positions()
        if joint_id not in positions:
            raise ValueError(f"Joint {joint_id} not found in configured joints")
        return positions[joint_id]

    async def set_joint_position(
        self, joint_id: int, position: float, duration: float = 1.0
    ) -> bool:
        """
        Set position of a single joint
        
        Args:
            joint_id: ID of the joint
            position: Target position value
            duration: Movement duration in seconds
            
        Returns:
            True if successful
        """
        return await self.set_joint_positions({joint_id: position}, duration)

    def __repr__(self) -> str:
        """String representation"""
        status = "connected" if self._connected else "disconnected"
        return f"BrewieRobot(host='{self.host}', port={self.port}, status='{status}')"

