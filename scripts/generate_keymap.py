#!/usr/bin/env python3

import MicroM92CI_driver as m92
import sys
import pickle

KEYMAP_FILENAME = "keymap.p"

ir_board = m92.M92CI_IR(sys.argv[1], timeout=5, verbose=True)
ir_board.display_funny_boot()

try:
  keymap = pickle.load( open(KEYMAP_FILENAME, "rb") )
except FileNotFoundError:
  print("NOTICE:",KEYMAP_FILENAME,"not found, using empty dict", file=sys.stderr)
  keymap = dict()

keymap = ir_board.generate_keymap(keymap)

#~ ir_board.standby()

print(keymap)

pickle.dump( keymap, open(KEYMAP_FILENAME, "wb") )


