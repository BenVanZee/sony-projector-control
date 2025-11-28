#!/usr/bin/env python3
"""
Test connection to rear projector (10.10.10.4)
Verifies PJLink connectivity and basic functionality
"""

import sys
import os
import socket
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rear_projector_control import RearProjectorController

def test_basic_connection():
    """Test basic network connectivity to rear projector"""
    print("Testing basic network connectivity to rear projector...")
    
    try:
        # Test basic socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('10.10.10.4', 4352))
        
        # Read initial connection message
        initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"✅ Basic connection successful!")
        print(f"   Initial message: {initial_msg.strip()}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        return False

def test_pjlink_commands():
    """Test PJLink commands on rear projector"""
    print("\nTesting PJLink commands on rear projector...")
    
    controller = RearProjectorController()
    
    try:
        # Test power status
        print("Testing power status query...")
        power_status = controller.get_power_status()
        print(f"   Power status: {power_status or 'UNKNOWN'}")
        
        # Test mute status
        print("Testing mute status query...")
        mute_status = controller.get_mute_status()
        print(f"   Mute status: {mute_status or 'UNKNOWN'}")
        
        # Test freeze status
        print("Testing freeze status query...")
        freeze_status = controller.get_freeze_status()
        print(f"   Freeze status: {freeze_status or 'UNKNOWN'}")
        
        # Test lamp hours
        print("Testing lamp hours query...")
        lamp_hours = controller.get_lamp_hours()
        print(f"   Lamp hours: {lamp_hours or 'UNKNOWN'}")
        
        # Test input status
        print("Testing input status query...")
        input_status = controller.get_input_status()
        print(f"   Input status: {input_status or 'UNKNOWN'}")
        
        # Test error status
        print("Testing error status query...")
        error_status = controller.get_error_status()
        print(f"   Error status: {error_status or 'NONE'}")
        
        print("✅ PJLink command testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ PJLink command testing failed: {e}")
        return False
    finally:
        controller.disconnect()

def test_comprehensive_status():
    """Test comprehensive status retrieval"""
    print("\nTesting comprehensive status retrieval...")
    
    controller = RearProjectorController()
    
    try:
        status = controller.get_status()
        print("✅ Comprehensive status retrieved:")
        print(f"   Power: {status['power'] or 'UNKNOWN'}")
        print(f"   Mute: {status['mute'] or 'UNKNOWN'}")
        print(f"   Freeze: {status['freeze'] or 'UNKNOWN'}")
        print(f"   Lamp Hours: {status['lamp_hours'] or 'UNKNOWN'}")
        print(f"   Input: {status['input'] or 'UNKNOWN'}")
        print(f"   Error: {status['error'] or 'NONE'}")
        print(f"   Online: {'Yes' if status['online'] else 'No'}")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive status failed: {e}")
        return False
    finally:
        controller.disconnect()

def main():
    """Main test function"""
    print("="*60)
    print("Rear Projector Connection Test (10.10.10.4)")
    print("="*60)
    
    tests = [
        ("Basic Network Connection", test_basic_connection),
        ("PJLink Commands", test_pjlink_commands),
        ("Comprehensive Status", test_comprehensive_status)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rear projector is ready for use.")
    else:
        print("⚠️  Some tests failed. Check network connectivity and PJLink settings.")
    
    print("\nNext steps:")
    print("1. Use 'python rear_projector_control.py' for interactive control")
    print("2. Use 'python rear_projector_cli.py status' for command-line status")
    print("3. Use 'python rear_projector_cli.py power --action on' to turn on")

if __name__ == "__main__":
    main()

