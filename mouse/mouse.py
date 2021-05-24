# module to interface the 3D SpaceMouse

import time

def loop(camera):
  """
  Main loop to handle mouse input and apply it to the camera.
  :param camera: the camera object as defined in camera.py, used to control the PTZ camera.
  """
  
  # The 3D SpaceMouse is enumerated as Human Interface Device (HID)
  import hid
  mouse = hid.device()
  
  while True:
    time.sleep(1)
