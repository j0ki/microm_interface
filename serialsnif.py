#!/usr/bin/env python3

import serial
import sys
import time
import json

verbose = False



MASTERKEY = bytes((0x0e, 0x0b))

CMD_PREFIX = bytes([0x8e])
CMD_DISPLAY_PREFIX      = CMD_PREFIX + bytes([0x41])
CMD_STANDBY_PREFIX      = CMD_PREFIX + bytes([0x67])
CMD_CONFIRM_KEYEXCHANGE = CMD_PREFIX + bytes([0x08])

def crypt_multi(data, key):
  return bytes(a^b for a,b in zip(data,key))

def crypt_list_8bit(data, key):
  return bytes([d ^ key for d in data])

def blob_to_hex(bytestring):
  return " ".join("{:02x}".format(c) for c in bytestring)

def hex_to_blob(asciistring):
  return bytes([int(x,16) for x in asciistring.split(" ")])

def readdata(ser, n):
  data = ser.read(n)
  if data:
    if verbose:
      print("<== " + blob_to_hex(data))
  return data

def senddata(ser, packet):
  if verbose:
    print("--> " + blob_to_hex(packet))
  ser.write(packet)

cmd_display_boot = b'\x8e\xc1"\xf4\xf4G\x94\xe4t\x00\x00\x00\x00\x00\x00\x00\x00\x00'
cmd_display_boot = b'\x8eA"\xf4\xf4G\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

cmd_display_dash_dash_dash_dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
cmd_display_dash_dash_dash_dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

def swapnibbles(x):
  return x<<4 & 0xf0 | x>>4 & 0x0f

def ascii_to_display(string):
  displaystring = b''
  for c in string:
    if c.isdigit():
      displaystring += bytes([swapnibbles(ord(c))])
    else:
      displaystring += ord(c)
  return displaystring

def hex_list_from_int(number):
  h, l  = divmod(number, 16)
  hex_list = [l]
  if 0 != h:
    hex_list = hex_list_from_int(h) + hex_list
  return hex_list

def hexdigit(i):
  if i < 10:
    return 16*i + 3 # {0x03..0x93}
  if i < 16:
    return 16*(i-9) + 2 #{0x12..0x62}
  return 0

def hex_to_display(number):
  displaystring = bytes([ hexdigit(i) for i in hex_list_from_int(number) ])
  return cmd_display_raw(displaystring)

def cmd_display(string):
  cmd = CMD_DISPLAY_PREFIX
  if len(string) > 16:
    return b''
  cmd += ascii_to_display(string)
  cmd = cmd.ljust(18, b'\0')
  return cmd

def cmd_display_raw(bytestring):
  cmd = CMD_DISPLAY_PREFIX
  if len(bytestring) > 16:
    return b''
  cmd += bytestring
  cmd = cmd.ljust(18, b'\0')
  return cmd

def format_standby_time(t):
  h1, h2 = divmod(t.tm_hour, 10)
  m1, m2 = divmod(t.tm_min, 10)
  s1, s2 = divmod(t.tm_sec, 10)
  cmd = ''.join(map(str,[h1,h2,m1,m2,s1,s2]))
  print(cmd)
  return ascii_to_display(cmd).ljust(9, b'\0')

def cmd_standby(t):
  return CMD_STANDBY_PREFIX.ljust(9, b'\0') + format_standby_time(t)

def initialize_interface_board(ser):
  magic = b'\xab\xbc\xcd\xde\xea'

  init_01 = b'\xab\xbc\xcd\xde\xea\x06\x05\x04\xc0\x10\x00'
  key_01 = 0x01

  # initialize key_exchange
  init_03 = b'\xab\xbc\xcd\xde\xea\x0f\x06\x06@\x90\xd0'
  key_03 = 0x03

  # initialize key_exchange
  # plaintext magic + encrypted garbage(?)
  init_2a = b'\xab\xbc\xcd\xde\xea\x03\'\x05p\xb0\xc0'

  #~ key_2a = b'**'
  #~ key_2a = bytes((0x2a, 0x2a))
  key_2a = 0x2a


  init = init_03[5:]
  key = key_03

  senddata(ser, magic)
  senddata(ser, init)
  data = readdata(ser, 6)
  if len(data) < 6:
    print("bad response:(",len(data), ") ", data)
    return (False, 0)
  c_key = crypt_list_8bit(MASTERKEY, key)
  senddata(ser, c_key)

  c_cmd_confirm_key = crypt_list_8bit(CMD_CONFIRM_KEYEXCHANGE, key)
  senddata(ser, c_cmd_confirm_key)
  readdata(ser, 3)
  return (True, key)

