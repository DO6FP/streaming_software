

from message_type import *

def zoom_direct(args):
  f = args[0]
  b = int.to_bytes((int)(args[0]*16384), length=2, byteorder='big')
  return bytearray.fromhex('81 01 04 47 0{} 0{} 0{} 0{} FF'.format(b.hex()[0], b.hex()[1], b.hex()[2], b.hex()[3]))

def zoom_direct_speed(args):
  f = args[0]
  speed = args[1]
  b = int.to_bytes((int)(f*16384), length=2, byteorder='big')
  return bytearray.fromhex('81 01 04 47 0{} 0{} 0{} 0{} 0{} FF'.format(b.hex()[0], b.hex()[1], b.hex()[2], b.hex()[3], speed))

def zoom_tele_variable(args):
  return bytearray.fromhex('81 01 04 07 2{} FF'.format(args[0]))

def zoom_wide_variable(args):
  return bytearray.fromhex('81 01 04 07 3{} FF'.format(args[0]))

def pan_tilt_drive(args):
  """
  direction x,y in {-1,0,1}, 
  speed vx,vy in [0,1], (vx,vy)=(0,0) equals stop
  """
  x,y,vx,vy = args
  
  direction0 = None
  direction1 = None
  if x == 0 and y == 1:  # up
    direction0, direction1 = "3", "1"
  elif x == 0 and y == -1:  # down
    direction0, direction1 = "3", "2"
  elif x == -1 and y == 0:  # left
    direction0, direction1 = "1", "3"
  elif x == 1 and y == 0:  # right
    direction0, direction1 = "2", "3"
  elif x == -1 and y == 1:  # up left
    direction0, direction1 = "1", "1"
  elif x == 1 and y == 1:  # up right
    direction0, direction1 = "2", "1"
  elif x == -1 and y == -1:  # down left
    direction0, direction1 = "1", "2"
  elif x == 1 and y == -1:  # down right
    direction0, direction1 = "2", "2"
  else: # stop
    direction0, direction1 = "3", "3"

  # speed
  vx_binary = int.to_bytes((int)(vx*0x18), length=1, byteorder='big')
  vy_binary = int.to_bytes((int)(vy*0x18), length=1, byteorder='big')
  
  return bytearray.fromhex('81 01 06 01 {} {} 0{} 0{} FF'.format(
    vx_binary.hex(), vy_binary.hex(), direction0, direction1))

def pan_tilt_absolute(args):
  return pan_tilt_absolute_relative(args, True)
    
def pan_tilt_relative(args):
  return pan_tilt_absolute_relative(args, False)
    
def pan_tilt_absolute_relative(args, is_absolute):
  """
  position x,y in [-1,1], 
  speed vx,vy in [0,1]
  """
  x,y,vx,vy = args
  
  if is_absolute:
    relative_absolute_digit = "2"
  else:
    relative_absolute_digit = "3"
  
  # speed
  vx_binary = int.to_bytes((int)(vx*0x18), length=1, byteorder='big')
  vy_binary = int.to_bytes((int)(vy*0x18), length=1, byteorder='big')
  
  # x position (pan)
  if x > 0:
    pos_x = int.to_bytes((int)(x*0x6A40), length=2, byteorder='big')
  else:
    pos_x = int.to_bytes((int)(0x95C0 + (-x)*(0xFFFF-0x95C0)), 
                         length=2, byteorder='big')

  # y position (tilt)
  if y > 0:
    pos_y = int.to_bytes((int)(y*0x3840), length=2, byteorder='big')
  else:
    pos_y = int.to_bytes((int)(0xED40 + (-y)*(0xFFFF-0xED40)), 
                         length=2, byteorder='big')

  return bytearray.fromhex('81 01 06 0{} {} {} 0{} 0{} 0{} 0{} 0{} 0{} 0{} 0{} FF'.format(
    relative_absolute_digit, vx_binary.hex(), vy_binary.hex(), 
    pos_x.hex()[0], pos_x.hex()[1], pos_x.hex()[2], pos_x.hex()[3], 
    pos_y.hex()[0], pos_y.hex()[1], pos_y.hex()[2], pos_y.hex()[3]))

def get_optical_zoom_position(data):
  data = data.hex()
  print('get {}{}{}{}'.format(data[5], data[7], data[9], data[11]))
  zoom_bytes = bytes.fromhex('{}{}{}{}'.format(data[5], data[7], data[9], data[11]))
  return int.from_bytes(zoom_bytes, byteorder="big") / 0x4000

