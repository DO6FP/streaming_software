#!/usr/bin/python3
# module that interfaces the PTZ camera 


import socket
import time
import commands
import threading
import datetime
from message_type import *
import sys
import traceback
sys.path.append('..')
import globals

class Camera:
  """
  This class provides an interface to the Marshall PTZ camera.
  It executes given commands on the camera using the VISCA over IP interface
  """  
  sequence_no = 1
  open_commands = {}
    
  def __init__(self, ip_address, port=52381):
    print("initialize VISCA-over-IP, IP address: {}, port: {}".format(ip_address, port))
    
    self.ip_address = ip_address
    self.port = port
    
    # open socket for UDP communication
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    self.reset_sequence_no()
    
    # start receive thread
    self.receiving_thread = threading.Thread(target=self.receive_loop).start()

  def receive_loop(self):
    received_message = bytes()
    bufsize = 4096
    payload = None
    
    while True:
      try:
        # receive UDP message
        b = self.socket.recv(bufsize, socket.MSG_DONTWAIT)
        received_message += b
        #print("< recv [{}]".format(received_message.hex()))
        
        # if the received message could already be complete
        if len(received_message) >= 8:
          # parse payload type
          payload_type = received_message[0:2]
          
          payload_type_str = "unknown ({})".format(payload_type)
          if payload_type == bytearray.fromhex("0111"):
            payload_type_str = "VISCA reply"
          elif payload_type == bytearray.fromhex("0201"):
            payload_type_str = "Control reply"
          
          # parse other fields and payload
          payload_length = int.from_bytes(received_message[2:4], byteorder='big')
          sequence_no = int.from_bytes(received_message[4:8], byteorder='big')
          payload = received_message[8:]
          
          # if the anounced number of bytes have been recived, end waiting loop
          if len(received_message) == 8+payload_length:
              
            # check if reply contained an error and completion notice
            payload_message = ""
            
            message_is_complete = True
            if payload == bytearray.fromhex("90 41 FF"):
              payload_message = "Ack"
            
            elif payload == bytearray.fromhex("90 51 FF"):
              payload_message = "Completion (commands)"
            
            elif payload == bytearray.fromhex("90 60 02 FF"):
              payload_message = "Error: Syntax Error"
              
            elif payload == bytearray.fromhex("90 60 03 FF"):
              payload_message = "Error: Command buffer full"
              
            elif payload == bytearray.fromhex("90 60 04 FF"):
              payload_message = "Error: Command cancelled (socket no. 0)"
            
            elif payload == bytearray.fromhex("90 61 04 FF"):
              payload_message = "Error: Command cancelled (socket no. 1)"
            
            elif payload == bytearray.fromhex("90 62 04 FF"):
              payload_message = "Error: Command cancelled (socket no. 2)"
            
            elif payload == bytearray.fromhex("90 60 05 FF"):
              payload_message = "Error: No socket (to be cancelled, socket no. 0)"
            
            elif payload == bytearray.fromhex("90 61 05 FF"):
              payload_message = "Error: No socket (to be cancelled, socket no. 1)"
            
            elif payload == bytearray.fromhex("90 62 05 FF"):
              payload_message = "Error: No socket (to be cancelled, socket no. 2)"
            
            elif payload == bytearray.fromhex("90 60 41 FF"):
              payload_message = "Error: Command not executable (socket no. 0)"
            
            elif payload == bytearray.fromhex("90 61 41 FF"):
              payload_message = "Error: Command not executable  (socket no. 1)"
            
            elif payload == bytearray.fromhex("90 62 41 FF"):
              payload_message = "Error: Command not executable  (socket no. 2)"
            
            elif payload == bytearray.fromhex("01"):
              payload_message = "Reset sequence number."
            
            elif payload == bytearray.fromhex("0F 01"):
              payload_message = "Abnormality in the sequence number."
            
            elif payload == bytearray.fromhex("0F 01"):
              payload_message = "Abnormality in the message (message type)."
            
            # if there was a special reply
            if payload_message != "":
              
              # clear received message
              received_message = bytes()
            
            # if there was a normal reply
            else:
              # find end of payload
              position_ff = received_message.find(bytearray.fromhex("FF"))
              
              # if the end was not yet contained
              if position_ff == -1:
                message_is_complete = False
              
              # if the end was found
              else:
                
                # extract payload
                payload = received_message[8:position_ff+1]
                if len(payload) >= 2 and payload[0:2] == bytearray.fromhex("90 50"):
                  payload_message = "Completion (inquiries)"
                
                # remove payload, rest of received message is handled in next iteration
                received_message = received_message[position_ff+1:]
            
            # output message
            print("[{:%M:%S}] < recv {}, seq. no. {}, payload (length {}): {} ({})".format(
              datetime.datetime.now(), payload_type_str, sequence_no, payload_length, payload.hex(), payload_message))
              
            # store message
            if sequence_no not in self.open_commands:
              self.open_commands[sequence_no] = {}
            
            # add items
            self.open_commands[sequence_no]["payload"] = payload
            self.open_commands[sequence_no]["payload_type"] = payload_type
            self.open_commands[sequence_no]["payload_message"] = payload_message
            self.open_commands[sequence_no]["result"] = None
            
            # process the return value, if a function was specified
            if "process_return_value" in self.open_commands[sequence_no]:
              try:
                result = self.open_commands[sequence_no]["process_return_value"](payload)
                self.open_commands[sequence_no]["result"] = result
                print("  Processed result is {}".format(result))
              except:
                if payload:
                  print("  Could not process return value {} for command {}.".format(payload.hex(), self.open_commands[sequence_no]["command_name"]))
                  #traceback.print_exc()
                else:
                  print("  Could not process return value.")
                  #traceback.print_exc()
            else:
              # set result to True if there is no process_return_value command and the command has terminated
              self.open_commands[sequence_no]["result"] = True
            
      # if nothing is received, continue
      except BlockingIOError:
        continue
        
      # if there was a different error, print stacktrace
      except:
        print(sys.exc_info()[0])
        traceback.print_exc()
      
      # wait short time and then continue receiving
      time.sleep(0.01)
      
  def reset_sequence_no(self):
    message = bytearray.fromhex('02 00 00 01 00 00 00 01 01')
    self.socket.sendto(message,(self.ip_address, self.port))
    self.sequence_no = 1
    self.open_commands = {}
  
  def send_message(self, message_type, message_payload):
    
    # compose payload type
    message_payload_type = bytes()
    if message_type == MessageType.VISCA_COMMAND:
      message_payload_type = bytearray.fromhex('01 00')
      
    elif message_type == MessageType.VISCA_INQUIRY:
      message_payload_type = bytearray.fromhex('01 10')
    
    elif message_type == MessageType.VISCA_DEVICE_SETTING_COMMAND:
      message_payload_type = bytearray.fromhex('01 20')
    
    elif message_type == MessageType.CONTROL_COMMAND:
      message_payload_type = bytearray.fromhex('02 00')
    
    else:
      message_payload_type = bytearray.fromhex('00 00')
    
    # compose payload and length
    message_payload_length = len(message_payload).to_bytes(2, 'big')
    message_sequence_no = self.sequence_no.to_bytes(4, 'big')
    
    # compose message
    message = message_payload_type + message_payload_length + message_sequence_no + message_payload
    
    #print("> send [{}], seq. no. {}".format(message.hex(), self.sequence_no))
    
    # send message with UDP
    self.socket.sendto(message, (self.ip_address, self.port))
    
    # increment sequence number
    self.sequence_no += 1
    
    return self.sequence_no - 1
  
  def send_command(self, command_name, *args):
    
    # check if command exists in the dict of commands
    if command_name not in commands.commands:
      print("> send_command([]): error, no such command name".format(command_name))
      return None
    
    # get the message type (either MessageType.INQUIRY or MessageType.COMMAND)
    message_type_value = commands.commands[command_name]["message_type"]
    
    # get the binary packet to send for this command
    command_packet = commands.commands[command_name]["command_packet"](args)

    self.open_commands[self.sequence_no] = {
      "command_packet": command_packet,
      "command_name": command_name,
      "command_type": message_type_value,
      "result": None,
    }
    
    # if there is a function to process the return value, add it to the open_commands queue
    if "process_return_value" in commands.commands[command_name]:
      if commands.commands[command_name]["process_return_value"]:
        self.open_commands[self.sequence_no]["process_return_value"] = commands.commands[command_name]["process_return_value"]
        
    # debugging output
    print("[{:%M:%S}] > send command \"{}\", seq. no. {}".format(
      datetime.datetime.now(), command_name, self.sequence_no))
    
    # send actual message
    return self.send_message(message_type_value, command_packet)
    
  def get_result(self, sequence_no):
    return self.open_commands[sequence_no]["result"]
    
  def wait_for_result(self, sequence_no):
    while self.open_commands[sequence_no]["result"] is None:
      time.sleep(0.001)
    return self.open_commands[sequence_no]["result"]
    
