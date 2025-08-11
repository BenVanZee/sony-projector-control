import socket

PROJECTOR_IP = "10.10.10.2"
PROJECTOR_PORT = 4352  # Standard PJ Link port
BLANK_COMMAND = "%1AVMT 31\r"
UNBLANK_COMMAND = "%1AVMT 30\r"

def send_pjlink_command(command):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
            
            # Read the initial connection message
            initial_msg = sock.recv(1024).decode('ascii')
            print(f"Initial message: {initial_msg.strip()}")
            
            # Send the command
            sock.sendall(command.encode('ascii'))
            print(f"Sent command: {command.strip()}")
            
            # Receive the response
            response = sock.recv(1024).decode('ascii')
            print(f"Response: {response.strip()}")
            
            return response.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Try to blank the screen
print("Attempting to blank the screen...")
response = send_pjlink_command(BLANK_COMMAND)
if response == "%1AVMT=OK":
    print("Screen blanked successfully")
else:
    print("Failed to blank screen")

# Wait for user input before unblanking
input("Press Enter to unblank the screen...")

# Try to unblank the screen
print("Attempting to unblank the screen...")
response = send_pjlink_command(UNBLANK_COMMAND)
if response == "%1AVMT=OK":
    print("Screen unblanked successfully")
else:
    print("Failed to unblank screen")