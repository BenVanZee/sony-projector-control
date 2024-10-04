import socket

PROJECTOR_IP = "10.10.10.2"
PROJECTOR_PORT = 53484
COMMUNITY = "SONY"
BLANK_SCREEN_COMMAND = f"{COMMUNITY}\x02VIDO\x03001\x03"  # Changed VID to VIDO and adjusted the command
UNBLANK_SCREEN_COMMAND = f"{COMMUNITY}\x02VIDO\x03000\x03"

def send_command(command):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((PROJECTOR_IP, PROJECTOR_PORT))
            print(f"Connected to projector")
            
            s.sendall(command.encode('ascii'))
            print(f"Sent command: {command}")
            
            response = s.recv(1024).decode('ascii')
            print(f"Response from projector: {response}")
            
            if response.startswith(f"{COMMUNITY}"):
                print("Command acknowledged")
                return True
            else:
                print("Command not acknowledged")
                return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# Try to blank the screen
print("Attempting to blank the screen...")
if send_command(BLANK_SCREEN_COMMAND):
    print("Screen blanked successfully")
else:
    print("Failed to blank screen")

# Wait for user input before unblanking
input("Press Enter to unblank the screen...")

# Try to unblank the screen
print("Attempting to unblank the screen...")
if send_command(UNBLANK_SCREEN_COMMAND):
    print("Screen unblanked successfully")
else:
    print("Failed to unblank screen")