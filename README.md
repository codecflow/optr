

# Operator (`optr`)

A unified Python framework for building, training, and deploying intelligent operators across digital and physical environments.

> [!WARNING]  
> **Early Alpha** — APIs and behavior will change without notice.

## Overview

`optr` provides a flexible architecture for creating operators that can:
- **Automate desktop applications** via GUI interaction
- **Control physical robots** through simulation and hardware interfaces  
- **Learn from demonstrations** using imitation learning and reinforcement learning
- **Record and replay** episodes for testing and training
- **Bridge multiple environments** with unified connector interfaces

## Key Features

- **Desktop Automation** - Click, type, and interact with GUI elements
- **Robot Control** - MuJoCo simulation and physical robot support
- **Learning Algorithms** - Imitation learning, Pi0, and custom algorithms
- **Episode Recording** - Capture and replay operator sequences
- **Modular Connectors** - Extensible interface for any environment
- **Validation & Safety** - Built-in sentinel guards and validators
- **Training Pipeline** - Dataset management and model training

## Installation

### Basic Install
```bash
pip install optr
```

### Development Install (using uv)
```bash
git clone https://github.com/codecflow/optr

cd optr

uv sync --dev
```

## Quick Start

### Desktop Automation

Create an operator that automates login:

```python
# my_app/operators/login.py

from optr.operator import Operator
from optr.connector.desktop import DesktopConnector

async def login_operator():
    op = Operator({"desktop": DesktopConnector()})
    
    # Click username field
    await op.execute_action("click", selector="#username")
    await op.execute_action("type", text="demo_user")
    
    # Click password field  
    await op.execute_action("click", selector="#password")
    await op.execute_action("type", text="secure_pass")
    
    # Submit form
    await op.execute_action("click", selector="#submit")
    
    return op
```

### Robot Control (MuJoCo)

Control a simulated robot:

```python
# my_app/operators/robot.py

from optr.operator import Operator
from optr.simulator.mujoco import MuJoCoSimulation

async def robot_operator():
    sim = MuJoCoSimulation("models/robot.xml")
    op = Operator({"robot": sim.get_connector()})
    
    # Move to target position
    await op.execute_action("move", 
                           connector_name="robot",
                           position=[0.5, 0.3, 0.2])
    
    # Grasp object
    await op.execute_action("grasp", 
                           connector_name="robot",
                           force=10.0)
    
    return op
```

## Core Concepts

### Operators
The main abstraction for defining automated behaviors. Operators can work with multiple connectors simultaneously.

### Connectors
Interfaces to different environments (desktop, robot, web, etc.). Each connector provides state observation and action execution.

### Algorithms
Learning algorithms for training operators from demonstrations or through reinforcement learning.

### Episodes
Recorded sequences of states and actions that can be replayed or used for training.

### Sentinel
Safety and validation layer that ensures operators behave within defined constraints.

## Roadmap

- [ ] Cloud API connectors
- [ ] Distributed operator coordination
- [ ] Model zoo with pre-trained operators
- [ ] Real-time monitoring dashboard

## License

MIT © CodecFlow