def get_xy_position(data):
  data = data.hex()
  #print("data in get_xy_position: {}".format(data))
  
  # x position (pan)
  x_bytes = bytes.fromhex('{}{}{}{}'.format(data[5], data[7], data[9], data[11]))
  x_int = int.from_bytes(x_bytes, byteorder="big")
  
  x_pos = 0
  if x_int <= 0x6A40:
    x_pos = x_int / 0x6A40
  else:
    x_pos = -(x_int - 0x95C0) / (0xFFFF - 0x95C0)
  
  #print("  -> x: {}{} {}{}  ->  {}  ->  {}  ->  {}".format(data[2], data[3], data[4], data[5], x_bytes.hex(), x_int, x_pos))
  
  # y position (tilt)
  y_bytes = bytes.fromhex('{}{} {}{}'.format(data[13], data[15], data[17], data[19]))
  y_int = int.from_bytes(y_bytes, byteorder="big")
  
  y_pos = 0
  if y_int <= 0x3840:
    y_pos = y_int / 0x3840
  else:
    y_pos = -(y_int - 0xED40) / (0xFFFF - 0xED40)
    
  return (x_pos, y_pos)

commands = {
  # VISCA inquiries
  "CAM_PowerInq": {
    "message_type": MessageType.VISCA_INQUIRY,
    "command_packet": lambda *args: bytearray.fromhex('81 09 04 00 FF'),
    "process_return_value": lambda data: data[2] == 0x02,
  },
  
  "CAM_VersionInq": {
    "message_type": MessageType.VISCA_INQUIRY,
    "command_packet": lambda *args: bytearray.fromhex('81 09 00 02 FF'),
    "process_return_value": lambda data: None,
  },
  
  "CAM_OpticalZoomPosInq": {
    "message_type": MessageType.VISCA_INQUIRY,
    "command_packet": lambda *args: bytearray.fromhex('81 09 04 47 FF'),
    "process_return_value": get_optical_zoom_position,
  },
  
  "Pan-tiltPosInq": {
    "message_type": MessageType.VISCA_INQUIRY,
    "command_packet": lambda *args: bytearray.fromhex('81 09 06 12 FF'),
    "process_return_value": get_xy_position,
  },
  
  # VISCA commands
  # CAM_PowerOn(bool on)
  "CAM_PowerOn": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 04 00 02 FF') if args[0] else bytearray.fromhex('81 01 04 00 03 FF')
  },
  
  # CAM_Zoom_Stop
  "CAM_Zoom_Stop": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 04 07 00 FF')
  },
  
  # CAM_Zoom_Tele
  "CAM_Zoom_Tele": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 04 07 02 FF')
  },
  
  # CAM_Zoom_Wide
  "CAM_Zoom_Wide": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 04 07 03 FF')
  },
  
  # CAM_Zoom_Tele_Step
  "CAM_Zoom_Tele_Step": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 04 07 04 FF')
  },
  
  # CAM_Zoom_Wide_Step
  "CAM_Zoom_Wide_Step": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 04 07 05 FF')
  },
  
  # CAM_Zoom_Tele_Variable(int p), speed p=0 (Low) to 7 (High)
  "CAM_Zoom_Tele_Variable": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": zoom_tele_variable,
  },
  
  # CAM_Zoom_Wide_Variable(int p), speed p=0 (Low) to 7 (High)
  "CAM_Zoom_Wide_Variable": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": zoom_wide_variable,
  },
  
  # CAM_Zoom_Direct(float f), f in [0,1] specifies the final zoom level
  "CAM_Zoom_Direct": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": zoom_direct,
  },
  
  # CAM_Zoom_Direct_Speed(float f, int speed), f in [0,1] specifies the final zoom level, speed 0: Low, 7: High
  "CAM_Zoom_Direct_Speed": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": zoom_direct_speed,
  },
  
  # Pan-tiltDrive(x,y,vx,vy), direction x,y in {-1,0,1}, speed vx,vy in [0,1], (vx,vy)=(0,0) equals stop
  "Pan-tiltDrive": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": pan_tilt_drive,
  },
  
  # Pan-tiltDrive_Stop
  "Pan-tiltDrive_Stop": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 06 01 0C 0C 03 03 FF')
  },
  
  # Pan-tiltDrive_relative(x,y,vx,vy), position x,y in [-1,1], speed vx,vy in [0,1]
  "Pan-tiltDrive_relative": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": pan_tilt_relative,
  },
  # Pan-tiltDrive_absolute(x,y,vx,vy), position x,y in [-1,1], speed vx,vy in [0,1]
  "Pan-tiltDrive_absolute": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": pan_tilt_absolute,
  },
  
  # Pan-tiltDrive_Home
  "Pan-tiltDrive_Home": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 06 04 FF')
  },
  
  # Pan-tiltDrive_Reset
  "Pan-tiltDrive_Reset": {
    "message_type": MessageType.VISCA_COMMAND,
    "command_packet": lambda *args: bytearray.fromhex('81 01 06 05 FF')
  },
  
  
}
