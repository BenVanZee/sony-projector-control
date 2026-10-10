#!/usr/bin/env python3
"""
Run macropad control scripts with mock projectors
This allows testing macropad functionality without real hardware
"""

import sys
import os
import time
import argparse

# Add tests directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
from mock_macropad_integration import MockMacropadEnvironment, mock_projector_config


def run_usb_keypad_with_mocks(keypad_type: str = "cut_copy_paste", num_projectors: int = 2, **projector_states):
    """Run USB keypad control with mock projectors"""
    from macropad.usb_keypad_control import USBKeypadController
    
    print("🎭 Starting USB Keypad Control with MOCK PROJECTORS")
    print("=" * 60)
    
    # Create mock environment
    mock_env = MockMacropadEnvironment(num_projectors=num_projectors, **projector_states)
    projectors = mock_env.start()
    
    print(f"✅ Created {len(projectors)} mock projectors:")
    for i, (ip, port) in enumerate(projectors):
        state = mock_env.get_state(i)
        print(f"   Projector {i+1}: {ip}:{port} (Power: {state.get('power', 'UNKNOWN')})")
    
    try:
        # Convert to config format
        mock_projector_config = [
            {'ip': ip, 'port': port} for ip, port in projectors
        ]
        
        # Create controller
        controller = USBKeypadController(
            projectors=mock_projector_config,
            keypad_type=keypad_type,
            debug_mode=True
        )
        
        print("\n🎹 USB Keypad Control Ready!")
        print("   Press buttons on your keypad to test")
        print("   (All commands will go to mock projectors)")
        print("   Press ESC to exit\n")
        
        controller.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        mock_env.stop()
        print("✅ Mock projectors stopped")


def run_macropad_with_mocks(button_layout: str = "4", num_projectors: int = 2, **projector_states):
    """Run macropad control with mock projectors"""
    from macropad.macropad_control import MacropadController
    
    print("🎭 Starting Macropad Control with MOCK PROJECTORS")
    print("=" * 60)
    
    # Create mock environment
    mock_env = MockMacropadEnvironment(num_projectors=num_projectors, **projector_states)
    projectors = mock_env.start()
    
    print(f"✅ Created {len(projectors)} mock projectors:")
    for i, (ip, port) in enumerate(projectors):
        state = mock_env.get_state(i)
        print(f"   Projector {i+1}: {ip}:{port} (Power: {state.get('power', 'UNKNOWN')})")
    
    try:
        # Create controller
        controller = MacropadController(
            projectors=projectors,
            debug_mode=True,
            button_layout=button_layout
        )
        
        print(f"\n🎹 {button_layout}-Button Macropad Control Ready!")
        print("   Press buttons on your macropad to test")
        print("   (All commands will go to mock projectors)")
        print("   Press ESC to exit\n")
        
        controller.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        mock_env.stop()
        print("✅ Mock projectors stopped")


def run_hid_macropad_with_mocks(num_projectors: int = 2, **projector_states):
    """Run HID macropad control with mock projectors"""
    from macropad.hid_macropad_control import HIDMacropadController
    
    print("🎭 Starting HID Macropad Control with MOCK PROJECTORS")
    print("=" * 60)
    
    # Create mock environment
    mock_env = MockMacropadEnvironment(num_projectors=num_projectors, **projector_states)
    projectors = mock_env.start()
    
    print(f"✅ Created {len(projectors)} mock projectors:")
    for i, (ip, port) in enumerate(projectors):
        state = mock_env.get_state(i)
        print(f"   Projector {i+1}: {ip}:{port} (Power: {state.get('power', 'UNKNOWN')})")
    
    try:
        # Convert to config format
        mock_projector_config = [
            {'ip': ip, 'port': port} for ip, port in projectors
        ]
        
        # Create controller
        controller = HIDMacropadController(
            projectors=mock_projector_config,
            debug_mode=True
        )
        
        print("\n🎹 HID Macropad Control Ready!")
        print("   Press buttons on your macropad to test")
        print("   (All commands will go to mock projectors)")
        print("   Press ESC to exit")
        print("\n💡 Note: If you see escape sequences (^[OP, ^[OQ, etc.)")
        print("   in the terminal, your device may be acting as a keyboard.")
        print("   Try using 'usb-keypad' instead: python run_macropad_with_mocks.py usb-keypad\n")
        
        controller.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        mock_env.stop()
        print("✅ Mock projectors stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run macropad control with mock projectors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run USB keypad with mocks (projectors start ON)
  python run_macropad_with_mocks.py usb-keypad
  
  # Run macropad with mocks (projectors start OFF)
  python run_macropad_with_mocks.py macropad --power OFF
  
  # Run with custom initial states
  python run_macropad_with_mocks.py macropad --power ON --mute MUTED --freeze FROZEN
        """
    )
    
    parser.add_argument(
        'script',
        choices=['usb-keypad', 'macropad', 'hid-macropad'],
        help='Which macropad script to run'
    )
    
    parser.add_argument(
        '--keypad-type',
        default='cut_copy_paste',
        help='USB keypad type (for usb-keypad script)'
    )
    
    parser.add_argument(
        '--layout',
        choices=['4', '9'],
        default='4',
        help='Button layout (for macropad script)'
    )
    
    # Projector state options
    parser.add_argument(
        '--power',
        choices=['ON', 'OFF', 'COOLING', 'WARMING'],
        default='ON',
        help='Initial power state'
    )
    
    parser.add_argument(
        '--mute',
        choices=['MUTED', 'UNMUTED'],
        default='UNMUTED',
        help='Initial mute state'
    )
    
    parser.add_argument(
        '--freeze',
        choices=['FROZEN', 'NORMAL'],
        default='NORMAL',
        help='Initial freeze state'
    )
    
    parser.add_argument(
        '--num-projectors',
        type=int,
        default=2,
        help='Number of mock projectors to create'
    )
    
    args = parser.parse_args()
    
    # Build projector states
    projector_states = {
        'power': args.power,
        'mute': args.mute,
        'freeze': args.freeze
    }
    
    # Run appropriate script
    if args.script == 'usb-keypad':
        run_usb_keypad_with_mocks(
            keypad_type=args.keypad_type,
            num_projectors=args.num_projectors,
            **projector_states
        )
    elif args.script == 'macropad':
        run_macropad_with_mocks(
            button_layout=args.layout,
            num_projectors=args.num_projectors,
            **projector_states
        )
    elif args.script == 'hid-macropad':
        run_hid_macropad_with_mocks(
            num_projectors=args.num_projectors,
            **projector_states
        )


if __name__ == "__main__":
    main()

