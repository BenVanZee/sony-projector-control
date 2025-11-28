"""
Configuration file for Sony Projector Control System
"""

# Projector network configuration
PROJECTORS = [
    {
        'ip': '10.10.10.2',
        'port': 4352,  # Standard PJLink port
        'name': 'Left',
        'nickname': 'left',
        'location': 'Main Hall - Left Side',
        'group': 'front'
    },
    {
        'ip': '10.10.10.3', 
        'port': 4352,
        'name': 'Right',
        'nickname': 'right',
        'location': 'Main Hall - Right Side',
        'group': 'front'
    },
    {
        'ip': '10.10.10.4',
        'port': 4352,
        'name': 'Rear',
        'nickname': 'rear',
        'location': 'Main Hall - Rear',
        'group': 'rear'
    }
]

# Nickname aliases for easy reference
PROJECTOR_ALIASES = {
    'left': '10.10.10.2',
    'right': '10.10.10.3',
    'rear': '10.10.10.4',
    'l': '10.10.10.2',
    'r': '10.10.10.3',
    'b': '10.10.10.4'  # 'b' for back/rear
}

# Group-based aliases for controlling multiple projectors
PROJECTOR_GROUPS = {
    'front': ['left', 'right'],      # Front projectors (left and right)
    'rear': ['rear'],                # Rear projector only
    'all': ['left', 'right', 'rear'] # All projectors
}

# Network settings
NETWORK_TIMEOUT = 10  # seconds
RECONNECT_DELAY = 5   # seconds
MAX_RETRIES = 3

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/projector_control.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# PJLink commands
PJLINK_COMMANDS = {
    'power_on': '%1POWR 1\r',
    'power_off': '%1POWR 0\r',
    'power_status': '%1POWR ?\r',
    'mute_on': '%1AVMT 31\r',
    'mute_off': '%1AVMT 30\r',
    'free_screen': '%1AVMT 30\r',  # Free screen (same as unmute)
    'freeze_on': '%2FREZ 1\r',     # Freeze screen (pause video) - CORRECT PJLink command
    'freeze_off': '%2FREZ 0\r',    # Unfreeze screen (resume video) - CORRECT PJLink command
    'freeze_status': '%2FREZ ?\r',  # Freeze status query - CORRECT PJLink command
    'mute_status': '%1AVMT ?\r',
    'lamp_hours': '%1LAMP ?\r',
    'input_status': '%1INPT ?\r',
    'error_status': '%1ERST ?\r'
}

# Status responses
POWER_STATUS = {
    '%1POWR=0': 'OFF',
    '%1POWR=1': 'ON', 
    '%1POWR=2': 'COOLING',
    '%1POWR=3': 'WARMING'
}

MUTE_STATUS = {
    '%1AVMT=30': 'NORMAL',
    '%1AVMT=31': 'MUTED'
}

FREEZE_STATUS = {
    '%2FREZ=0': 'NORMAL',
    '%2FREZ=1': 'FROZEN'
}
