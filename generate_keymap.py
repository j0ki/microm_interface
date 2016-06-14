#!/usr/bin/env python3

import MicroM92CI_driver as m92
import sys
import pickle

def test_generate_keymap():
  ir_board = m92.M92CI_IR(sys.argv[1], timeout=5, verbose=True)
  ir_board.display_funny_boot()

  keymap = ir_board.generate_keymap()

  ir_board.standby()

  print(keymap)
  print("\n\n\n")
  print(json.dumps(keymap, sort_keys=True, indent=4, separators=(',', ': ')))


test_generate_keymap()


