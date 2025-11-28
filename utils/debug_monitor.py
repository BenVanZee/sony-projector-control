#!/usr/bin/env python3
"""
Debug Monitor for Sony Projector Control System
Provides real-time monitoring and debugging capabilities
"""

import time
import threading
import socket
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projector_control import ProjectorManager

class DebugMonitor:
    """Real-time debugging and monitoring for projector system"""
    
    def __init__(self, projectors: list, log_file: str = "debug_monitor.log"):
        self.projectors = projectors
        self.log_file = log_file
        self.manager = ProjectorManager(projectors)
        self.running = False
        self.debug_data = {}
        self.command_history = []
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup debug logging"""
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_command(self, command: str, response: str, success: bool, projector_ip: str):
        """Log command execution details"""
        timestamp = datetime.now().isoformat()
        entry = {
            'timestamp': timestamp,
            'command': command,
            'response': response,
            'success': success,
            'projector_ip': projector_ip
        }
        
        self.command_history.append(entry)
        
        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history.pop(0)
            
        # Log to file
        status = "✅" if success else "❌"
        self.logger.info(f"{status} {projector_ip}: {command.strip()} -> {response}")
        
    def test_raw_connection(self, ip: str, port: int = 4352) -> Dict:
        """Test raw network connection and PJLink handshake"""
        results = {
            'network_ok': False,
            'pjlink_ok': False,
            'initial_message': None,
            'error': None
        }
        
        try:
            # Test basic connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, port))
            results['network_ok'] = True
            
            # Test PJLink handshake
            initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
            results['initial_message'] = initial_msg.strip()
            
            if initial_msg:
                results['pjlink_ok'] = True
                
            sock.close()
            
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    def test_pjlink_commands(self, ip: str, port: int = 4352) -> Dict:
        """Test various PJLink commands and responses"""
        commands = {
            'power_status': '%1POWR ?\r',
            'mute_status': '%1AVMT ?\r',
            'lamp_hours': '%1LAMP ?\r',
            'input_status': '%1INPT ?\r',
            'error_status': '%1ERST ?\r'
        }
        
        results = {}
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, port))
            
            # Read initial message
            initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
            
            for cmd_name, command in commands.items():
                try:
                    # Send command
                    sock.sendall(command.encode('ascii'))
                    
                    # Receive response
                    response = sock.recv(1024).decode('ascii', errors='ignore')
                    
                    results[cmd_name] = {
                        'command': command.strip(),
                        'response': response.strip(),
                        'success': response.startswith('%1') or response == 'OK'
                    }
                    
                except Exception as e:
                    results[cmd_name] = {
                        'command': command.strip(),
                        'response': f"Error: {e}",
                        'success': False
                    }
                    
            sock.close()
            
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    def monitor_projector_status(self, duration: int = 300):
        """Monitor projector status continuously"""
        print(f"🔍 Starting continuous monitoring for {duration} seconds...")
        print("Press Ctrl+C to stop monitoring")
        
        start_time = time.time()
        self.running = True
        
        try:
            while self.running and (time.time() - start_time) < duration:
                print("\n" + "="*60)
                print(f"Status Check at {datetime.now().strftime('%H:%M:%S')}")
                print("="*60)
                
                # Get status from manager
                status = self.manager.get_all_status()
                
                for ip, info in status.items():
                    nickname = getattr(self.manager, 'get_nickname_by_ip', lambda x: None)(ip)
                    display_name = f"{nickname} ({ip})" if nickname else ip
                    print(f"\n{display_name}:")
                    print(f"  Power: {info['power'] or 'UNKNOWN'}")
                    print(f"  Mute: {info['mute'] or 'UNKNOWN'}")
                    print(f"  Online: {'Yes' if info['online'] else 'No'}")
                    print(f"  Lamp Hours: {info['lamp_hours'] or 'UNKNOWN'}")
                    
                    # Store debug data
                    self.debug_data[ip] = {
                        'last_check': datetime.now().isoformat(),
                        'status': info
                    }
                    
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        finally:
            self.running = False
            
    def run_diagnostic_test(self):
        """Run comprehensive diagnostic test"""
        print("🔧 Running Comprehensive Diagnostic Test")
        print("="*60)
        
        for ip, port in self.projectors:
            print(f"\n📡 Testing {ip}:{port}")
            print("-" * 40)
            
            # Test 1: Raw connection
            print("1. Testing raw network connection...")
            raw_results = self.test_raw_connection(ip, port)
            
            if raw_results['network_ok']:
                print("   ✅ Network connection successful")
                print(f"   📡 Initial message: {raw_results['initial_message']}")
                
                if raw_results['pjlink_ok']:
                    print("   ✅ PJLink handshake successful")
                else:
                    print("   ❌ PJLink handshake failed")
            else:
                print(f"   ❌ Network connection failed: {raw_results['error']}")
                
            # Test 2: PJLink commands (only if connection works)
            if raw_results['network_ok']:
                print("\n2. Testing PJLink commands...")
                cmd_results = self.test_pjlink_commands(ip, port)
                
                for cmd_name, result in cmd_results.items():
                    if cmd_name == 'error':
                        print(f"   ❌ {cmd_name}: {result}")
                    else:
                        status = "✅" if result['success'] else "❌"
                        print(f"   {status} {cmd_name}: {result['response']}")
                        
            # Test 3: Manager integration
            print("\n3. Testing manager integration...")
            try:
                with self.manager.controllers[ip]:
                    power_status = self.manager.controllers[ip].get_power_status()
                    mute_status = self.manager.controllers[ip].get_mute_status()
                    
                    print(f"   ✅ Power status: {power_status}")
                    print(f"   ✅ Mute status: {mute_status}")
                    
            except Exception as e:
                print(f"   ❌ Manager test failed: {e}")
                
            print("-" * 40)
            
    def show_command_history(self, limit: int = 20):
        """Display recent command history"""
        print(f"\n📜 Recent Command History (last {limit} commands)")
        print("="*60)
        
        recent_commands = self.command_history[-limit:] if self.command_history else []
        
        if not recent_commands:
            print("No commands executed yet")
            return
            
        for entry in recent_commands:
            timestamp = entry['timestamp'][11:19]  # Just time part
            status = "✅" if entry['success'] else "❌"
            print(f"{timestamp} {status} {entry['projector_ip']}: {entry['command']}")
            if not entry['success']:
                print(f"     Response: {entry['response']}")
                
    def export_debug_data(self, filename: str = "debug_export.json"):
        """Export debug data to JSON file"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'projectors': self.projectors,
            'debug_data': self.debug_data,
            'command_history': self.command_history
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"✅ Debug data exported to {filename}")
        except Exception as e:
            print(f"❌ Failed to export debug data: {e}")
            
    def interactive_debug_mode(self):
        """Interactive debugging mode"""
        print("🔧 Interactive Debug Mode")
        print("="*50)
        print("Commands:")
        print("1. Run diagnostic test")
        print("2. Start continuous monitoring")
        print("3. Show command history")
        print("4. Export debug data")
        print("5. Test specific projector")
        print("6. Exit")
        
        while True:
            try:
                choice = input("\nEnter choice (1-6): ").strip()
                
                if choice == "1":
                    self.run_diagnostic_test()
                    
                elif choice == "2":
                    duration = input("Enter monitoring duration in seconds (default 300): ").strip()
                    try:
                        duration = int(duration) if duration else 300
                        self.monitor_projector_status(duration)
                    except ValueError:
                        print("Invalid duration, using default 300 seconds")
                        self.monitor_projector_status()
                        
                elif choice == "3":
                    limit = input("Enter number of commands to show (default 20): ").strip()
                    try:
                        limit = int(limit) if limit else 20
                        self.show_command_history(limit)
                    except ValueError:
                        self.show_command_history()
                        
                elif choice == "4":
                    filename = input("Enter export filename (default debug_export.json): ").strip()
                    filename = filename if filename else "debug_export.json"
                    self.export_debug_data(filename)
                    
                elif choice == "5":
                    self.test_specific_projector()
                    
                elif choice == "6":
                    print("Exiting debug mode...")
                    break
                    
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\nExiting debug mode...")
                break
                
    def test_specific_projector(self):
        """Test a specific projector"""
        print("\n🎯 Test Specific Projector")
        print("Available projectors:")
        
        for i, (ip, port) in enumerate(self.projectors, 1):
            print(f"{i}. {ip}:{port}")
            
        try:
            choice = input("Enter projector number: ").strip()
            projector_idx = int(choice) - 1
            
            if 0 <= projector_idx < len(self.projectors):
                ip, port = self.projectors[projector_idx]
                print(f"\nTesting {ip}:{port}")
                
                # Run tests
                raw_results = self.test_raw_connection(ip, port)
                cmd_results = self.test_pjlink_commands(ip, port)
                
                print(f"\nRaw connection: {'✅' if raw_results['network_ok'] else '❌'}")
                print(f"PJLink: {'✅' if raw_results['pjlink_ok'] else '❌'}")
                
                if cmd_results:
                    print("\nCommand responses:")
                    for cmd_name, result in cmd_results.items():
                        if cmd_name != 'error':
                            status = "✅" if result['success'] else "❌"
                            print(f"  {status} {cmd_name}: {result['response']}")
                            
            else:
                print("Invalid projector number")
                
        except (ValueError, IndexError):
            print("Invalid input")
            
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.manager.close()

def main():
    """Main function"""
    # Import config for projectors and aliases
    try:
        from config import PROJECTORS, PROJECTOR_ALIASES
        # Convert config format to tuple format
        projectors = [(p['ip'], p['port']) for p in PROJECTORS]
        aliases = PROJECTOR_ALIASES
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
    
    monitor = DebugMonitor(projectors)
    
    try:
        monitor.interactive_debug_mode()
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    main()
