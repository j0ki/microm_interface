/****************************************************************************
** microm92ci.c **************************************************************
****************************************************************************
*
* routines for Micro M92 CI hacked interface board
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
#define TIMEOUT 20000

static const unsigned char MAGIC[] = {0xab, 0xbc, 0xcd, 0xde, 0xea};
static const unsigned char MASTERKEY[] = {0x0e, 0x0b};
static const unsigned char INIT[] = {0x0f, 0x06, 0x06, 0x40, 0x90, 0xd0};
static const unsigned char KEY = 0x03;

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


static unsigned char crypt_byte(unsigned char byte)
{
	return byte ^ KEY;
}

static void crypt_bytes(unsigned char *src, unsigned char *dest, int len)
{
	for (int i = 0; i < len; i++) {
		dest[i] = crypt_byte(src[i]);
	}
}

static int microm92ci_decode(struct ir_remote* remote, struct decode_ctx_t* ctx)
{
	log_debug("m92 decode");
	//ctx->repeat_flag = (code == 0x8efe) ? 1 : 0;
	if (!map_code(remote, ctx, 0, 0, 8 * NUMBYTES, code, 0, 0))
		return 0;

	//map_gap(remote, ctx, &start, &last, 0);

	return 1;
}

static int readdata(unsigned char *dest, int nbytes)
{
	log_debug("m92 readdata");
	struct timeval timeout;
	timeout.tv_sec = 10;
	timeout.tv_usec = 0;
	fd_set readfs;
	FD_SET(drv.fd, &readfs);
	int maxfd = drv.fd + 1;
	select(maxfd, &readfs, NULL, NULL, &timeout);
	int i = read(drv.fd, dest, nbytes);
	if (i != nbytes) {
		if (i > 0) {
			log_error("microm92ci: readdata error: expected %d bytes, but read 1 byte", nbytes);
		}
	}
	return i;
}

static int microm92ci_init(void)
{
	unsigned char buffer[18] = {0};
	struct termios options;
	log_debug("m92 init");
	//~ if (!tty_create_lock(drv.device)) {
		//~ log_error("microm92ci: could not create lock files");
		//~ return 0;
	//~ }
	log_debug("init: open device..");
	drv.fd = open(drv.device, O_RDWR | O_NOCTTY | O_NONBLOCK);
	if (drv.fd < 0) {
		log_error("microm92ci: could not open %s", drv.device);
		//~ tty_delete_lock();
		return 0;
	}
	//~ if (!tty_reset(drv.fd)) {
		//~ log_error("microm92ci: could not reset tty");
		//~ microm92ci_deinit();
		//~ return 0;
	//~ }
	
	//~ if (!tty_setbaud(drv.fd, 115200)) {
		//~ log_error("microm92ci: could not set baud rate");
		//~ microm92ci_deinit();
		//~ return 0;
	//~ }
	if (tcgetattr(drv.fd, &options) == -1) {
		log_error("m92: tcgetattr() failed");
		return 0;
	}
	cfmakeraw(&options);
	(void)cfsetispeed(&options, B115200);
	(void)cfsetospeed(&options, B115200);
	options.c_cflag |= (CLOCAL | CREAD);
	options.c_cc[VTIME] = 0;
	options.c_cc[VMIN]  = 0;
	if (tcsetattr(drv.fd, TCSAFLUSH, &options) == -1) {
		log_trace("m92: tcsetattr() failed");
		return 0;
	}
	tcflush(drv.fd, TCIFLUSH);

	log_debug("init: sending magic..");
	if (!write(drv.fd, MAGIC, sizeof MAGIC)) {
		log_error("microm92ci: failed to send magic to m92");
		microm92ci_deinit();
		return 0;
	}
	log_debug("init: sending crypto init..");
	if (!write(drv.fd, INIT, sizeof INIT)) {
		log_error("microm92ci: failed to send init to m92");
		microm92ci_deinit();
		return 0;
	}
	log_debug("init: reading crypto init response..");
	int n = readdata(buffer, 6);
	if (n != 6) {
		log_error("microm92ci: failed to get 6 byte response from m92. got %d bytes: %02x %02x %02x %02x %02x %02x", n,
				buffer[0], buffer[1], buffer[2], buffer[3], buffer[4], buffer[5]);
		microm92ci_deinit();
		return 0;
	}
	crypt_bytes(MASTERKEY, buffer, sizeof MASTERKEY);
	//~ log_debug("init: sending key..");
	if (!write(drv.fd, buffer, sizeof MASTERKEY)) {
		log_error("microm92ci: failed to send masterkey to m92");
		microm92ci_deinit();
		return 0;
	}
	crypt_bytes(CMD_CONFIRM_KEYEXCHANGE, buffer, sizeof CMD_CONFIRM_KEYEXCHANGE);
	//~ log_debug("init: sending key exchange command..");
	if (!write(drv.fd, buffer, sizeof CMD_CONFIRM_KEYEXCHANGE)) {
		log_error("microm92ci: failed to send key exchange to m92");
		microm92ci_deinit();
		return 0;
	}
	log_debug("init: reading key exchange ack..");
	n = readdata(buffer, 3);
	if (n != 3) {
		log_error("microm92ci: failed to get 3 byte response from m92. got %d bytes: %02x %02x %02x", n,
				buffer[0], buffer[1], buffer[2]);
		microm92ci_deinit();
		return 0;
	}
	if (buffer[0] != crypt_byte(0x8e) || buffer[1] != crypt_byte(0x9c) || buffer[2] != crypt_byte(0x29)) {
		log_error("microm92ci: bad response from m92");
		return 0;
	}

	memset(buffer, crypt_byte(0), sizeof(buffer));
	crypt_bytes(CMD_DISPLAY_PREFIX, buffer, sizeof(CMD_DISPLAY_PREFIX));
	crypt_bytes(DISPLAY_INIT, &buffer[2], sizeof(DISPLAY_INIT));
	log_debug("init: sending display message..");
	if (!write(drv.fd, buffer, sizeof(buffer))) {
		log_error("failed to display init on m92");
		microm92ci_deinit();
		return 0;
	}

	// set timeouts for receive mode:
	if (tcgetattr(drv.fd, &options) == -1) {
		log_error("m92: tcgetattr() failed");
		return 0;
	}
	options.c_cc[VTIME] = 0;
	options.c_cc[VMIN]  = 0;
	if (tcsetattr(drv.fd, TCSAFLUSH, &options) == -1) {
		log_trace("m92: tcsetattr() failed");
		return 0;
	}
	
	log_debug("microm92ci: successfully initialized m92");
	return 1;
}

static int microm92ci_deinit(void)
{
	log_debug("m92 deinit");
	//TODO: put board into standby? no! it should go into standby just before the cpu halts
	close(drv.fd);
	//~ tty_delete_lock();
	return 1;
}

static char* microm92ci_rec(struct ir_remote* remotes)
{
	log_debug("m92 rec");
	int i = read(drv.fd, b, NUMBYTES);
	if (i != NUMBYTES) {
		if (i > 0) {
			log_error("microm92ci: receive error: expected 2 bytes, but read 1 byte");
		}
		return NULL;
	}
	char* m;

	//~ last = end;
	//~ gettimeofday(&start, NULL);
	//~ for (i = 0; i < NUMBYTES; i++) {
		//~ if (i > 0) {
			//~ if (!waitfordata(TIMEOUT)) {
				//~ log_error("microm92ci: timeout reading byte %d", i);
				//~ return NULL;
			//~ }
		//~ }
		//~ if (read(drv.fd, &b[i], 1) != 1) {
			//~ log_error("microm92ci: reading of byte %d failed", i);
			//~ log_perror_err(NULL);
			//~ return NULL;
		//~ }
		//~ log_trace("byte %d: %02x", i, b[i]);
	//~ }
	//~ gettimeofday(&end, NULL);

	/* mark as Irman */
	//~ code = 0xffff;
	//~ code <<= 16;

	code = ((ir_code)crypt_byte(b[0]));
	code = code << 8;
	code |= ((ir_code)crypt_byte(b[1]));
	//~ code = code << 8;
	//~ code |= ((ir_code)b[2]);
	//~ code = code << 8;
	//~ code |= ((ir_code)b[3]);
	//~ code = code << 8;
	//~ code |= ((ir_code)b[4]);
	//~ code = code << 8;
	//~ code |= ((ir_code)b[5]);
	log_debug("code: %llx", code);

	log_trace("code: %llx", (__u64)code);

	m = decode_all(remotes);
	return m;
}
