#!/usr/bin/env python3
"""
Test Freeze Functionality for Sony Projectors
Debug script to see what PJLink commands are supported
"""

import socket
import time

def test_pjlink_command(ip, port, command, description):
    """Test a specific PJLink command"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))
        
        # Read initial message
        initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"  📡 Initial: {initial_msg.strip()}")
        
        # Send command
        sock.sendall(command.encode('ascii'))
        print(f"  📤 Sent: {command.strip()}")
        
        # Receive response
        response = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"  📥 Response: {response.strip()}")
        
        # Check if successful
        success = response == "%1AVMT=OK" or response.startswith("%1AVMT=")
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {status}: {description}")
        
        sock.close()
        return success, response.strip()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, str(e)

def test_projector_commands(ip, port):
    """Test various commands on a projector"""
    print(f"\n🔍 Testing {ip}:{port}")
    print("=" * 50)
    
    # Test basic commands
    commands = [
        ("%1POWR ?\r", "Power Status Query"),
        ("%1AVMT ?\r", "Mute Status Query"),
        ("%1AVMT 30\r", "Unmute Command"),
        ("%1AVMT 31\r", "Mute Command"),
        ("%1AVMT 32\r", "Freeze Command (Standard)"),
        ("%1AVMT 33\r", "Freeze Command (Alternative)"),
        ("%1AVMT 34\r", "Freeze Command (Extended)"),
        ("%1AVMT 35\r", "Freeze Command (Alternative 2)"),
    ]
    
    results = {}
    
    for command, description in commands:
        print(f"\n🔧 Testing: {description}")
        success, response = test_pjlink_command(ip, port, command, description)
        results[command] = (success, response)
        time.sleep(0.5)  # Brief pause between commands
        
    return results

def main():
    """Main test function"""
    print("❄️ Sony Projector Freeze Command Test")
    print("=" * 60)
    
    # Test projectors
    projectors = [
        ("10.10.10.2", 4352),
        ("10.10.10.3", 4352),
    ]
    
    all_results = {}
    
    for ip, port in projectors:
        results = test_projector_commands(ip, port)
        all_results[ip] = results
        
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for ip, results in all_results.items():
        print(f"\n{ip}:")
        for command, (success, response) in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {command.strip()}: {response}")
            
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    for ip, results in all_results.items():
        print(f"\n{ip}:")
        
        # Check what freeze commands work
        freeze_commands = []
        for command, (success, response) in results.items():
            if "Freeze" in command and success:
                freeze_commands.append(command.strip())
                
        if freeze_commands:
            print(f"  ✅ Supported freeze commands: {', '.join(freeze_commands)}")
        else:
            print(f"  ❌ No freeze commands supported - using mute as fallback")
            
        # Check mute support
        mute_success = results.get("%1AVMT 31\r", (False, ""))[0]
        if mute_success:
            print(f"  ✅ Mute command supported")
        else:
            print(f"  ❌ Mute command not supported")

if __name__ == "__main__":
    main()
