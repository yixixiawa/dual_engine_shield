#include <stdio.h>
#include <string.h>

int main() {
    char buffer[10];
    char secret[] = "PASSWORD_123";

    printf("请输入一些文本: ");
    gets(buffer);  // 危险！不检查输入长度

    printf("你输入的是: %s\n", buffer);
    printf("秘密数据: %s\n", secret);

    return 0;
}