if __name__ == "__main__":

  camera = Camera(globals.ptz_camera_ip_address)
  
  sequence_no = camera.send_command("CAM_Zoom_Stop")
  time.sleep(1)
  
  sequence_no = camera.send_command("CAM_PowerInq")
  camera_is_on = camera.wait_for_result(sequence_no)
  print("camera is on: {}".format(camera.get_result(sequence_no)))
  
  # if camera is turned off, turn on now
  if not camera_is_on:
    sequence_no = camera.send_command("CAM_PowerOn", True)
  
  # Pan-tiltDrive_Home
  sequence_no = camera.send_command("Pan-tiltDrive_Home")
  camera.wait_for_result(sequence_no)
  time.sleep(2)
  """
  sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", 0.1, 7)
  for i in range(100):
    sequence_no = camera.send_command("CAM_OpticalZoomPosInq")
    
    result = None
    while not result:
      result = camera.get_result(sequence_no) 
      if result:
        print("zoom: {}".format(result))
      time.sleep(0.02)
  
  print("done")
  sys.exit(0)
  """
  
  # Pan-tiltDrive_absolute(x,y,vx,vy)
  sequence_no = camera.send_command("Pan-tiltDrive_absolute", -0.7, -0.1, 0.8, 0.8)
  
  for i in range(100):
    sequence_no = camera.send_command("Pan-tiltPosInq")
    
    result = None
    while not result:
      result = camera.get_result(sequence_no) 
      if result:
        print("Pan-tiltPos: {}".format(result))
      time.sleep(0.2)
  
  print("done")
  sys.exit(0)
  
  time.sleep(2)
  
  sequence_no = camera.send_command("CAM_Zoom_Stop")
  time.sleep(1)
  
  # turn camera off
  sequence_no = camera.send_command("CAM_PowerOn", False)
  
  # Pan-tiltDrive_Reset
  #sequence_no = camera.send_command("Pan-tiltDrive_Reset")
  #time.sleep(2)
  # Pan-tiltDrive_relative(x,y,vx,vy)
  #sequence_no = camera.send_command("Pan-tiltDrive_relative", -0.2, -0.5, 1, 1.0)
  #time.sleep(2)
  
    
  
  """
  # Pan-tiltDrive(x,y,vx,vy)
  sequence_no = camera.send_command("Pan-tiltDrive", -1, 1, 0.1, 1.0)
  time.sleep(2)
  sequence_no = camera.send_command("Pan-tiltDrive", 1, -1, 0.1, 1.0)
  time.sleep(2)
  sequence_no = camera.send_command("Pan-tiltDrive_Stop")
  """
  
  """
  sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", 0.5, 7)
  time.sleep(7)
  sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", 0.6, 5)
  time.sleep(7)
  sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", 0.4, 3)
  time.sleep(7)
  sequence_no = camera.send_command("CAM_Zoom_Direct_Speed", 0.2, 0)
  time.sleep(7)
  sequence_no = camera.send_command("CAM_Zoom_Stop")
  time.sleep(1)
  """
