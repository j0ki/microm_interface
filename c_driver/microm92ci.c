/****************************************************************************
** microm92ci.c **************************************************************
****************************************************************************
*
* lirc plugin for Micro M92 CI hacked interface board
*
* Copyright (C) 1999 Christoph Bartelmus <lirc@bartelmus.de>
*       modified for logitech receiver by Isaac Lauer <inl101@alumni.psu.edu>
*      modified for UIRT2 receiver by
*      Mikael Magnusson <mikma@users.sourceforge.net>
*      modified for microm92ci interface board by
*      Lukas Fischer <joki0z@web.de>
*
*  This program is free software; you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation; either version 2 of the License, or
*  (at your option) any later version.
*
*  This program is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU Library General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with this program; if not, write to the Free Software
*  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.
*
*/

#ifdef HAVE_CONFIG_H
# include <config.h>
#endif

#ifndef LIRC_IRTTY
#define LIRC_IRTTY "/dev/ttyS0"
#endif

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <limits.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <termios.h>
#include "lirc_driver.h"
#include "lirc/serial.h"

#define NUMBYTES 2

static const unsigned char MAGIC[] = {0xab, 0xbc, 0xcd, 0xde, 0xea};
static const unsigned char MASTERKEY[] = {0x0e, 0x0b};
static const unsigned char INIT[] = {0x06, 0x05, 0x04, 0xc0, 0x10, 0x00};
static const unsigned char KEY = 0x01;

#define CMD_PREFIX 0x8e
static const unsigned char CMD_DISPLAY_PREFIX[] = {CMD_PREFIX, 0x41};
static const unsigned char CMD_STANDBY_PREFIX[] = {CMD_PREFIX, 0x67};
static const unsigned char CMD_CONFIRM_KEYEXCHANGE[] = {CMD_PREFIX, 0x08};
static const unsigned char DISPLAY_INIT[] = "\x13\xe4\x13\x45";

static const logchannel_t logchannel = LOG_DRIVER;

static unsigned char b[NUMBYTES];
static struct timeval start, end, last;
static ir_code code;

static int microm92ci_decode(struct ir_remote* remote, struct decode_ctx_t* ctx);
static int microm92ci_init(void);
static int microm92ci_deinit(void);
static char* microm92ci_rec(struct ir_remote* remotes);

const struct driver hw_microm92ci = {
	.name		= "microm92ci",
	.device		= LIRC_IRTTY,
	.features	= LIRC_CAN_REC_LIRCCODE,
	.send_mode	= 0,
	.rec_mode	= LIRC_MODE_LIRCCODE,
	.code_length	= 8 * NUMBYTES,
	.init_func	= microm92ci_init,
	.deinit_func	= microm92ci_deinit,
	.open_func	= default_open,
	.close_func	= default_close,
	.send_func	= NULL,
	.rec_func	= microm92ci_rec,
	.decode_func	= microm92ci_decode,
	.drvctl_func	= NULL,
	.readdata	= NULL,
	.api_version	= 3,
	.driver_version = "0.9.3",
	.info		= "No info available",
	.device_hint    = "/dev/tty[0-9]*",
};

const struct driver* hardwares[] = { &hw_microm92ci, (const struct driver*)NULL };

#include "microm92ci_functions.c"
