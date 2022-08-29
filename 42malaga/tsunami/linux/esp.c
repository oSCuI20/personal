#include <stdio.h>

int main() {
	register int i asm("esp");
	printf("$esp => %#010x\n", i);
	return 0;
}
