#!/usr/bin/python3
# adapted from:
# https://raw.githubusercontent.com/ARISE-Initiative/robosuite/master/robosuite/devices/spacemouse.py
# by ARISE Initiative
# MIT-license

"""Driver class for SpaceMouse controller.

This class provides a driver support to SpaceMouse on Mac OS X.
In particular, we assume you are using a SpaceMouse Wireless by default.

To set up a new SpaceMouse controller:
  1. Download and install driver from https://www.3dconnexion.com/service/drivers.html
  2. Install hidapi library through pip
     (make sure you run uninstall hid first if it is installed).
  3. Make sure SpaceMouse is connected before running the script
  4. (Optional) Based on the model of SpaceMouse, you might need to change the
     vendor id and product id that correspond to the device.

For Linux support, you can find open-source Linux drivers and SDKs online.
  See http://spacenav.sourceforge.net/

"""

import time
import threading
import numpy as np

try:
  import hid
except ModuleNotFoundError as exc:
  raise ImportError("Unable to load module hid, required to interface with SpaceMouse. ") from exc

def to_int16(y1, y2):
  """
  Convert two 8 bit bytes to a signed 16 bit integer.

  Args:
    y1 (int): 8-bit byte
    y2 (int): 8-bit byte

  Returns:
    int: 16-bit integer
  """
  x = (y1) | (y2 << 8)
  if x >= 32768:
    x = -(65536 - x)
  return x


def scale_to_control(x, axis_scale=350., min_v=-1.0, max_v=1.0):
  """
  Normalize raw HID readings to target range.

  Args:
    x (int): Raw reading from HID
    axis_scale (float): (Inverted) scaling factor for mapping raw input value
    min_v (float): Minimum limit after scaling
    max_v (float): Maximum limit after scaling

  Returns:
    float: Clipped, scaled input from HID
  """
  x = x / axis_scale
  x = min(max(x, min_v), max_v)
  return x


def convert(b1, b2):
  """
  Converts SpaceMouse message to commands.

  Args:
    b1 (int): 8-bit byte
    b2 (int): 8-bit byte

  Returns:
    float: Scaled value from Spacemouse message
  """
  return scale_to_control(to_int16(b1, b2))


class SpaceMouse:
  """
  A minimalistic driver class for SpaceMouse with HID library.

  Note: Use hid.enumerate() to view all USB human interface devices (HID).
  Make sure SpaceMouse is detected before running the script.
  You can look up its vendor/product id from this method.

  Args:
    vendor_id (int): HID device vendor id
    product_id (int): HID device product id
  """

  def __init__(self,
         vendor_id=9583,
         product_id=50734
         ):

    print("Waiting until SpaceMouse device is available . . .")
    while True:
      try:
        self.device = hid.device()
        self.device.open(vendor_id, product_id)  # SpaceMouse
        break
      except:
        time.sleep(0.2)

    print("SpaceMouse found.")
    print("Manufacturer: {}".format(self.device.get_manufacturer_string()))
    print("Product:      {}".format(self.device.get_product_string()))

    # 6-DOF variables
    self.x, self.y, self.z = 0, 0, 0
    self.roll, self.pitch, self.yaw = 0, 0, 0

    self.is_left_button_pressed = False
    self.is_right_button_pressed = False

    self._control = [0., 0., 0., 0., 0., 0.]
    self._reset_state = 0
    self.rotation = np.array([[-1., 0., 0.], [0., 1., 0.], [0., 0., -1.]])
    self._enabled = True

    # launch a new listener thread to listen to SpaceMouse
    self.thread = threading.Thread(target=self.run)
    self.thread.daemon = True
    self.thread.start()

  def run(self):
    """Listener method that keeps pulling new messages."""

    t_last_click = -1

    while True:
      d = self.device.read(13)
      if d is not None and self._enabled:

        if d[0] == 1:  ## readings from 6-DoF sensor
          self.y = convert(d[1], d[2])
          self.x = convert(d[3], d[4])
          self.z = convert(d[5], d[6]) * -1.0

          self.roll = convert(d[7], d[8])
          self.pitch = convert(d[9], d[10])
          self.yaw = convert(d[11], d[12])

          self._control = [
            self.x,
            self.y,
            self.z,
            self.roll,
            self.pitch,
            self.yaw,
          ]

        elif d[0] == 3:  ## readings from the side buttons

          print("buttons: {}".format(d[1]))

          self.is_left_button_pressed = True if d[1] % 2 == 1 else False
          self.is_right_button_pressed = True if d[1] // 2 == 1 else False
          
  @property
  def control(self):
    """
    Grabs current pose of Spacemouse

    Returns:
      np.array: 6-DoF control value
    """
    return np.array(self._control)

if __name__ == "__main__":

  space_mouse = SpaceMouse()
  for i in range(100000):
    print(space_mouse.control, space_mouse.is_left_button_pressed, space_mouse.is_right_button_pressed)
    time.sleep(0.02)
