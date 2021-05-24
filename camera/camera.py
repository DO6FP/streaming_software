# module that interfaces the PTZ camera

class Camera:
  """
  This class provides an interface to the PTZ camera.
  It executes given commands on the camera using the VISCA over IP interface
  """
  
  def __init__(self):
    print("init")
  
  def command(self, command_name, *kwargs):
    print("camera command [{}]".format(command_name))
