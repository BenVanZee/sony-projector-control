import socket

# Projector IP and PJ Talk port
projector_ip = '10.10.10.2'
pj_talk_port = 53484  # Common port for PJ Talk

# Create the socket connection
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((projector_ip, pj_talk_port))
    
    # Command to mute the video (black screen)
    command = '%1AVMT 31\r'
    
    # Send the command
    s.send(command.encode())
    
    # Receive and print the response
    response = s.recv(1024).decode()
    print(f"Response: {response}")