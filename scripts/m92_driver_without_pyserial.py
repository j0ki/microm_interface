#!/usr/bin/env python3
import os
import time

verbose = True

magic = b'\xab\xbc\xcd\xde\xea'

key01 = 0x01
init01 = b'\x06\x05\x04\xc0\x10\x00'

key03 = 0x03
init03 = b'\x0f\x06\x06@\x90\xd0'

key = key03
ini = init03


masterkey = b'\x0e\x0b'
keyex = b'\x8e\x08'

def _blob_to_hex(bytestring):
  return " ".join("{:02x}".format(c) for c in bytestring)

def crypt_list_8bit(key, data):
  return bytes([d ^ key for d in data])

def senddata(fd, packet, key):
  if verbose:
    print("--> " + _blob_to_hex(packet))
  packet = crypt_list_8bit(key, packet)
  os.write(fd, packet)

dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

dashl = b'\x8eA\xd0\xd1\xd2\xd3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

s = 1
def initi(a):
if a: key = key01; ini = init01;
else: key = key03; ini = init03;
if a: cmd = dash;  print("dash")
else: cmd = dashl; print("quaaaaaaaaaaaaaaaaaaaaaaaaaaaaaark")
fd = os.open("/dev/ttyACM1", os.O_RDWR | os.O_NOCTTY)
time.sleep(s)
#~ os.write(fd, magic)
#~ os.write(fd, init)
senddata(fd, magic, 0x00)
senddata(fd, ini, 0x00)
time.sleep(s)
r = os.read(fd, 6)
print(r)
#~ ckey = crypt_list_8bit(key, masterkey)
#~ ckeyex = crypt_list_8bit(key, keyex)
#~ os.write(fd, ckey); os.write(fd, ckeyex)
senddata(fd, masterkey, key)
#CRITICAL TIMING!!! wait at least 2milliseconds before sending the following bytes
senddata(fd, keyex, key)
time.sleep(s)
r = os.read(fd, 3)
print(r)
senddata(fd, cmd, key)
time.sleep(s)
os.close(fd)



def run():
  a = True
  while True:
    initi(a)
    a = not a
    time.sleep(0.5)


quit()
