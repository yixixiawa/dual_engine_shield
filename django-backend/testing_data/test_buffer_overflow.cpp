#include <iostream>
#include <cstring>
using namespace std;

// C++ 漏洞测试

void buffer_overflow() {
    // CWE-121: Stack-based Buffer Overflow
    char buffer[10];
    strcpy(buffer, "This is a very long string that will overflow");
}

void use_after_free() {
    // CWE-416: Use After Free
    int* ptr = new int(5);
    delete ptr;
    cout << *ptr << endl;  // 使用已释放的内存
}

void null_pointer_dereference() {
    // CWE-476: NULL Pointer Dereference
    int* ptr = nullptr;
    cout << *ptr << endl;  // 解引用空指针
}

int main() {
    buffer_overflow();
    return 0;
}
