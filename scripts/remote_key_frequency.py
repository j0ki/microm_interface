#!/usr/bin/env python3

import MicroM92CI_driver as m92
import sys
import time

if len(sys.argv) > 1:
  device = sys.argv[1]
else:
  device = "/dev/ttyACM0"

ir_board = m92.M92CI_IR(device, timeout=5, verbose=True)
ir_board.display_funny_boot()

print("press and hold any button in 5 seconds...")
time.sleep(1)
print("4")
time.sleep(1)
print("3")
time.sleep(1)
print("2")
time.sleep(1)
print("1")
time.sleep(1)

#~ starttime = time.time()
#~ while time.time() < starttime+0.5:
  #~ ir_board.read
ir_board.reset_input_buffer()

byte_counter = 0
starttime = time.time()
while time.time() < starttime+30:
  data = ir_board.readdata(2)
  byte_counter += len(data)

ir_keypress_counter = byte_counter // 2
print(byte_counter, "bytes read,", ir_keypress_counter, "repetitions in 30 seconds.")
print("that is a \"code_length\" of", 30000 // ir_keypress_counter, "milliseconds")


