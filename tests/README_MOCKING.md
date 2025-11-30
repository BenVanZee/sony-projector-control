# Mock Projector Testing

This directory contains utilities for testing projector control without requiring actual hardware.

## Overview

The mocking system provides two main approaches:

1. **Mock Projector Server** - A full TCP server that simulates a PJLink projector
2. **Mock Socket Patcher** - A lightweight mock that patches socket connections

## Files

- `mock_projector_server.py` - Full mock PJLink server implementation
- `mock_helpers.py` - Helper functions and utilities for mocking
- `test_with_mocks.py` - Example tests demonstrating usage

## Quick Start

### Using Mock Server (Recommended)

The mock server approach creates a real TCP server that responds to PJLink commands:

```python
from mock_helpers import mock_projector_server
from projector_control import ProjectorController

# Test with projector ON
with mock_projector_server(power="ON", mute="UNMUTED") as server:
    controller = ProjectorController(server.host, server.port)
    controller.connect()
    
    status = controller.get_power_status()
    assert status == "ON"
    
    controller.disconnect()
```

### Using Mock Socket Patcher

The socket patcher approach mocks at the socket level (faster, but less realistic):

```python
from mock_helpers import create_mock_socket_patcher, ProjectorStateBuilder
from projector_control import ProjectorController

# Build state and responses
builder = ProjectorStateBuilder()
builder.power_on().unmuted().normal()
responses = builder.build_responses()

# Use patcher
with create_mock_socket_patcher(responses):
    controller = ProjectorController("127.0.0.1", 4352)
    controller.connect()
    
    status = controller.get_power_status()
    assert status == "ON"
    
    controller.disconnect()
```

## Available Mock States

You can set the following projector states:

- `power`: "ON", "OFF", "COOLING", "WARMING"
- `mute`: "MUTED", "UNMUTED"
- `freeze`: "FROZEN", "NORMAL"
- `lamp_hours`: Integer (e.g., 1234)
- `input`: String (e.g., "11")
- `error`: String (e.g., "00000000")

## Examples

### Test Power Control

```python
def test_power_control():
    with mock_projector_server(power="OFF") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        # Turn on
        success = controller.set_power(True)
        assert success
        
        # Verify state changed
        status = controller.get_power_status()
        assert status == "ON"
        
        controller.disconnect()
```

### Test Multiple Projectors

```python
def test_multiple_projectors():
    server1 = MockProjectorServer(port=0)
    server1.set_state(power="ON")
    port1 = server1.start()
    
    server2 = MockProjectorServer(port=0)
    server2.set_state(power="OFF")
    port2 = server2.start()
    
    try:
        projectors = [
            ("127.0.0.1", port1),
            ("127.0.0.1", port2)
        ]
        
        manager = ProjectorManager(projectors)
        status = manager.get_all_status()
        
        # Verify status retrieved
        assert len(status) >= 1
        
    finally:
        server1.stop()
        server2.stop()
```

### Test State Builder

```python
from mock_helpers import ProjectorStateBuilder

builder = ProjectorStateBuilder()
builder.power_on().muted().frozen().lamp_hours(5000)
responses = builder.build_responses()

# Use responses with mock socket patcher
with create_mock_socket_patcher(responses):
    # ... test code ...
```

## Running Tests

Run the example test suite:

```bash
python tests/test_with_mocks.py
```

Or run individual test functions:

```python
from tests.test_with_mocks import test_power_control_with_mock_server
test_power_control_with_mock_server()
```

## Mock Server Standalone

You can also run the mock server standalone for manual testing:

```bash
python tests/mock_projector_server.py
```

This starts a server on a random port. You can then connect to it using the projector control tools.

## Supported PJLink Commands

The mock server supports all standard PJLink commands used by the control system:

- Power: `%1POWR ?`, `%1POWR 1`, `%1POWR 0`
- Mute: `%1AVMT ?`, `%1AVMT 30`, `%1AVMT 31`
- Freeze: `%2FREZ ?`, `%2FREZ 1`, `%2FREZ 0`
- Lamp: `%1LAMP ?`
- Input: `%1INPT ?`
- Error: `%1ERST ?`

## Tips

1. **Use mock server for integration tests** - More realistic, tests actual network code
2. **Use socket patcher for unit tests** - Faster, good for testing logic
3. **Set initial state** - Use `set_state()` or pass kwargs to `mock_projector_server()`
4. **Check state changes** - The mock server maintains state, so commands affect subsequent queries
5. **Multiple servers** - Create multiple `MockProjectorServer` instances for testing multiple projectors

## Troubleshooting

- **Connection refused**: Make sure the server has started (add a small sleep after `start()`)
- **No response**: Check that the command is in the responses dictionary
- **State not changing**: Verify you're using the correct command format (with `\r`)


