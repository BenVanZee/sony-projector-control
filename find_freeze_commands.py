#!/usr/bin/env python3
"""
Find Working Freeze Commands for Sony VPL-PHZ61
Systematically tests different PJLink commands to find what works
"""

import socket
import time
import sys

def test_command(ip, port, command, description):
    """Test a single PJLink command"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))
        
        # Read initial message
        initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
        
        # Send command
        sock.sendall(command.encode('ascii'))
        
        # Receive response
        response = sock.recv(1024).decode('ascii', errors='ignore')
        
        # Check if successful
        success = response == "%1AVMT=OK" or response.startswith("%1AVMT=")
        
        sock.close()
        return success, response.strip()
        
    except Exception as e:
        return False, str(e)

def test_projector_commands(ip, port):
    """Test various commands systematically"""
    print(f"\n🔍 Testing {ip}:{port}")
    print("=" * 50)
    
    # Test different AVMT commands
    commands = [
        ("%1AVMT 30\r", "Normal/Unmute"),
        ("%1AVMT 31\r", "Mute (Black Screen)"),
        ("%1AVMT 32\r", "Freeze (Standard) - CAUSES BLACK SCREEN"),
        ("%1AVMT 33\r", "Freeze (Alternative)"),
        ("%1AVMT 34\r", "Freeze (Extended)"),
        ("%1AVMT 35\r", "Freeze (Alternative 2)"),
        ("%1AVMT 36\r", "Freeze (Alternative 3)"),
        ("%1AVMT 37\r", "Freeze (Alternative 4)"),
        ("%1AVMT 38\r", "Freeze (Alternative 5)"),
        ("%1AVMT 39\r", "Freeze (Alternative 6)"),
    ]
    
    results = {}
    
    for command, description in commands:
        print(f"\n🔧 Testing: {description}")
        success, response = test_command(ip, port, command, description)
        
        if success:
            print(f"  ✅ SUCCESS: {response}")
        else:
            print(f"  ❌ FAILED: {response}")
            
        results[command] = (success, response)
        
        # Brief pause between commands
        time.sleep(0.5)
        
    return results

def main():
    """Main test function"""
    print("❄️ Finding Working Freeze Commands for Sony VPL-PHZ61")
    print("=" * 60)
    print("This script will test different PJLink commands to find")
    print("which ones work for freezing without causing a black screen.")
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
        
    # Summary and recommendations
    print("\n" + "=" * 60)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 60)
    
    for ip, results in all_results.items():
        print(f"\n{ip}:")
        
        # Find working freeze commands (excluding 31 and 32)
        working_freeze = []
        for command, (success, response) in results.items():
            if success and "Freeze" in command and "31" not in command and "32" not in command:
                working_freeze.append(command.strip())
                
        if working_freeze:
            print(f"  ✅ Working freeze commands: {', '.join(working_freeze)}")
            print(f"  💡 Use these instead of AVMT 32")
        else:
            print(f"  ❌ No freeze commands work properly")
            print(f"  💡 Use mute (AVMT 31) as fallback")
            
        # Check what causes black screen
        black_screen_commands = []
        for command, (success, response) in results.items():
            if success and ("31" in command or "32" in command):
                black_screen_commands.append(command.strip())
                
        if black_screen_commands:
            print(f"  ⚠️  Commands that cause black screen: {', '.join(black_screen_commands)}")
            
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Run this script to see what commands work")
    print("2. Look for commands that return 'OK' but don't cause black screen")
    print("3. Update the freeze function to use working commands")
    print("4. If no freeze works, use mute as fallback")

if __name__ == "__main__":
    main()
