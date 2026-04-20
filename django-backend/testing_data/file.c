#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *ptr = malloc(100);  // 分配内存
    strcpy(ptr, "敏感数据");
    
    free(ptr);  // 释放内存
    
    // 危险！ptr成了悬空指针
    printf("%s\n", ptr);  // 可能打印出之前的内容或乱码
    
    // 更危险的情况：另一段代码分配了同一块内存
    char *ptr2 = malloc(100);
    strcpy(ptr2, "恶意数据");
    
    printf("%s\n", ptr);  // 可能输出"恶意数据"
    free(ptr);  // 双重释放，导致崩溃或漏洞
    
    return 0;
}