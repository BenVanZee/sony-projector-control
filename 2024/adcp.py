import socket
import time
import struct

PROJECTOR_IP = "10.10.10.2"
PROJECTOR_PORT = 53595

def create_adcp_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
    return sock

def send_adcp_command(sock, command):
    cmd = struct.pack('>I', len(command)) + command.encode('ascii')
    sock.sendall(cmd)
    response = sock.recv(1024)
    return response[4:].decode('ascii')  # Remove the 4-byte length header

def get_power_status(sock):
    return send_adcp_command(sock, "POWR ?\r")

def get_mute_status(sock):
    return send_adcp_command(sock, "AVMT ?\r")

try:
    with create_adcp_connection() as sock:
        while True:
            power_status = get_power_status(sock)
            mute_status = get_mute_status(sock)
            print(f"Power: {power_status.strip()}, Picture Mute: {mute_status.strip()}")
            time.sleep(1)  # Check every second
except Exception as e:
    print(f"Connection lost: {e}")