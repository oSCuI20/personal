/*
 * compile, gcc -o corsair corsair.c -lssl -lcrypto -Wall -Werror -Wextra
 */

#include "corsair.h"

char buff[4096];
char filename[128];
int mode = 0;
int fd;

int main(int argc, char *argv[]) {
	parse_arguments(argc, argv);

	OpenSSL_add_all_algorithms();
  ERR_load_BIO_strings();
  ERR_load_crypto_strings();

 	if (mode == CERTFILE) {
		X509		  		*cert;
		BIO 					*i = BIO_new(BIO_s_file());
		BIO				 		*o = BIO_new_fp(stdout, BIO_NOCLOSE);

		BIO_read_filename(i, filename);  //read file

		if (! (cert = PEM_read_bio_X509(i, NULL, 0, NULL))) {  //load cert
			BIO_printf(o, "Error load certfile\n");
			return -1;
		}

		X509_print_ex(o, cert, XN_FLAG_COMPAT, X509_FLAG_COMPAT);  //print detail

		X509_free(cert);
		BIO_free_all(i);
		BIO_free_all(o);
 	} else if (mode == GENRSA) {
		
	}

 	return 0;
}

int parse_arguments(int argc, char *argv[]) {
	int i;

	for (i = 1; i < argc; i++) {
		if (strcmp(argv[i], "--help") == 0) {
			usage(argv);
		} else if (strcmp(argv[i], "--certfile") == 0) {
			i += 1;
			mode = CERTFILE;
			strcpy(filename, argv[i]);
		} else if (strcmp(argv[i], "--genrsa") == 0) {
			//i += 1;
			mode = GENRSA;

			strcpy(filename, argv[i]);
		} else {
			printf("No se reconoce la opción %s", argv[i]);
			usage(argv);
		}
	}

	return 0;
}

void usage(char *argv[]) {
	printf("%s [--cert-file|--genrsa] [--help]\n", argv[0]);
	exit(EXIT_SUCCESS);
}
