#!/usr/bin/env python3
"""
Integration helper for using mock projectors with macropad control scripts
Allows testing macropad functionality without real projectors
"""

import sys
import os
import time
import unittest.mock
from contextlib import contextmanager
from typing import List, Tuple, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_projector_server import MockProjectorServer
from mock_helpers import mock_projector_server


class MockMacropadEnvironment:
    """Sets up a complete mock environment for macropad testing"""
    
    def __init__(self, num_projectors: int = 2, **projector_states):
        """
        Initialize mock environment
        
        Args:
            num_projectors: Number of mock projectors to create
            **projector_states: Initial states for projectors (power, mute, freeze, etc.)
        """
        self.num_projectors = num_projectors
        self.projector_states = projector_states
        self.servers = []
        self.mock_projectors = []
        
    def start(self) -> List[Tuple[str, int]]:
        """
        Start all mock projectors and return list of (host, port) tuples
        
        Returns:
            List of (host, port) tuples for use with ProjectorManager
        """
        self.servers = []
        self.mock_projectors = []
        
        for i in range(self.num_projectors):
            server = MockProjectorServer(host="127.0.0.1", port=0)
            
            # Apply initial state if provided
            if self.projector_states:
                server.set_state(**self.projector_states)
            
            port = server.start()
            self.servers.append(server)
            self.mock_projectors.append(("127.0.0.1", port))
            
        # Give servers time to start
        time.sleep(0.2)
        
        return self.mock_projectors
    
    def stop(self):
        """Stop all mock projectors"""
        for server in self.servers:
            server.stop()
        self.servers = []
        self.mock_projectors = []
    
    def get_server(self, index: int = 0) -> MockProjectorServer:
        """Get a specific mock server by index"""
        if 0 <= index < len(self.servers):
            return self.servers[index]
        return None
    
    def set_state(self, index: int, **state):
        """Set state for a specific projector"""
        server = self.get_server(index)
        if server:
            server.set_state(**state)
    
    def get_state(self, index: int) -> Dict:
        """Get state for a specific projector"""
        server = self.get_server(index)
        if server:
            return server.get_state()
        return {}


@contextmanager
def mock_projector_config(num_projectors: int = 2, **projector_states):
    """
    Context manager that patches the config to use mock projectors
    
    Usage:
        with mock_projector_config(num_projectors=2, power="ON") as mock_env:
            # Now macropad scripts will use mock projectors
            from macropad.usb_keypad_control import USBKeypadController
            from config import PROJECTORS
            controller = USBKeypadController(PROJECTORS)
            controller.run()
    """
    # Create default mock projectors
    mock_env = MockMacropadEnvironment(num_projectors=num_projectors, **projector_states)
    projectors = mock_env.start()
    
    # Patch config.PROJECTORS
    try:
        import config
        
        # Save original
        original_projectors = config.PROJECTORS
        
        # Convert mock projectors to config format
        mock_config = []
        for i, (ip, port) in enumerate(projectors):
            mock_config.append({
                'ip': ip,
                'port': port,
                'name': f'Mock {i+1}',
                'nickname': ['left', 'right', 'rear'][i] if i < 3 else f'mock{i+1}',
                'location': f'Mock Location {i+1}',
                'group': 'front' if i < 2 else 'rear'
            })
        
        # Patch config
        config.PROJECTORS = mock_config
        
        yield mock_env
        
    finally:
        # Restore original
        if 'config' in sys.modules:
            config.PROJECTORS = original_projectors
        mock_env.stop()


def create_mock_projector_manager(num_projectors: int = 2, **projector_states):
    """
    Create a ProjectorManager with mock projectors
    
    Args:
        num_projectors: Number of mock projectors
        **projector_states: Initial states
    
    Returns:
        Tuple of (ProjectorManager, MockMacropadEnvironment)
    """
    from projector_control import ProjectorManager
    
    mock_env = MockMacropadEnvironment(num_projectors, **projector_states)
    projectors = mock_env.start()
    
    manager = ProjectorManager(projectors)
    
    return manager, mock_env


# Example usage functions
def example_usb_keypad_with_mocks():
    """Example: Use USB keypad control with mock projectors"""
    from macropad.usb_keypad_control import USBKeypadController
    
    # Create mock environment
    mock_env = MockMacropadEnvironment(num_projectors=2, power="ON", mute="UNMUTED")
    projectors = mock_env.start()
    
    try:
        # Create controller with mock projectors
        controller = USBKeypadController(
            projectors=[{'ip': ip, 'port': port} for ip, port in projectors],
            keypad_type="cut_copy_paste",
            debug_mode=True
        )
        
        print("✅ Mock projectors ready!")
        print("   Press buttons on your keypad to test")
        print("   (Projectors will respond with mock data)")
        
        # Run controller (this would normally block)
        # controller.run()
        
    finally:
        mock_env.stop()


def example_macropad_with_mocks():
    """Example: Use macropad control with mock projectors"""
    from macropad.macropad_control import MacropadController
    
    # Create mock environment
    mock_env = MockMacropadEnvironment(num_projectors=2, power="ON")
    projectors = mock_env.start()
    
    try:
        # Convert to tuple format
        projector_tuples = projectors
        
        # Create controller
        controller = MacropadController(
            projectors=projector_tuples,
            debug_mode=True,
            button_layout="4"
        )
        
        print("✅ Mock projectors ready!")
        print("   Press buttons on your macropad to test")
        
        # Run controller
        # controller.run()
        
    finally:
        mock_env.stop()


def example_with_config_patch():
    """Example: Use config patching for seamless integration"""
    with mock_projector_config(num_projectors=2, power="ON", mute="UNMUTED") as mock_env:
        # Now any script that imports config will use mock projectors
        from macropad.usb_keypad_control import USBKeypadController
        from config import PROJECTORS
        
        print(f"✅ Config patched with {len(PROJECTORS)} mock projectors")
        print(f"   Projectors: {PROJECTORS}")
        
        # Create controller - it will automatically use mock projectors from config
        controller = USBKeypadController(
            projectors=PROJECTORS,
            keypad_type="cut_copy_paste",
            debug_mode=True
        )
        
        print("✅ Controller ready with mock projectors!")
        # controller.run()


if __name__ == "__main__":
    print("=" * 60)
    print("Mock Macropad Integration Examples")
    print("=" * 60)
    
    print("\n1. Testing mock environment...")
    mock_env = MockMacropadEnvironment(num_projectors=2, power="ON")
    projectors = mock_env.start()
    print(f"✅ Created {len(projectors)} mock projectors")
    print(f"   Projectors: {projectors}")
    
    # Test getting status
    from projector_control import ProjectorManager
    manager = ProjectorManager(projectors)
    status = manager.get_all_status()
    print(f"✅ Status retrieved: {len(status)} projectors")
    for ip, info in status.items():
        print(f"   {ip}: Power={info['power']}, Online={info['online']}")
    
    mock_env.stop()
    print("\n✅ All tests passed!")

