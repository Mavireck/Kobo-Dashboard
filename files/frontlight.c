#include <stdio.h>
#include <fcntl.h>
#include <sys/ioctl.h>

int main(int argc, char *argv[])
{
    if ( argc != 2 ) {
        printf("Usage: %s brightness \n", argv[0]);
        return 1;
    }
    
    int light;

    // Open the file for reading and writing
    if ((light = open("/dev/ntx_io", O_RDWR)) == -1) {
        printf("Error opening ntx_io device");	
    }

    int brightness = atoi ( (argv[1]) );
    ioctl(light, 241, brightness);

    return 0;
}
