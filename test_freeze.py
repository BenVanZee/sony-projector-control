#!/usr/bin/env python3
"""
Test script for freeze functionality
"""

import logging
from projector_control import ProjectorManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_freeze_functionality():
    """Test freeze/unfreeze functionality"""
    
    # Test configuration
    projectors = [
        ("10.10.10.2", 4352),
        ("10.10.10.3", 4352),
    ]
    
    aliases = {
        'left': '10.10.10.2',
        'right': '10.10.10.3',
    }
    
    print("🧪 Testing Freeze Functionality")
    print("="*50)
    
    manager = ProjectorManager(projectors, aliases)
    
    try:
        # Get initial status
        print("\n📊 Initial Status:")
        status = manager.get_all_status()
        for ip, info in status.items():
            print(f"  {ip}: Power={info['power']}, Mute={info['mute']}, Freeze={info.get('freeze')}")
        
        # Test freeze
        print("\n❄️ Testing Freeze...")
        results = manager.freeze_all_screens(True)
        print(f"Freeze results: {results}")
        
        # Check status after freeze
        print("\n📊 Status After Freeze:")
        status = manager.get_all_status()
        for ip, info in status.items():
            print(f"  {ip}: Power={info['power']}, Mute={info['mute']}, Freeze={info.get('freeze')}")
        
        # Test unfreeze
        print("\n🔄 Testing Unfreeze...")
        results = manager.freeze_all_screens(False)
        print(f"Unfreeze results: {results}")
        
        # Check final status
        print("\n📊 Final Status:")
        status = manager.get_all_status()
        for ip, info in status.items():
            print(f"  {ip}: Power={info['power']}, Mute={info['mute']}, Freeze={info.get('freeze')}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        manager.close()

if __name__ == "__main__":
    test_freeze_functionality()
