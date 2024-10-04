from pypjlink import Projector

# Use the IP address of your projector
projector_ip = '10.10.10.2'
projector = Projector.from_address(projector_ip)

# Authenticate if needed
# projector.authenticate('password')

# Check if the projector supports Picture Muting and toggle it
if projector.get_mute() == ('video', False):
    # Turn Picture Muting on (black/blank screen)
    projector.set_mute('video', True)
    print("Picture Muting is now ON.")
else:
    # Turn Picture Muting off
    projector.set_mute('video', False)
    print("Picture Muting is now OFF.")