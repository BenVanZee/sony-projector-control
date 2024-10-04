from pjlink import PJLink

projector_ip = "10.10.10.2"  # Replace with your projector's IP
port = 4352  # Default PJLink port, change if your projector uses a different port

# Create a PJLink instance
pjlink = PJLink(projector_ip, port)

try:
    # Connect to the projector
    pjlink.connect()
    
    # Turn off the picture (blank the screen)
    #pjlink.set_video_mute(True)
    #print("Screen blanked successfully")

    # To turn the picture back on, you would use:
    pjlink.set_video_mute(False)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Always disconnect when done
    pjlink.disconnect()