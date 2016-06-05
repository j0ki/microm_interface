#!/usr/bin/env python3

import serial
import sys
import time


verbose = False

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


ser = serial.Serial(port=sys.argv[1], baudrate=115200)
ser.timeout = 10



#~ init = "ab bc cd de ea 06 05 04 c0 10 00"
#~ print(bytes([int(x, 16) for x in init.split(" ")]))

#~ quit()

init_0101 = b'\xab\xbc\xcd\xde\xea\x06\x05\x04\xc0\x10\x00'






MASTERKEY = bytes((0x0e, 0x0b))


cmd_confirm_key = b'\x8e\x08'


#~ print(crypt_multi(c_key, p_key))

# command: assert key is valid (or something like that)
# encrypted by key ( 0x2a )
c_cmd_confirm_key = b'\xa4"'
# display: 'boot'
# encrypted by key ( 0x2a )
packet1_1 = b'\xa4\xeb\x08\xde\xdem\xbe\xce^*********'



#~ print(decrypt(p_key, 0x2a))
#~ print(decrypt(p_cmd_confirm_key, 0x2a))

#~ quit()


cmd_display_boot = b'\x8e\xc1"\xf4\xf4G\x94\xe4t\x00\x00\x00\x00\x00\x00\x00\x00\x00'
cmd_display_boot = b'\x8eA"\xf4\xf4G\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

cmd_display_dash_dash_dash_dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
cmd_display_dash_dash_dash_dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

cmd_display_0_0_2_0 = b'\x8eA\x03\x03#\x03\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
cmd_display_0_0_2_0 = b'\x8eA\x03\x03#\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

def swapnibbles(x):
  return bytes([x<<4 & 0xf0 | x>>4 & 0x0f])

def ascii_to_cmd_string(string):
  cmd = b''
  for c in string:
    if c.isdigit():
      cmd += swapnibbles(ord(c))
    else:
      cmd += ord(c)
  return cmd

def command(string):
  cmd = b'\x8eA'
  if len(string) > 16:
    return b''
  cmd += ascii_to_cmd_string(string)
  cmd = cmd.ljust(18, b'\0')
  return cmd

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


init = init_01
key = key_01


senddata(ser, init)
readdata(ser, 6)

c_key = crypt_list_8bit(MASTERKEY, key)
senddata(ser, c_key)

c_cmd_confirm_key = crypt_list_8bit(cmd_confirm_key, key)
senddata(ser, c_cmd_confirm_key)
readdata(ser, 3)

senddata(ser, crypt_list_8bit(cmd_display_dash_dash_dash_dash, key))
time.sleep(.5)
senddata(ser, crypt_list_8bit(cmd_display_0_0_2_0, key))
time.sleep(.5)
senddata(ser, crypt_list_8bit(cmd_display_boot, key))
time.sleep(.5)

for i in range(0, 10000):
  i = str(i).rjust(4, "0")
  #~ print(command(i))
  senddata(ser, crypt_list_8bit(command(i), key))
  c_data = readdata(ser, 2)
  print("<== " + blob_to_hex(crypt_list_8bit(c_data, key)))



quit()
#~ time.sleep(.1)




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
