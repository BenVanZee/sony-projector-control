#!/usr/bin/env python3
"""
Test PJLink Commands on Rear Projector
Discover which commands the rear projector actually supports
"""

import socket
import time

def test_pjlink_command(ip, port, command, description):
    """Test a specific PJLink command on the rear projector"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        
        # Read initial connection message
        initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"Connected: {initial_msg.strip()}")
        
        # Send command
        sock.sendall(command.encode('ascii'))
        print(f"Sent: {command.strip()}")
        
        # Receive response
        response = sock.recv(1024).decode('ascii', errors='ignore')
        print(f"Response: {response.strip()}")
        
        # Determine if command is supported
        if response.startswith('%') and 'ERR' not in response:
            print(f"✅ {description}: SUPPORTED")
            return True
        elif 'ERR' in response:
            print(f"❌ {description}: NOT SUPPORTED ({response.strip()})")
            return False
        else:
            print(f"⚠️  {description}: UNKNOWN RESPONSE")
            return False
            
    except Exception as e:
        print(f"❌ {description}: CONNECTION ERROR - {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    """Test various PJLink commands on the rear projector"""
    ip = '10.10.10.4'
    port = 4352
    
    print("="*60)
    print("Testing PJLink Commands on Rear Projector (10.10.10.4)")
    print("="*60)
    
    # Standard PJLink commands to test
    commands_to_test = [
        ("%1POWR ?\r", "Power Status Query"),
        ("%1POWR 1\r", "Power ON Command"),
        ("%1POWR 0\r", "Power OFF Command"),
        ("%1AVMT ?\r", "Mute Status Query"),
        ("%1AVMT 31\r", "Mute ON Command"),
        ("%1AVMT 30\r", "Mute OFF Command"),
        ("%2FREZ ?\r", "Freeze Status Query"),
        ("%2FREZ 1\r", "Freeze ON Command"),
        ("%2FREZ 0\r", "Freeze OFF Command"),
        ("%1LAMP ?\r", "Lamp Hours Query"),
        ("%1INPT ?\r", "Input Status Query"),
        ("%1ERST ?\r", "Error Status Query"),
        ("%1INF1 ?\r", "Product Name Query"),
        ("%1INF2 ?\r", "Manufacturer Query"),
        ("%1INFO ?\r", "Product Info Query"),
        ("%1CLSS ?\r", "Class Query"),
    ]
    
    # Alternative freeze commands (some projectors use different commands)
    alternative_commands = [
        ("%1AVMT 32\r", "Alternative Freeze 1 (AVMT 32)"),
        ("%1AVMT 33\r", "Alternative Freeze 2 (AVMT 33)"),
        ("%1AVMT 34\r", "Alternative Freeze 3 (AVMT 34)"),
        ("%1AVMT 35\r", "Alternative Freeze 4 (AVMT 35)"),
        ("%1AVMT 36\r", "Alternative Freeze 5 (AVMT 36)"),
        ("%1AVMT 37\r", "Alternative Freeze 6 (AVMT 37)"),
        ("%1AVMT 38\r", "Alternative Freeze 7 (AVMT 38)"),
        ("%1AVMT 39\r", "Alternative Freeze 8 (AVMT 39)"),
    ]
    
    print("\nTesting Standard PJLink Commands:")
    print("-" * 40)
    
    supported_commands = []
    for command, description in commands_to_test:
        print(f"\n{description}:")
        if test_pjlink_command(ip, port, command, description):
            supported_commands.append((command, description))
        time.sleep(1)  # Small delay between commands
    
    print("\nTesting Alternative Freeze Commands:")
    print("-" * 40)
    
    freeze_alternatives = []
    for command, description in alternative_commands:
        print(f"\n{description}:")
        if test_pjlink_command(ip, port, command, description):
            freeze_alternatives.append((command, description))
        time.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    print(f"\n✅ Supported Commands ({len(supported_commands)}):")
    for command, description in supported_commands:
        print(f"  {description}: {command.strip()}")
    
    if freeze_alternatives:
        print(f"\n🎯 Freeze Alternatives Found ({len(freeze_alternatives)}):")
        for command, description in freeze_alternatives:
            print(f"  {description}: {command.strip()}")
    else:
        print("\n❌ No freeze alternatives found")
    
    print(f"\n📊 Total Commands Tested: {len(commands_to_test) + len(alternative_commands)}")
    print(f"📊 Commands Supported: {len(supported_commands)}")
    print(f"📊 Freeze Alternatives: {len(freeze_alternatives)}")
    
    if freeze_alternatives:
        print("\n💡 Recommendation: Use one of the freeze alternatives for the rear projector")
    else:
        print("\n⚠️  Warning: Rear projector may not support freeze functionality")

if __name__ == "__main__":
    main()

