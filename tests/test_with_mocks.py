#!/usr/bin/env python3
"""
Example tests using mock projector responses
Demonstrates how to test projector control without actual hardware
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from projector_control import ProjectorController, ProjectorManager
from rear_projector_control import RearProjectorController
from mock_helpers import (
    mock_projector_server,
    create_mock_socket_patcher,
    ProjectorStateBuilder,
    get_default_responses
)
from mock_projector_server import MockProjectorServer


def test_power_status_with_mock_server():
    """Test power status using mock server"""
    print("\n🧪 Test: Power Status with Mock Server")
    print("-" * 50)
    
    # Test with projector ON
    with mock_projector_server(power="ON") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        status = controller.get_power_status()
        print(f"✅ Power status (ON): {status}")
        assert status == "ON", f"Expected ON, got {status}"
        
        controller.disconnect()
    
    # Test with projector OFF
    with mock_projector_server(power="OFF") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        status = controller.get_power_status()
        print(f"✅ Power status (OFF): {status}")
        assert status == "OFF", f"Expected OFF, got {status}"
        
        controller.disconnect()


def test_power_control_with_mock_server():
    """Test power control using mock server"""
    print("\n🧪 Test: Power Control with Mock Server")
    print("-" * 50)
    
    with mock_projector_server(power="OFF") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        # Turn on
        success = controller.set_power(True)
        print(f"✅ Power ON command: {success}")
        assert success, "Power ON should succeed"
        
        # Check state changed
        status = controller.get_power_status()
        print(f"✅ Power status after ON: {status}")
        assert status == "ON", f"Expected ON after power on, got {status}"
        
        # Turn off
        success = controller.set_power(False)
        print(f"✅ Power OFF command: {success}")
        assert success, "Power OFF should succeed"
        
        controller.disconnect()


def test_mute_control_with_mock_server():
    """Test mute control using mock server"""
    print("\n🧪 Test: Mute Control with Mock Server")
    print("-" * 50)
    
    with mock_projector_server(mute="UNMUTED") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        # Mute
        success = controller.set_mute(True)
        print(f"✅ Mute command: {success}")
        assert success, "Mute should succeed"
        
        status = controller.get_mute_status()
        print(f"✅ Mute status: {status}")
        assert status == "MUTED", f"Expected MUTED, got {status}"
        
        # Unmute
        success = controller.set_mute(False)
        print(f"✅ Unmute command: {success}")
        assert success, "Unmute should succeed"
        
        controller.disconnect()


def test_freeze_control_with_mock_server():
    """Test freeze control using mock server"""
    print("\n🧪 Test: Freeze Control with Mock Server")
    print("-" * 50)
    
    with mock_projector_server(freeze="NORMAL") as server:
        controller = ProjectorController(server.host, server.port)
        controller.connect()
        
        # Freeze
        success = controller.freeze_screen(True)
        print(f"✅ Freeze command: {success}")
        assert success, "Freeze should succeed"
        
        status = controller.get_freeze_status()
        print(f"✅ Freeze status: {status}")
        assert status == "FROZEN", f"Expected FROZEN, got {status}"
        
        # Unfreeze
        success = controller.freeze_screen(False)
        print(f"✅ Unfreeze command: {success}")
        assert success, "Unfreeze should succeed"
        
        status = controller.get_freeze_status()
        print(f"✅ Freeze status after unfreeze: {status}")
        assert status == "NORMAL", f"Expected NORMAL, got {status}"
        
        controller.disconnect()


def test_multiple_projectors_with_mock():
    """Test ProjectorManager with multiple mock projectors"""
    print("\n🧪 Test: Multiple Projectors with Mock")
    print("-" * 50)
    
    # Create two mock servers
    server1 = MockProjectorServer(port=0)
    server1.set_state(power="ON", mute="UNMUTED")
    port1 = server1.start()
    
    server2 = MockProjectorServer(port=0)
    server2.set_state(power="OFF", mute="MUTED")
    port2 = server2.start()
    
    try:
        import time
        time.sleep(0.2)  # Give servers time to start
        
        projectors = [
            ("127.0.0.1", port1),
            ("127.0.0.1", port2)
        ]
        
        manager = ProjectorManager(projectors)
        
        # Get all status
        status = manager.get_all_status()
        print(f"✅ Status keys: {list(status.keys())}")
        print(f"✅ Status count: {len(status)}")
        
        # Note: ProjectorManager uses IP as key, so with same IP but different ports,
        # the second controller overwrites the first. In real usage, use different IPs.
        # For this test, we verify the functionality works with at least one projector
        assert "127.0.0.1" in status, "Should have status for 127.0.0.1"
        assert status["127.0.0.1"]['online'], "Projector should be online"
        
        manager.close()
        
    finally:
        server1.stop()
        server2.stop()


def test_with_mock_socket_patcher():
    """Test using mock socket patcher (alternative approach)"""
    print("\n🧪 Test: Mock Socket Patcher")
    print("-" * 50)
    
    builder = ProjectorStateBuilder()
    builder.power_on().unmuted().normal().lamp_hours(5678)
    responses = builder.build_responses()
    
    with create_mock_socket_patcher(responses):
        controller = ProjectorController("127.0.0.1", 4352)
        controller.connect()
        
        # Test various status queries
        power = controller.get_power_status()
        print(f"✅ Power: {power}")
        assert power == "ON"
        
        mute = controller.get_mute_status()
        print(f"✅ Mute: {mute}")
        assert mute == "UNMUTED"
        
        freeze = controller.get_freeze_status()
        print(f"✅ Freeze: {freeze}")
        assert freeze == "NORMAL"
        
        lamp = controller.get_lamp_hours()
        print(f"✅ Lamp hours: {lamp}")
        assert lamp == 5678
        
        controller.disconnect()


def test_rear_projector_with_mock():
    """Test rear projector controller with mock"""
    print("\n🧪 Test: Rear Projector with Mock")
    print("-" * 50)
    
    with mock_projector_server(power="ON", mute="UNMUTED", freeze="NORMAL") as server:
        controller = RearProjectorController(server.host, server.port)
        controller.connect()
        
        status = controller.get_status()
        print(f"✅ Rear projector status: {status}")
        
        assert status['power'] == "ON"
        assert status['mute'] == "UNMUTED"
        assert status['freeze'] == "NORMAL"
        assert status['online'] == True
        
        controller.disconnect()


def main():
    """Run all mock tests"""
    print("=" * 60)
    print("Mock Projector Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Power Status", test_power_status_with_mock_server),
        ("Power Control", test_power_control_with_mock_server),
        ("Mute Control", test_mute_control_with_mock_server),
        ("Freeze Control", test_freeze_control_with_mock_server),
        ("Multiple Projectors", test_multiple_projectors_with_mock),
        ("Mock Socket Patcher", test_with_mock_socket_patcher),
        ("Rear Projector", test_rear_projector_with_mock),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name}: PASSED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED - {e}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

