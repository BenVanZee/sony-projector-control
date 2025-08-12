#!/usr/bin/env python3
"""
Example Usage Script for Sony Projector Control System
Demonstrates nickname functionality and common operations
"""

from projector_control import ProjectorManager
import time

def main():
    """Demonstrate nickname functionality"""
    print("🎬 Sony Projector Control - Nickname Examples")
    print("=" * 50)
    
    # Import config for projectors and aliases
    try:
        from config import PROJECTORS, PROJECTOR_ALIASES
        # Convert config format to tuple format
        projectors = [(p['ip'], p['port']) for p in PROJECTORS]
        aliases = PROJECTOR_ALIASES
        print("✅ Loaded configuration with nicknames")
    except ImportError:
        # Fallback configuration
        projectors = [
            ("10.10.10.2", 4352),
            ("10.10.10.3", 4352),
        ]
        aliases = {
            'left': '10.10.10.2',
            'right': '10.10.10.3',
            'l': '10.10.10.2',
            'r': '10.10.10.3'
        }
        print("⚠️  Using fallback configuration")
    
    # Show available nicknames
    print(f"\n📋 Available nicknames:")
    for nickname, ip in aliases.items():
        print(f"  {nickname:8} → {ip}")
    
    # Create manager
    manager = ProjectorManager(projectors, aliases)
    
    try:
        # Example 1: Check status using nicknames
        print(f"\n🔍 Example 1: Checking status...")
        status = manager.get_all_status()
        
        for ip, info in status.items():
            nickname = manager.get_nickname_by_ip(ip)
            display_name = f"{nickname} ({ip})" if nickname else ip
            print(f"\n{display_name}:")
            print(f"  Power: {info['power'] or 'UNKNOWN'}")
            print(f"  Mute: {info['mute'] or 'UNKNOWN'}")
            print(f"  Online: {'Yes' if info['online'] else 'No'}")
        
        # Example 2: Control specific projectors by nickname
        print(f"\n🎯 Example 2: Controlling specific projectors...")
        
        # Test nickname resolution
        test_nicknames = ['left', 'right', 'l', 'r']
        for nickname in test_nicknames:
            ip = manager.get_projector_by_nickname(nickname)
            if ip:
                print(f"  {nickname} → {ip}")
            else:
                print(f"  ❌ {nickname} not found")
        
        # Example 3: Demonstrate common operations
        print(f"\n⚡ Example 3: Common operations...")
        print("  (These are examples - not actually executed)")
        print("  python3 projector_cli.py power --action on --projectors left right")
        print("  python3 projector_cli.py mute --action on --projectors left")
        print("  python3 projector_cli.py mute --action off --projectors right")
        print("  python3 projector_cli.py free --projectors left right")
        print("  python3 projector_cli.py freeze --action on --projectors left right")
        print("  python3 projector_cli.py freeze --action off --projectors left right")
        print("  python3 projector_cli.py status --projectors l r")
        
        # Example 4: Show how to add more nicknames
        print(f"\n🔧 Example 4: Adding more nicknames...")
        print("  Edit config.py to add more aliases:")
        print("  PROJECTOR_ALIASES = {")
        print("      'left': '10.10.10.2',")
        print("      'right': '10.10.10.3',")
        print("      'front': '10.10.10.2',")
        print("      'rear': '10.10.10.3',")
        print("      'main': '10.10.10.2',")
        print("      'side': '10.10.10.3',")
        print("      'l': '10.10.10.2',")
        print("      'r': '10.10.10.3'")
        print("  }")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        manager.close()
        print(f"\n✅ Example completed")

if __name__ == "__main__":
    main()
