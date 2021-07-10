# module to interface the 3D SpaceMouse

import time
import spacemouse

def loop(camera):
  """
  Main loop to handle mouse input and apply it to the camera.
  :param camera: the camera object as defined in camera.py, used to control the PTZ camera.
  """
  
  # get handle to space mouse
  space_mouse = spacemouse.SpaceMouse()
  
  while True:
    print(space_mouse.control, space_mouse.is_left_button_pressed, space_mouse.is_right_button_pressed)
    time.sleep(0.2)
