/****************************************************************************
** m92driver ***************************************************************
****************************************************************************
*
* tests for microm92ci
*
*
*/

#include <termios.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>



#define log_error (printf)
#define log_debug (printf)

struct driva {
	int fd;
	char *device;
};

struct driva drv = {
	.fd = 0,
	.device = "/dev/ttyACM0"
};



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

static int microm92ci_deinit(void)
{
	log_debug("m92 deinit");
	//TODO: put board into standby? no! it should go into standby just before the cpu halts
	close(drv.fd);
	//~ tty_delete_lock();
	return 1;
}

static int readdata_with_select(unsigned char *dest, int nbytes)
{
	log_debug("m92 readdata");
	struct timeval timeout;
	timeout.tv_sec = 2;
	timeout.tv_usec = 0;
	fd_set readfs;
	int maxfd = drv.fd + 1;
	//~ usleep(100);
	int bytesread = 0;
	while( bytesread < nbytes ) {
		FD_SET(drv.fd, &readfs);
		select(maxfd, &readfs, NULL, NULL, &timeout);

		int i = read(drv.fd, &dest[bytesread], 1);
		bytesread += i;
		if (i != 1) {
			break;
		}
	}
	if (bytesread != nbytes) {
		log_error("microm92ci: readdata error: expected %d bytes, but read %d bytes", nbytes, bytesread);
	}
	return bytesread;
}

static int readdata(unsigned char *dest, int nbytes)
{
	return readdata_with_select( dest, nbytes);
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
		log_error("m92: tcsetattr() failed");
		return 0;
	}
	tcflush(drv.fd, TCIFLUSH);

	log_debug("init: sending magic..");
	if (!write(drv.fd, MAGIC, sizeof MAGIC)) {
		log_error("microm92ci: failed to send magic to m92");
		microm92ci_deinit();
		return 0;
	}
	//~ usleep(200);

	log_debug("init: sending crypto init..");
	if (!write(drv.fd, INIT, sizeof INIT)) {
		log_error("microm92ci: failed to send init to m92");
		microm92ci_deinit();
		return 0;
	}
	//~ usleep(200);
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

	//joki: this sleep is critical. need to wait some time,
	// else the uC will not respond. waiting longer is not a problem.
	usleep(2000);

	crypt_bytes(CMD_CONFIRM_KEYEXCHANGE, buffer, sizeof CMD_CONFIRM_KEYEXCHANGE);
	//~ log_debug("init: sending key exchange command..");
	if (!write(drv.fd, buffer, sizeof CMD_CONFIRM_KEYEXCHANGE)) {
		log_error("microm92ci: failed to send key exchange to m92");
		microm92ci_deinit();
		return 0;
	}
	//~ usleep(200);
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
		log_error("m92: tcsetattr() failed");
		return 0;
	}

	log_debug("microm92ci: successfully initialized m92");
	return 1;
}


int main()
{
	//~ drv = hw_microm92ci;
	drv.device = "/dev/ttyACM0";

	return !microm92ci_init();
}
