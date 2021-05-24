#!/usr/bin/python3

# This is the main module which starts all functionality of the streaming software.
if __name__ == "__main__":
  import sys, os
  import time
  import datetime
  import threading
  import traceback
  import globals    # global variables
  
  print("main.py started at {}".format(time.strftime("%d.%m.%Y %H:%M:%S")))
  
  # global catch block
  try:
    
    # add subdirectories to python path
    sys.path.insert(0, 'camera')
    sys.path.insert(0, 'video')
    sys.path.insert(0, 'mouse')
    sys.path.insert(0, 'web_interface')
    
    # import scripts from subdirectories
    import camera
    import mouse
    import video
    import web_interface
    
    # initialize camera
    camera = camera.Camera()
    camera.command("debug")
    
    # start main loop for mouse in separate thread
    def mouse_thread(camera):
      mouse.loop(camera)
    
    thread = threading.Thread(group=None, target=mouse_thread, args=[camera])
    thread.start()

    # initialize video module
    video.debug()
    
    # initialize web interface
    
    print("main.py ended at {}".format(time.strftime("%d.%m.%Y %H:%M:%S")))
    
  except:
    print("An error occured at {}".format(time.strftime("%d.%m.%Y %H:%M:%S")))
    traceback.print_exc()
