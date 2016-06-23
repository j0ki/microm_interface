# Generic Makefile for compiling LIRC plugins out of tree.
# Copyright: public domain

# Following two or three lines should be adjusted

# Where are the LIRC sources located (needed for include files only)
LIRC_SRC=/home/joki/Projects/reverse_dvbc_interface_board/lirc/src/lirc-0.9.4
# Where are out plugins to be installed
PLUGINDIR := /home/joki/Projects/reverse_dvbc_interface_board/lirc/src/lirc-0.9.4/plugins/.libs

# Some extra includes and/or libraries might be needed
#EXTRA_INCLUDES := -I/usr/include/libxml2
#EXTRA_LIBS := -lxml2 -lDecodeIR -Wl,-rpath=/local/lib64

MACHINE := -m64
INCLUDE := -I$(LIRC_SRC)/lib -I$(LIRC_SRC) $(EXTRA_INCLUDES)
OPTIMIZE := -O2
DEBUG := -g
SHARED :=-shared -fPIC
WARNINGS=-Wall
CC := gcc
CPP := g++

# Rule for compiling C
%.so: %.c microm92ci_functions.c
	$(CC)  $(WARNINGS) $(INCLUDE) $(MACHINE) $(OPTIMIZE) $(DEBUG) $(SHARED) -o $@ $< $(EXTRA_LIBS)

# Rule for compiling C++
%.so: %.cpp
	$(CPP) $(WARNINGS) $(INCLUDE) $(MACHINE) $(OPTIMIZE) $(DEBUG) $(SHARED) -o $@ $< $(EXTRA_LIBS)

m92driver: m92driver.c microm92ci_functions.c
	$(CC) $(WARNINGS) $(INCLUDE) $(MACHINE) $(OPTIMIZE) $(DEBUG)  -o $@ $< $(EXTRA_LIBS)

main: m92driver

default:
	@echo "There is no default target in this makefile."
	@echo "Type \"make plugin.so\" to compile the plugin named plugin,"
	@echo "and \"make install\" to install it"

install:
	cp *.so $(PLUGINDIR)

clean:
	rm -f *.so

