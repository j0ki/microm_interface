#!/usr/bin/env python3

import MicroM92CI_driver as m92
import sys

ir_board = m92.M92CI_IR(sys.argv[1], timeout=5, verbose=True)
ir_board.standby()



