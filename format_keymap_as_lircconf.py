#!/usr/bin/env python3

import MicroM92CI_driver as m92
import sys
import pickle

PRE_CONF = """begin remote
        name            microremotetest
        bits            8
        eps             30
        aeps            100
        pre_data_bits   8
        pre_data        0x8e
        post_data_bits  0
        post_data       0x0
        gap             0
        toggle_bit      0
	driver          microm92ci

        begin codes
"""
POST_CONF = """        end codes
end remote
"""

KEYMAP_FILENAME = "keymap.p"

#~ ir_board = m92.M92CI_IR(sys.argv[1], timeout=5, verbose=True)
#~ ir_board.display_funny_boot()

try:
  keymap = pickle.load( open(KEYMAP_FILENAME, "rb") )
except FileNotFoundError:
  print("NOTICE:",KEYMAP_FILENAME,"not found, using empty dict", file=sys.stderr)
  quit()


#keymap = ir_board.generate_keymap(keymap)

#~ ir_board.standby()

sys.stdout.write(PRE_CONF)
for keycode, button in keymap.items():
  print('         {0: <20}{1:0=#4x}'.format(button, keycode))
sys.stdout.write(POST_CONF)

#~ pickle.dump( keymap, open(KEYMAP_FILENAME, "wb") )


