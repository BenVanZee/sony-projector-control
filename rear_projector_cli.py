#!/usr/bin/env python3
"""
Command-line interface for Rear Projector Control
Usage: python rear_projector_cli.py [command] [options]
"""

import sys
import argparse
from rear_projector_control import RearProjectorController

def main():
    parser = argparse.ArgumentParser(description='Control Rear Projector (10.10.10.4)')
    parser.add_argument('command', choices=['status', 'power', 'mute', 'free', 'freeze'], 
                       help='Command to execute')
    parser.add_argument('--action', choices=['on', 'off', 'toggle'], 
                       help='Action for power/mute commands')
    parser.add_argument('--port', type=int, default=4352,
                       help='PJLink port (default: 4352)')
    
    args = parser.parse_args()
    
    controller = RearProjectorController(port=args.port)
    
    try:
        if args.command == 'status':
            status = controller.get_status()
            print(f"Rear Projector (10.10.10.4):")
            print(f"  Power: {status['power'] or 'UNKNOWN'}")
            print(f"  Mute: {status['mute'] or 'UNKNOWN'}")
            print(f"  Freeze: {status['freeze'] or 'UNKNOWN'}")
            print(f"  Lamp Hours: {status['lamp_hours'] or 'UNKNOWN'}")
            print(f"  Input: {status['input'] or 'UNKNOWN'}")
            print(f"  Error: {status['error'] or 'NONE'}")
            print(f"  Online: {'Yes' if status['online'] else 'No'}")
                
        elif args.command == 'power':
            if not args.action:
                print("Error: --action required for power command")
                sys.exit(1)
                
            if args.action == 'on':
                success = controller.set_power(True)
                print(f"Power ON: {'SUCCESS' if success else 'FAILED'}")
            elif args.action == 'off':
                success = controller.set_power(False)
                print(f"Power OFF: {'SUCCESS' if success else 'FAILED'}")
            elif args.action == 'toggle':
                # Get current status and toggle
                status = controller.get_status()
                if status['power'] == 'ON':
                    success = controller.set_power(False)
                    print(f"Turned rear projector OFF: {'SUCCESS' if success else 'FAILED'}")
                else:
                    success = controller.set_power(True)
                    print(f"Turned rear projector ON: {'SUCCESS' if success else 'FAILED'}")
                    
        elif args.command == 'mute':
            if not args.action:
                print("Error: --action required for mute command")
                sys.exit(1)
                
            if args.action == 'on':
                success = controller.set_mute(True)
                print(f"Mute: {'SUCCESS' if success else 'FAILED'}")
            elif args.action == 'off':
                success = controller.set_mute(False)
                print(f"Unmute: {'SUCCESS' if success else 'FAILED'}")
            elif args.action == 'toggle':
                # Get current status and toggle
                status = controller.get_status()
                if status['mute'] == 'MUTED':
                    success = controller.set_mute(False)
                    print(f"Unmuted rear projector: {'SUCCESS' if success else 'FAILED'}")
                else:
                    success = controller.set_mute(True)
                    print(f"Muted rear projector: {'SUCCESS' if success else 'FAILED'}")
                    
        elif args.command == 'free':
            success = controller.free_screen()
            print(f"Free screen: {'SUCCESS' if success else 'FAILED'}")
            
        elif args.command == 'freeze':
            if not args.action:
                print("Error: --action required for freeze command")
                sys.exit(1)
                
            if args.action == 'on':
                success = controller.freeze_screen(True)
                print(f"Freeze screen: {'SUCCESS' if success else 'FAILED'}")
            elif args.action == 'off':
                success = controller.freeze_screen(False)
                print(f"Unfreeze screen: {'SUCCESS' if success else 'FAILED'}")
            elif args.action == 'toggle':
                # Get current status and toggle
                status = controller.get_status()
                if status['freeze'] == 'FROZEN':
                    success = controller.freeze_screen(False)
                    print(f"Unfroze rear projector: {'SUCCESS' if success else 'FAILED'}")
                else:
                    success = controller.freeze_screen(True)
                    print(f"Froze rear projector: {'SUCCESS' if success else 'FAILED'}")
                    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
