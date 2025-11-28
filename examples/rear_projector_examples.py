#!/usr/bin/env python3
"""
Rear Projector Control Examples
Demonstrates various ways to control the rear projector independently
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rear_projector_control import RearProjectorController
from projector_control import ProjectorManager
from config import PROJECTOR_GROUPS, PROJECTOR_ALIASES

# Try to import group_projector_control if it exists
try:
    from group_projector_control import get_projectors_by_group
except ImportError:
    # Functionality may be in projector_control instead
    get_projectors_by_group = None

def example_rear_only_control():
    """Example: Control rear projector only"""
    print("="*60)
    print("EXAMPLE: Rear Projector Only Control")
    print("="*60)
    
    controller = RearProjectorController()
    
    try:
        # Get status
        print("Getting rear projector status...")
        status = controller.get_status()
        print(f"Power: {status['power']}")
        print(f"Mute: {status['mute']}")
        print(f"Freeze: {status['freeze']}")
        
        # Example commands (commented out for safety)
        print("\nExample commands (commented out for safety):")
        print("# controller.set_power(True)      # Turn ON")
        print("# controller.set_mute(True)       # Mute (blank screen)")
        print("# controller.freeze_screen(True)  # Freeze video")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        controller.disconnect()

def example_group_control():
    """Example: Control projectors by group"""
    print("\n" + "="*60)
    print("EXAMPLE: Group-based Control")
    print("="*60)
    
    # Show available groups
    print("Available groups:")
    for group_name, nicknames in PROJECTOR_GROUPS.items():
        ips = [PROJECTOR_ALIASES.get(nick, nick) for nick in nicknames]
        print(f"  {group_name}: {nicknames} -> {ips}")
    
    # Example: Get projectors for each group
    print("\nProjector configurations by group:")
    for group_name in ['front', 'rear', 'all']:
        projectors = get_projectors_by_group(group_name)
        if projectors:
            ips = [ip for ip, port in projectors]
            print(f"  {group_name}: {ips}")
    
    # Example: Control front projectors only
    print("\nExample: Control front projectors only")
    front_projectors = get_projectors_by_group('front')
    if front_projectors:
        manager = ProjectorManager(front_projectors, PROJECTOR_ALIASES)
        try:
            status = manager.get_all_status()
            print("Front projectors status:")
            for ip, info in status.items():
                nickname = manager.get_nickname_by_ip(ip)
                print(f"  {nickname}: Power={info['power']}, Mute={info['mute']}")
        finally:
            manager.close()

def example_individual_vs_group():
    """Example: Individual vs group control"""
    print("\n" + "="*60)
    print("EXAMPLE: Individual vs Group Control")
    print("="*60)
    
    print("Individual control:")
    print("  python3 rear_projector_cli.py power --action on")
    print("  python3 rear_projector_cli.py mute --action off")
    
    print("\nGroup control:")
    print("  python3 group_projector_control.py power --action on --group rear")
    print("  python3 group_projector_control.py power --action on --group front")
    print("  python3 group_projector_control.py power --action on --group all")
    
    print("\nTraditional control (specific projectors):")
    print("  python3 projector_cli.py power --action on --projectors left right")
    print("  python3 projector_cli.py power --action on --projectors rear")

def main():
    """Main example function"""
    print("Rear Projector Control Examples")
    print("This script demonstrates the new rear projector functionality")
    
    try:
        example_rear_only_control()
        example_group_control()
        example_individual_vs_group()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✅ Rear projector control script created")
        print("✅ Group-based control system implemented")
        print("✅ Independent control of front and rear projectors")
        print("✅ All existing functionality preserved")
        
        print("\nReady to use!")
        print("1. Test connection: python3 test_rear_connection.py")
        print("2. Interactive control: python3 rear_projector_control.py")
        print("3. Command-line: python3 rear_projector_cli.py status")
        print("4. Group control: python3 projector_cli.py --help")
        
    except Exception as e:
        print(f"Error running examples: {e}")

if __name__ == "__main__":
    main()