def generate_keymap(ser, key):
  keymap = dict()
  while True:
    data = crypt_list_8bit(readdata(ser, 2), key)
    if len(data) < 2:
      continue
    if data == CMD_STANDBY_PREFIX:
      t = time.localtime()
      senddata(ser, crypt_list_8bit(cmd_standby(t), key))
      break
    keycode = data[1]
    remote_control_key = input(str(keycode)+": ")
    keymap[keycode] = remote_control_key
    senddata(ser, crypt_list_8bit(hex_to_display(data[0]<<8 | data[1]), key))
  return keymap

def display_all_decimals(ser, key):
  for i in range(0, 10000):
    i = str(i).rjust(4, "0")
    senddata(ser, crypt_list_8bit(cmd_display(i), key))

def display_raw_bytes(ser):
  for i in range(0, 0x100):
    i = swapnibbles(i)
    #~ cmd = cmd_display_raw(bytes((i,(i+0x10)&0xff,(i+0x20)&0xff,(i+0x30)&0xff)))
    time.sleep(0.5)

    cmd = hex_to_display(i)
    time.sleep(.5)
    senddata(ser, crypt_list_8bit(cmd, key))

def display_funny_boot(ser):
  senddata(ser, crypt_list_8bit(cmd_display_dash_dash_dash_dash, key))
  time.sleep(.5)
  senddata(ser, crypt_list_8bit(cmd_display_0_0_2_0, key))
  time.sleep(.5)
  senddata(ser, crypt_list_8bit(cmd_display_boot, key))
  time.sleep(.5)
  senddata(ser, crypt_list_8bit(cmd_display_dash_dash_dash_dash, key))


ser = serial.Serial(port=sys.argv[1], baudrate=115200)
ser.timeout = 10

success, key = initialize_interface_board(ser)
if not success:
  print("failed to initialize")
  quit()
keymap = generate_keymap(ser, key)

print(keymap)
print("\n\n\n")
print(json.dumps(keymap, sort_keys=True, indent=4, separators=(',', ': ')))



#~ t = time.localtime()
#~ senddata(ser, crypt_list_8bit(cmd_standby(t), key))
quit()

#########################################################################
remove_exchange = len(sys.argv) > 1

def decrypt(data, key):
  return bytes([d ^ key for d in data])

input = sys.stdin.buffer
output = sys.stdout.buffer

MASTERKEY = 0x0b

key = 0x00
data = bytes()
eos = False
while True:
  if eos and not data:
    break
  i = data.find(0xab)
  if i == -1:
    output.write(decrypt(data, key))
    data = input.read(1024)
    eos = len(data) < 1024
    continue
  output.write(decrypt(data[:i], key))
  more_data = input.read(12)
  eos = len(more_data) < 12
  data = data[i:] + more_data
  if len(data) < 12:
    output.write(decrypt(data, key))
    break
  if data[:5] == bytes([0xab, 0xbc, 0xcd, 0xde, 0xea]):
    key = data[12] ^ MASTERKEY
    if remove_exchange:
      data = data[13:]
    else:
      output.write(data[:11])
      data = data[11:]
  else:
    output.write(decrypt(data[:1], key))
    data = data[1:]


#~ key = int(sys.argv[2], 16)

#~ for line in open(sys.argv[1]):
  #~ line = line.split("\n")[0]
  #~ if line:
    #~ if line.startswith("Host   --> "):
      #~ print("Host   --> ")
      #~ line = line[11:]
    #~ if line.startswith("Device --> "):
      #~ print("Device --> ")
      #~ line = line[11:]
    #~ if not line.startswith("==>"):
      #~ print("  " + line)
      #~ bytes = line.split(" ")
      #~ bytes = [int(x,16) for x in bytes]
      #~ bytes = [x ^ key for x in bytes]
      #~ bytes = ["{:02x}".format(x, "x") for x in bytes]
      #~ line = "~>" + " ".join(bytes)
    #~ print(line)
