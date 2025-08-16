"""
Tests for simulation protocol and types
"""

import pytest

from .simulation import Simulation, State


def test_state_type_var():
    """Test that State is a proper TypeVar."""
    from typing import TypeVar
    
    assert isinstance(State, TypeVar)
    assert State.__name__ == "State"


def test_simulation_protocol():
    """Test that Simulation protocol can be implemented."""
    
    class MockSimulation:
        """Mock implementation of Simulation protocol."""
        
        def __init__(self):
            self.state = {"step": 0}
        
        def step(self):
            """Step simulation forward."""
            self.state = {"step": self.state["step"] + 1}
            return self.state
        
        def reset(self):
            """Reset to initial state."""
            self.state = {"step": 0}
            return self.state
        
        def close(self):
            """Clean up resources."""
            pass
    
    # Test that our mock implements the protocol
    sim = MockSimulation()
    
    # Test initial state
    assert sim.state == {"step": 0}
    
    # Test step
    state = sim.step()
    assert state == {"step": 1}
    assert sim.state == {"step": 1}
    
    # Test reset
    reset_state = sim.reset()
    assert reset_state == {"step": 0}
    assert sim.state == {"step": 0}
    
    # Test close (should not raise)
    sim.close()


def test_simulation_protocol_typing():
    """Test that Simulation protocol works with type hints."""
    
    class TypedSimulation:
        """Simulation with specific state type."""
        
        def __init__(self):
            self.state: dict[str, int] = {"value": 42}
        
        def step(self) -> dict[str, int]:
            self.state["value"] += 1
            return self.state
        
        def reset(self) -> dict[str, int]:
            self.state = {"value": 42}
            return self.state
        
        def close(self) -> None:
            pass
    
    sim = TypedSimulation()
    
    # Test that it behaves correctly
    assert sim.state == {"value": 42}
    
    state = sim.step()
    assert state == {"value": 43}
    
    reset_state = sim.reset()
    assert reset_state == {"value": 42}


def test_simulation_protocol_missing_methods():
    """Test that incomplete implementations are caught."""
    
    class IncompleteSimulation:
        """Simulation missing required methods."""
        
        def __init__(self):
            self.state = "initial"
        
        def step(self):
            return "stepped"
        
        # Missing reset() and close() methods
    
    sim = IncompleteSimulation()
    
    # Should have step method
    assert hasattr(sim, 'step')
    assert sim.step() == "stepped"
    
    # Should not have reset and close methods
    assert not hasattr(sim, 'reset')
    assert not hasattr(sim, 'close')


def test_simulation_with_complex_state():
    """Test simulation with complex state objects."""
    
    class ComplexState:
        """Complex state object."""
        
        def __init__(self, x=0, y=0):
            self.x = x
            self.y = y
        
        def __eq__(self, other):
            return isinstance(other, ComplexState) and self.x == other.x and self.y == other.y
    
    class ComplexSimulation:
        """Simulation with complex state."""
        
        def __init__(self):
            self.state = ComplexState()
        
        def step(self):
            self.state.x += 1
            self.state.y += 2
            return self.state
        
        def reset(self):
            self.state = ComplexState()
            return self.state
        
        def close(self):
            pass
    
    sim = ComplexSimulation()
    
    # Test initial state
    assert sim.state == ComplexState(0, 0)
    
    # Test step
    state = sim.step()
    assert state == ComplexState(1, 2)
    
    # Test another step
    state = sim.step()
    assert state == ComplexState(2, 4)
    
    # Test reset
    reset_state = sim.reset()
    assert reset_state == ComplexState(0, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
