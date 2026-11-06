// fbpan.so: LD_PRELOAD shim that makes FBIOPAN_DISPLAY asynchronous. ARM's
// fbdev EGL pans the framebuffer inside eglSwapBuffers; on sun4i-drm's fbdev
// emulation the pan is a synchronous atomic commit that waits for the
// display's vblank (about 8 ms a frame on the render thread, VSync setting
// or not). Here the calling thread hands the pan to a helper thread and
// returns at once; the helper issues the latest requested pan (an older one
// still pending is replaced). The buffer just panned away from is drawn
// into before the pan has landed, so there can be tearing: the same as
// VSync off in general.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <linux/fb.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>

static int (*real)(int, unsigned long, void *);
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t wake = PTHREAD_COND_INITIALIZER;
static pthread_t worker;
static int started, pending, pan_fd;
static struct fb_var_screeninfo pan_var;

static void *
worker_main(void *arg)
{
	(void)arg;
	for(;;){
		pthread_mutex_lock(&lock);
		while(!pending)
			pthread_cond_wait(&wake, &lock);
		pending = 0;
		int fd = pan_fd;
		struct fb_var_screeninfo var = pan_var;
		pthread_mutex_unlock(&lock);
		real(fd, FBIOPAN_DISPLAY, &var);
	}
	return NULL;
}

int
ioctl(int fd, unsigned long request, ...)
{
	if(!real)
		real = (int (*)(int, unsigned long, void *))dlsym(RTLD_NEXT, "ioctl");
	va_list ap;
	va_start(ap, request);
	void *arg = va_arg(ap, void *);
	va_end(ap);
	static int enabled = -1;
	if(enabled < 0){
		const char *s = getenv("LCS_FBPAN_SYNC");
		enabled = !(s && *s && *s != '0');
	}
	if(request != FBIOPAN_DISPLAY || !enabled || !arg)
		return real(fd, request, arg);
	pthread_mutex_lock(&lock);
	if(!started){
		started = 1;
		pthread_create(&worker, NULL, worker_main, NULL);
	}
	pan_fd = fd;
	memcpy(&pan_var, arg, sizeof pan_var);
	pending = 1;
	pthread_cond_signal(&wake);
	pthread_mutex_unlock(&lock);
	return 0;
}
