# Raspberry Pi Setup Guide for Sony Projector Control

Complete setup guide for installing the projector control system on your Raspberry Pi 5.

## Quick Setup (Automated)

### 1. Download and Run Setup Script
```bash
# Download the setup script
wget https://raw.githubusercontent.com/your-repo/sony-projector-control/main/setup_pi.sh
chmod +x setup_pi.sh
sudo ./setup_pi.sh
```

### 2. Configure Your Projectors
```bash
# Edit the configuration file
sudo nano /opt/projector-control/config.py
```

### 3. Test the System
```bash
# Test basic connectivity
python3 /opt/projector-control/test_connection.py

# Test CLI commands
python3 /opt/projector-control/projector_cli.py status
```

## Manual Setup (Step by Step)

### 1. Create Project Directory
```bash
# Create the main directory
sudo mkdir -p /opt/projector-control
cd /opt/projector-control

# Set proper permissions
sudo chown pi:pi /opt/projector-control
```

### 2. Copy Project Files
```bash
# Copy all Python files to the Pi
# You can use SCP, SFTP, or Git to transfer files

# If using Git:
git clone https://github.com/your-repo/sony-projector-control.git .

# If using SCP from your computer:
# scp -r /path/to/sony-projector-control/* pi@your-pi-ip:/opt/projector-control/
```

### 3. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and GPIO support
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install GPIO library
sudo apt install -y python3-rpi.gpio

# Install USB HID support (for USB macropads)
sudo apt install -y python3-hidapi

# Install additional tools
sudo apt install -y git curl wget nano htop
```

### 4. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install any additional Python packages if needed
pip install --upgrade pip
```

### 5. Configure the System
```bash
# Make scripts executable
chmod +x *.py

# Edit configuration file
nano config.py
```

### 6. Test the Installation
```bash
# Test basic connectivity
python3 test_connection.py

# Test CLI commands
python3 projector_cli.py status

# Test GPIO (if using hardware buttons)
python3 test_gpio.py
```

## Directory Structure

Your Pi will have this structure:
```
/opt/projector-control/
├── projector_control.py      # Main control library
├── projector_cli.py          # Command-line interface
├── macropad_control.py       # Hardware button control
├── config.py                 # Configuration file
├── requirements.txt          # Python dependencies
├── test_connection.py        # Connection testing
├── test_gpio.py             # GPIO testing
├── debug_monitor.py         # Debug monitoring
├── projector_control.log    # System logs
└── venv/                    # Python virtual environment
```

## Configuration

### Edit config.py
```bash
sudo nano /opt/projector-control/config.py
```

Update with your projector IP addresses:
```python
PROJECTORS = [
    {
        'ip': '10.10.10.2',      # Your first projector IP
        'port': 4352,
        'name': 'Left',
        'nickname': 'left',
        'location': 'Main Hall - Left Side',
        'group': 'front'
    },
    {
        'ip': '10.10.10.3',      # Your second projector IP
        'port': 4352,
        'name': 'Right',
        'nickname': 'right',
        'location': 'Main Hall - Right Side',
        'group': 'front'
    }
]
```

## Running the System

### Option 1: Command Line Interface
```bash
# Check status
python3 projector_cli.py status

# Turn on all projectors
python3 projector_cli.py power --action on

# Turn off all projectors
python3 projector_cli.py power --action off

# Toggle screen blanking
python3 projector_cli.py mute --action toggle
```

### Option 2: Hardware Macropad
```bash
# Run with 4-button layout
python3 macropad_control.py --layout 4

# Run with 9-button layout
python3 macropad_control.py --layout 9
```

### Option 3: Debug Monitor
```bash
# Run debug monitor for troubleshooting
python3 debug_monitor.py
```

## Auto-Start Service

### Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/projector-control.service
```

Add this content:
```ini
[Unit]
Description=Sony Projector Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/projector-control
Environment=PATH=/opt/projector-control/venv/bin
ExecStart=/opt/projector-control/venv/bin/python3 macropad_control.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable projector-control.service

# Start service now
sudo systemctl start projector-control.service

# Check status
sudo systemctl status projector-control.service

# View logs
sudo journalctl -u projector-control.service -f
```

## Network Configuration

### Set Static IP (Recommended)
```bash
# Edit network configuration
sudo nano /etc/dhcpcd.conf
```

Add at the bottom:
```
interface eth0
static ip_address=10.10.10.100/24
static routers=10.10.10.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

### Enable SSH
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Check SSH status
sudo systemctl status ssh
```

## Testing Commands

### Basic Tests
```bash
# Test network connectivity
ping 10.10.10.2

# Test projector connection
python3 test_connection.py

# Test CLI commands
python3 projector_cli.py status
python3 projector_cli.py power --action on
python3 projector_cli.py power --action off
```

### Hardware Tests
```bash
# Test GPIO buttons (if using hardware)
python3 test_gpio.py

# Test macropad
python3 macropad_control.py --test
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   sudo chown -R pi:pi /opt/projector-control
   chmod +x /opt/projector-control/*.py
   ```

2. **GPIO Permission Issues**
   ```bash
   sudo usermod -a -G gpio pi
   # Log out and back in
   ```

3. **Network Issues**
   ```bash
   # Check network configuration
   ip addr show
   
   # Test connectivity
   ping 10.10.10.2
   ```

4. **Service Not Starting**
   ```bash
   # Check service status
   sudo systemctl status projector-control.service
   
   # View detailed logs
   sudo journalctl -u projector-control.service -n 50
   ```

### Log Files
- **System logs**: `sudo journalctl -u projector-control.service`
- **Application logs**: `/opt/projector-control/projector_control.log`
- **Debug logs**: Run `python3 debug_monitor.py`

## Security Considerations

### Firewall Setup
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow projector communication
sudo ufw allow from 10.10.10.0/24

# Enable firewall
sudo ufw enable
```

### User Permissions
```bash
# Create dedicated user (optional)
sudo useradd -m -s /bin/bash projector
sudo usermod -a -G gpio projector
sudo chown -R projector:projector /opt/projector-control
```

## Maintenance

### Update System
```bash
# Update OS
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /opt/projector-control
source venv/bin/activate
pip install --upgrade pip
```

### Backup Configuration
```bash
# Backup config
sudo cp /opt/projector-control/config.py /opt/projector-control/config.py.backup

# Backup entire system
sudo tar -czf projector-control-backup.tar.gz /opt/projector-control
```

## Next Steps

1. **Test basic connectivity** with `test_connection.py`
2. **Configure your projectors** in `config.py`
3. **Test CLI commands** with `projector_cli.py`
4. **Set up hardware buttons** (if using GPIO)
5. **Enable auto-start service** for production use
6. **Set up monitoring** with `debug_monitor.py`

Your projector control system is now ready to use!
