
#ifndef CORSAIR_H
#define CORSAIR_H

#include <stdio.h>
#include <string.h>
#include <math.h>
#include <openssl/x509.h>
#include <openssl/pem.h>
#include <openssl/bio.h>
#include <openssl/err.h>

#define CERTFILE 1
#define GENRSA 2


int parse_arguments(int argc, char *argv[]);
//void RSA_get_modulus(unsigned char *binary, size_t size);
//void RSA_get_exponent(unsigned char *binary, size_t size);

//void readfile(char filename[], int mode);

void usage(char *argv[]);

//char *get_next_line(int fd);

// unsigned char *base64_decode(const char *data,
//                              size_t input_length,
//                              size_t *output_length);

#endif
