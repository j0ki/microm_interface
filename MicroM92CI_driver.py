#!/usr/bin/env python3

import serial
import sys
import time
import json


_MASTERKEY = bytes((0x0e, 0x0b))

_CMD_PREFIX = bytes([0x8e])
_CMD_DISPLAY_PREFIX      = _CMD_PREFIX + bytes([0x41])
_CMD_STANDBY_PREFIX      = _CMD_PREFIX + bytes([0x67])
_CMD_CONFIRM_KEYEXCHANGE = _CMD_PREFIX + bytes([0x08])


def _blob_to_hex(bytestring):
  return " ".join("{:02x}".format(c) for c in bytestring)

def _hex_list_from_int(number):
  h, l  = divmod(number, 16)
  hex_list = [l]
  if 0 != h:
    hex_list = _hex_list_from_int(h) + hex_list
  return hex_list

def _hexdigit(i):
  if i < 10:
    return 16*i + 3 # {0x03..0x93}
  if i < 16:
    return 16*(i-9) + 2 #{0x12..0x62}
  return 0

def _hex_to_display(number):
  displaystring = bytes([ _hexdigit(i) for i in _hex_list_from_int(number) ])
  return _cmd_display_raw(displaystring)

#~ def _hex_to_blob(asciistring):
  #~ return bytes([int(x,16) for x in asciistring.split(" ")])

def _swapnibbles(x):
  return x<<4 & 0xf0 | x>>4 & 0x0f

def _ascii_to_display(string):
  displaystring = b''
  for c in string:
    if c.isdigit():
      displaystring += bytes([_swapnibbles(ord(c))])
    else:
      displaystring += ord(c)
  return displaystring

def _cmd_display(string):
  cmd = _CMD_DISPLAY_PREFIX
  if len(string) > 16:
    return b''
  cmd += _ascii_to_display(string)
  cmd = cmd.ljust(18, b'\0')
  return cmd

def _cmd_display_raw(bytestring):
  cmd = _CMD_DISPLAY_PREFIX
  if len(bytestring) > 16:
    return b''
  cmd += bytestring
  cmd = cmd.ljust(18, b'\0')
  return cmd

def _format_standby_time(t):
  h1, h2 = divmod(t.tm_hour, 10)
  m1, m2 = divmod(t.tm_min, 10)
  s1, s2 = divmod(t.tm_sec, 10)
  cmd = ''.join(map(str,[h1,h2,m1,m2,s1,s2]))
  #~ print(cmd)
  return _ascii_to_display(cmd).ljust(9, b'\0')

def _cmd_standby(t):
  return _CMD_STANDBY_PREFIX.ljust(9, b'\0') + _format_standby_time(t)

class M92CI_IR:
  def crypt_multi(self, data):
    return bytes(a^b for a,b in zip(data,self.__key))

  def crypt_list_8bit(self, data):
    return bytes([d ^ self.__key for d in data])

  def readdata_clear(self, n):
    data = self.__ser.read(n)
    if data:
      if self.verbose:
        print("<== " + _blob_to_hex(data))
    return data

  def readdata(self, n):
    data = self.__ser.read(n)
    if data:
      data = self.crypt_list_8bit(data)
      if self.verbose:
        print("<== " + _blob_to_hex(data))
    return data

  def senddata_clear(self, packet):
    if self.verbose:
      print("--> " + _blob_to_hex(packet))
    self.__ser.write(packet)

  def senddata(self, packet):
    if self.verbose:
      print("--> " + _blob_to_hex(packet))
    packet = self.crypt_list_8bit(packet)
    self.__ser.write(packet)

  def __init__(self, port, timeout=2, verbose=False):
    self.__ser = serial.Serial(port=port, baudrate=115200, timeout=timeout)

    self.verbose = verbose

    magic = b'\xab\xbc\xcd\xde\xea'

    init_01 = b'\x06\x05\x04\xc0\x10\x00'
    key_01 = 0x01

    # initialize key_exchange
    init_03 = b'\x0f\x06\x06@\x90\xd0'
    key_03 = 0x03

    # initialize key_exchange
    # plaintext magic + encrypted garbage(?)
    init_2a = b'\x03\'\x05p\xb0\xc0'

    #~ key_2a = b'**'
    #~ key_2a = bytes((0x2a, 0x2a))
    key_2a = 0x2a


    init = init_03
    self.__key = key_03

    self.senddata_clear(magic)
    self.senddata_clear(init)
    data = self.readdata_clear(6)
    if len(data) < 6:
      raise ConnectionError("bad response:("+str(len(data))+") "+ str(data))
    self.senddata(_MASTERKEY)

    self.senddata(_CMD_CONFIRM_KEYEXCHANGE)
    self.readdata(3)
    if len(data) < 3:
      raise ConnectionError("bad response:("+str(len(data))+") "+ str(data))

  def standby(self, standby_time=None):
    if standby_time:
      cmd = _cmd_standby(standby_time)
    else:
      cmd = _cmd_standby(time.localtime())
    self.senddata(cmd)

  def generate_keymap(self, keymap=dict()):
    while True:
      data = self.readdata(2)
      if len(data) < 2:
        continue
      if data == _CMD_STANDBY_PREFIX:
        break
      keycode = data[1]
      prompt = str(keycode)
      if keycode in keymap:
        prompt += " \'"+keymap[keycode]+"\'"
      remote_control_key = input(prompt+": ")
      if remote_control_key:
        keymap[keycode] = remote_control_key
      self.senddata(_hex_to_display(data[0]<<8 | data[1]))
    return keymap

  def display_all_decimals(self):
    for i in range(0, 10000):
      i = str(i).rjust(4, "0")
      self.senddata(_cmd_display(i))

  def display_raw_bytes(self):
    for i in range(0, 0x100):
      i = _swapnibbles(i)
      #~ cmd = _cmd_display_raw(bytes((i,(i+0x10)&0xff,(i+0x20)&0xff,(i+0x30)&0xff)))
      time.sleep(0.5)

      cmd = _hex_to_display(i)
      time.sleep(.5)
      self.senddata(cmd)

  def display_funny_boot(self):
    cmd_display_boot = b'\x8e\xc1"\xf4\xf4G\x94\xe4t\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    cmd_display_boot = b'\x8eA"\xf4\xf4G\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    cmd_display_dash_dash_dash_dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
    cmd_display_dash_dash_dash_dash = b'\x8eA\xd3\xd3\xd3\xd3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    self.senddata(cmd_display_dash_dash_dash_dash)
    time.sleep(.5)
    self.senddata(cmd_display_boot)
    time.sleep(.5)
    self.senddata(cmd_display_dash_dash_dash_dash)

