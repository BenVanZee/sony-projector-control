#!/usr/bin/env python3
"""
Command-line interface for Sony Projector Control
Usage: python projector_cli.py [command] [options]
"""

import sys
import argparse
from projector_control import ProjectorManager

def main():
    parser = argparse.ArgumentParser(description='Control Sony VPL-PHZ61 projectors')
    parser.add_argument('command', choices=['status', 'power', 'mute'], 
                       help='Command to execute')
    parser.add_argument('--action', choices=['on', 'off', 'toggle'], 
                       help='Action for power/mute commands')
    parser.add_argument('--projectors', nargs='+', 
                       default=['left', 'right'],
                       help='Projector nicknames or IPs (default: left right)')
    parser.add_argument('--port', type=int, default=4352,
                       help='PJLink port (default: 4352)')
    
    args = parser.parse_args()
    
    # Import config for aliases
    try:
        from config import PROJECTORS, PROJECTOR_ALIASES
        aliases = PROJECTOR_ALIASES
    except ImportError:
        aliases = {
            'left': '10.10.10.2',
            'right': '10.10.10.3',
            'l': '10.10.10.2',
            'r': '10.10.10.3'
        }
    
    # Convert nicknames to IPs
    projector_ips = []
    for projector in args.projectors:
        if projector in aliases:
            projector_ips.append(aliases[projector])
        else:
            projector_ips.append(projector)  # Assume it's already an IP
    
    # Create projector list
    projectors = [(ip, args.port) for ip in projector_ips]
    manager = ProjectorManager(projectors, aliases)
    
    try:
        if args.command == 'status':
            status = manager.get_all_status()
            for ip, info in status.items():
                nickname = manager.get_nickname_by_ip(ip)
                display_name = f"{nickname} ({ip})" if nickname else ip
                print(f"{display_name}: Power={info['power']}, Mute={info['mute']}, Online={info['online']}")
                
        elif args.command == 'power':
            if not args.action:
                print("Error: --action required for power command")
                sys.exit(1)
                
            if args.action == 'on':
                results = manager.power_all(True)
                print("Power ON results:", results)
            elif args.action == 'off':
                results = manager.power_all(False)
                print("Power OFF results:", results)
            elif args.action == 'toggle':
                # Get current status and toggle
                status = manager.get_all_status()
                for ip, info in status.items():
                    if info['power'] == 'ON':
                        manager.power_all(False)
                        print("Turned all projectors OFF")
                    else:
                        manager.power_all(True)
                        print("Turned all projectors ON")
                    break
                    
        elif args.command == 'mute':
            if not args.action:
                print("Error: --action required for mute command")
                sys.exit(1)
                
            if args.action == 'on':
                results = manager.mute_all(True)
                print("Mute results:", results)
            elif args.action == 'off':
                results = manager.mute_all(False)
                print("Unmute results:", results)
            elif args.action == 'toggle':
                # Get current status and toggle
                status = manager.get_all_status()
                for ip, info in status.items():
                    if info['mute'] == 'MUTED':
                        manager.mute_all(False)
                        print("Unmuted all projectors")
                    else:
                        manager.mute_all(True)
                        print("Muted all projectors")
                    break
                    
    finally:
        manager.close()

if __name__ == "__main__":
    main()
