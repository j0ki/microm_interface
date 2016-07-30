# Generic Makefile for compiling LIRC plugins out of tree.
# Copyright: public domain

# Following two or three lines should be adjusted

# Where are the LIRC sources located (needed for include files only)
# Not needed, when the lirc package is installed
#LIRC_SRC=/usr/include

# The plugin installation directory
# This is defined in /etc/lirc/lirc_options.conf
PLUGINDIR := /usr/local/lib/lirc/plugins

# Some people still use 32-bit (Raspberry Pi)
#MACHINE := -m64

INCLUDE := -I$(LIRC_SRC)/lib -I$(LIRC_SRC)
OPTIMIZE := -O2
DEBUG := -g
SHARED :=-shared -fPIC
WARNINGS=-Wall
CC := gcc

# Rule for compiling C
microm92ci.so: microm92ci.c microm92ci.h
	$(CC)  $(WARNINGS) $(INCLUDE) $(MACHINE) $(OPTIMIZE) $(DEBUG) $(SHARED) -o $@ $< $(EXTRA_LIBS)

m92driver: m92driver.c microm92ci.c
	$(CC) $(WARNINGS) $(INCLUDE) $(MACHINE) $(OPTIMIZE) $(DEBUG)  -o $@ $< $(EXTRA_LIBS)

main: m92driver

default: microm92ci.so

install:
	cp *.so $(PLUGINDIR)

clean:
	rm -f *.so

