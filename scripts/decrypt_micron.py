#!/usr/bin/env python3

import sys

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
