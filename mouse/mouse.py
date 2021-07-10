# module to interface the 3D SpaceMouse

import time
import spacemouse
import numpy as np
import pickle

def loop(camera):
  """
  Main loop to handle mouse input and apply it to the camera.
  :param camera: the camera object as defined in camera.py, used to control the PTZ camera.
  """
  
  # get handle to space mouse
  space_mouse = spacemouse.SpaceMouse()

  #camera.send_command("Tally", True)
  #time.sleep(5.0)
  #camera.send_command("Tally_Mode")
  #time.sleep(5.0)
  #camera.send_command("Tally_Mode")
  #time.sleep(5.0)
  #camera.send_command("Tally", False)
  
  button_pressed = [False, False]
  time_button_press = [0,0]
  is_pan_tilt_in_progress = False
  is_zoom_in_progress = False
  
  while True:
    # control contains: [x,y,z,roll,pitch,yaw]
    
    current_vector = np.array(space_mouse.control)
    #current_control = current_vector - initial_vector
    
    x = -current_vector[4]
    y = -current_vector[3]
    z = current_vector[5]

    print("mouse control: {} (left button: {}, right button: {})".format(
      (x,y,z), space_mouse.is_left_button_pressed, space_mouse.is_right_button_pressed))
        
    if x == 0 and y == 0 and is_pan_tilt_in_progress:
      is_pan_tilt_in_progress = False
      sequence_no = camera.send_command("Pan-tiltDrive_Stop")
      camera.wait_for_result(sequence_no)
      
    if z == 0 and is_zoom_in_progress:
      is_zoom_in_progress = False
      sequence_no = camera.send_command("CAM_Zoom_Stop")
      camera.wait_for_result(sequence_no)
        
    direction_x = 0
    direction_y = 0
    
    if x < 0:
      direction_x = -1
    elif x > 0:
      direction_x = 1
      
    if y < 0:
      direction_y = -1
    elif y > 0:
      direction_y = 1
      
    velocity_x = abs(x)
    velocity_y = abs(y)
      
    if z > 0:
      zoom_speed = (int)(z*7)
      sequence_no = camera.send_command("CAM_Zoom_Tele_Variable", zoom_speed)
      is_zoom_in_progress = True
    elif z < 0:
      zoom_speed = (int)(-z*7)
      sequence_no = camera.send_command("CAM_Zoom_Wide_Variable", zoom_speed)
      is_zoom_in_progress = True
    elif x != 0 or y != 0:
      sequence_no = camera.send_command("Pan-tiltDrive", direction_x, direction_y, velocity_x, velocity_y)
      is_pan_tilt_in_progress = True
    
    time.sleep(0.2)
    
    # left button pressed
    if not button_pressed[0] and space_mouse.is_left_button_pressed:
      button_pressed[0] = True
      time_button_press[0] = time.time()
      
    # right button pressed
    elif not button_pressed[1] and space_mouse.is_right_button_pressed:
      button_pressed[1] = True
      time_button_press[1] = time.time()
      
    # left button released
    elif button_pressed[0] and not space_mouse.is_left_button_pressed:
      press_duration = time.time() - time_button_press[0]
      
      # long press
      if press_duration >= 2:
        
        # get current absolute position
        sequence_no = camera.send_command("Pan-tiltPosInq")
        pos_xy = camera.wait_for_result(sequence_no)
        
        sequence_no = camera.send_command("CAM_OpticalZoomPosInq")
        pos_zoom = camera.wait_for_result(sequence_no)
        
        print("Save position 1 (x,y,zoom) = ({},{},{})".format(pos_xy[0], pos_xy[1], pos_zoom))
        
        with open("pos1", "wb") as f:
          pickle.dump((pos_xy, pos_zoom), f)
      
      # short press
      else:
        with open("pos1", "rb") as f:
          (pos_xy, pos_zoom) = pickle.load(f)
        
        print("Load position 1 (x,y,zoom) = ({},{},{})".format(pos_xy[0], pos_xy[1], pos_zoom))
        
        # Pan-tiltDrive_absolute(x,y,vx,vy)
        sequence_no = camera.send_command("Pan-tiltDrive_absolute", pos_xy[0], pos_xy[1], 0.8, 0.8)
        camera.wait_for_result(sequence_no)
    
        # CAM_Zoom_Direct_Speed(float f, int speed)
        sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", pos_zoom, 0.8)
      
    # right button released
    elif button_pressed[1] and not space_mouse.is_right_button_pressed:
      press_duration = time.time() - time_button_press[1]
      
      if press_duration >= 2:
        
        # get current absolute position
        sequence_no = camera.send_command("Pan-tiltPosInq")
        pos_xy = camera.wait_for_result(sequence_no)
        
        sequence_no = camera.send_command("CAM_OpticalZoomPosInq")
        pos_zoom = camera.wait_for_result(sequence_no)
        
        print("Save position 2 (x,y,zoom) = ({},{},{})".format(pos_xy[0], pos_xy[1], pos_zoom))
        
        with open("pos2", "wb") as f:
          pickle.dump((pos_xy, pos_zoom), f)
          
      # short press
      else:
        with open("pos2", "rb") as f:
          (pos_xy, pos_zoom) = pickle.load(f)
          
        print("Load position 2 (x,y,zoom) = ({},{},{})".format(pos_xy[0], pos_xy[1], pos_zoom))
        
        # Pan-tiltDrive_absolute(x,y,vx,vy)
        sequence_no = camera.send_command("Pan-tiltDrive_absolute", pos_xy[0], pos_xy[1], 0.8, 0.8)
        camera.wait_for_result(sequence_no)
    
        # CAM_Zoom_Direct_Speed(float f, int speed)
        sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", pos_zoom, 0.8)
        
