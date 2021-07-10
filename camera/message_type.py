
from enum import Enum, auto

class MessageType(Enum):
  VISCA_COMMAND = auto(),
  VISCA_INQUIRY = auto(),
  VISCA_REPLY = auto(),
  VISCA_DEVICE_SETTING_COMMAND = auto(),
  CONTROL_COMMAND = auto(),
  CONTROL_REPLY = auto(),
  OTHER = auto()
