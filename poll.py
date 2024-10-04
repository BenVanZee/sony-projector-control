import socket
import time

PROJECTOR_IP = "10.10.10.2"
PROJECTOR_PORT = 4352  # Standard PJ Link port

def send_pjlink_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        try:
            sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
            # Read the initial connection message
            initial_msg = sock.recv(1024).decode('ascii', errors='ignore')
            print(f"Initial message: {initial_msg.strip()}")
            
            # Send the command
            print(f"Sending command: {command}")
            sock.sendall(command.encode('ascii'))
            
            # Receive the response
            response = sock.recv(1024).decode('ascii', errors='ignore')
            print(f"Received response: {response.strip()}")
            
            return response.strip()
        except Exception as e:
            print(f"Error: {e}")
            return None

def get_power_status():
    return send_pjlink_command("%1POWR ?\r")

def get_mute_status():
    return send_pjlink_command("%1AVMT ?\r")

def main():
    while True:
        print("\nQuerying projector status...")
        
        power_status = get_power_status()
        if power_status:
            if power_status == "%1POWR=0":
                print("Projector is powered off")
            elif power_status == "%1POWR=1":
                print("Projector is powered on")
            else:
                print(f"Unknown power status: {power_status}")
        
        mute_status = get_mute_status()
        if mute_status:
            if mute_status == "%1AVMT=30":
                print("Video and Audio are unmuted")
            elif mute_status == "%1AVMT=31":
                print("Video and Audio are muted")
            else:
                print(f"Unknown mute status: {mute_status}")
        
        print("-" * 50)
        time.sleep(5)  # Wait 5 seconds before next query

if __name__ == "__main__":
    main()