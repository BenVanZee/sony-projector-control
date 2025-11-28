#!/usr/bin/env python3
"""
Test script to verify connectivity to Sony projectors
Run this first to ensure your network setup is working
"""

import socket
import sys
import time

def test_network_connectivity(ip, port=4352, timeout=5):
    """Test basic network connectivity to projector"""
    print(f"Testing network connectivity to {ip}:{port}...")
    
    try:
        # Test basic ping-like connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        print(f"✅ Network connection successful to {ip}:{port}")
        sock.close()
        return True
    except socket.timeout:
        print(f"❌ Connection timeout to {ip}:{port}")
        return False
    except ConnectionRefusedError:
        print(f"❌ Connection refused to {ip}:{port} - port may be closed")
        return False
    except Exception as e:
        print(f"❌ Network error to {ip}:{port}: {e}")
        return False

def test_pjlink_handshake(ip, port=4352, timeout=10):
    """Test PJLink protocol handshake"""
    print(f"Testing PJLink handshake with {ip}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        # Read initial connection message
        initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"📡 Initial message: {initial_msg.strip()}")
        
        if initial_msg:
            print(f"✅ PJLink handshake successful with {ip}")
            sock.close()
            return True
        else:
            print(f"❌ No initial message received from {ip}")
            sock.close()
            return False
            
    except Exception as e:
        print(f"❌ PJLink handshake failed with {ip}: {e}")
        return False

def test_pjlink_command(ip, port=4352, timeout=10):
    """Test basic PJLink command"""
    print(f"Testing PJLink command with {ip}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        # Read initial message
        initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
        
        # Send power status query
        command = "%1POWR ?\r"
        sock.sendall(command.encode('ascii'))
        print(f"📤 Sent command: {command.strip()}")
        
        # Receive response
        response = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"📥 Received response: {response.strip()}")
        
        if response and response.startswith("%1POWR="):
            print(f"✅ PJLink command successful with {ip}")
            sock.close()
            return True
        else:
            print(f"❌ Unexpected response from {ip}: {response}")
            sock.close()
            return False
            
    except Exception as e:
        print(f"❌ PJLink command failed with {ip}: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Sony Projector Connection Test")
    print("=" * 60)
    
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
    
    results = {}
    
    for ip, port in projectors:
        print(f"\n🔍 Testing {ip}:{port}")
        print("-" * 40)
        
        # Test 1: Network connectivity
        network_ok = test_network_connectivity(ip, port)
        
        # Test 2: PJLink handshake (only if network is ok)
        handshake_ok = False
        if network_ok:
            handshake_ok = test_pjlink_handshake(ip, port)
        
        # Test 3: PJLink command (only if handshake is ok)
        command_ok = False
        if handshake_ok:
            command_ok = test_pjlink_command(ip, port)
        
        # Store results
        results[ip] = {
            'network': network_ok,
            'handshake': handshake_ok,
            'command': command_ok
        }
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for ip, result in results.items():
        nickname = aliases.get(ip, None)
        display_name = f"{nickname} ({ip})" if nickname else ip
        print(f"\n{display_name}:")
        print(f"  Network: {'✅ OK' if result['network'] else '❌ FAILED'}")
        print(f"  PJLink Handshake: {'✅ OK' if result['handshake'] else '❌ FAILED'}")
        print(f"  PJLink Command: {'✅ OK' if result['command'] else '❌ FAILED'}")
        
        if result['command']:
            print(f"  Status: 🟢 FULLY OPERATIONAL")
        elif result['handshake']:
            print(f"  Status: 🟡 PARTIALLY WORKING (check PJLink settings)")
        elif result['network']:
            print(f"  Status: 🟠 NETWORK ONLY (PJLink may be disabled)")
        else:
            print(f"  Status: 🔴 NOT CONNECTED")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    all_working = all(r['command'] for r in results.values())
    some_working = any(r['command'] for r in results.values())
    
    if all_working:
        print("🎉 All projectors are working correctly!")
        print("You can now use the main projector control system.")
    elif some_working:
        print("⚠️  Some projectors are working, others need attention.")
        print("Check the failed projectors' PJLink settings.")
    else:
        print("🚨 No projectors are responding to PJLink commands.")
        print("\nTroubleshooting steps:")
        print("1. Verify projector IP addresses")
        print("2. Check network connectivity")
        print("3. Ensure PJLink is enabled in projector settings")
        print("4. Check firewall rules for port 4352")
        print("5. Verify projectors are powered on")

if __name__ == "__main__":
    main()
