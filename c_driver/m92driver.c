/****************************************************************************
** m92driver ***************************************************************
****************************************************************************
*
* tests for microm92ci
*
*
*/

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <termios.h>

#define log_error (printf)
#define log_debug (printf)
#define log_trace (printf)

struct ir_remote { };
struct decode_ctx_t { };

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

static unsigned char b[NUMBYTES];
static struct timeval start, end, last;
typedef unsigned long __u64;
typedef __u64 ir_code;
static ir_code code;

static int microm92ci_decode(struct ir_remote* remote, struct decode_ctx_t* ctx);
static int microm92ci_init(void);
static int microm92ci_deinit(void);
static char* microm92ci_rec(struct ir_remote* remotes);
static int tty_create_lock() {return 1;};
static int tty_delete_lock() {return 1;};

#define MICROM92CI_H
#include "microm92ci_functions.c"

int main()
{
	return !microm92ci_init();
}
