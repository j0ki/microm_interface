#!/usr/bin/env python3

import MicroM92CI_driver as m92
import sys

if len(sys.argv) > 1:
  device = sys.argv[1]
else:
  device = "/dev/ttyACM0"

ir_board = m92.M92CI_IR(device, timeout=5, verbose=True)
ir_board.display_funny_boot()



