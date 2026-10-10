#!/usr/bin/env python3
"""
USB Keypad Configuration for Sony Projector Control
Supports various 4-button USB keypads including Cut/Copy/Paste keypads
"""

from pynput.keyboard import Key, KeyCode

# Button function definitions
BUTTON_FUNCTIONS = {
    1: "Turn projectors OFF",
    2: "Turn projectors ON", 
    3: "Toggle screen blanking",
    4: "Toggle screen freezing"
}

# Keypad configurations for different USB keypads
KEYPAD_CONFIGS = {
    # Standard 4-button keypad (Ctrl, C, V, Enter)
    "standard": {
        Key.ctrl: 1,        # Ctrl key - Turn projectors OFF
        KeyCode.from_char('c'): 2,  # C key - Turn projectors ON
        KeyCode.from_char('v'): 3,  # V key - Toggle screen blanking
        Key.enter: 4,       # Enter key - Toggle screen freezing
    },
    
    # Cut/Copy/Paste keypad (Ctrl+X, Ctrl+C, Ctrl+V, Enter)
    "cut_copy_paste": {
        KeyCode.from_char('x'): 1,  # Cut (Ctrl+X) - Turn projectors OFF
        KeyCode.from_char('c'): 2,  # Copy (Ctrl+C) - Turn projectors ON
        KeyCode.from_char('v'): 3,  # Paste (Ctrl+V) - Toggle screen blanking
        Key.enter: 4,       # Enter key - Toggle screen freezing
    },
    
    # Alternative Cut/Copy/Paste keypad (if keys are different)
    "cut_copy_paste_alt": {
        KeyCode.from_char('x'): 1,  # Cut key - Turn projectors OFF
        KeyCode.from_char('c'): 2,  # Copy key - Turn projectors ON
        KeyCode.from_char('v'): 3,  # Paste key - Toggle screen blanking
        KeyCode.from_char('z'): 4,  # Undo key - Toggle screen freezing
    },
    
    # Function key keypad (F1, F2, F3, F4)
    "function_keys": {
        Key.f1: 1,          # F1 - Turn projectors OFF
        Key.f2: 2,          # F2 - Turn projectors ON
        Key.f3: 3,          # F3 - Toggle screen blanking
        Key.f4: 4,          # F4 - Toggle screen freezing
    },
    
    # Number keypad (1, 2, 3, 4)
    "number_keys": {
        KeyCode.from_char('1'): 1,  # 1 - Turn projectors OFF
        KeyCode.from_char('2'): 2,  # 2 - Turn projectors ON
        KeyCode.from_char('3'): 3,  # 3 - Toggle screen blanking
        KeyCode.from_char('4'): 4,  # 4 - Toggle screen freezing
    }
}

def get_keypad_config(keypad_type="cut_copy_paste"):
    """
    Get keypad configuration for specified type
    
    Args:
        keypad_type (str): Type of keypad to use
        
    Returns:
        dict: Key mappings for the keypad
    """
    return KEYPAD_CONFIGS.get(keypad_type, KEYPAD_CONFIGS["cut_copy_paste"])

def list_available_configs():
    """List all available keypad configurations"""
    print("Available keypad configurations:")
    for config_name, config in KEYPAD_CONFIGS.items():
        print(f"\n{config_name}:")
        for key, button in config.items():
            print(f"  {key} → Button {button}: {BUTTON_FUNCTIONS[button]}")

if __name__ == "__main__":
    list_available_configs()
