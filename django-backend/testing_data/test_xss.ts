// TypeScript 漏洞测试

// CWE-79: XSS 漏洞
function displayComment(comment: any): void {
    const element = document.getElementById('comments');
    if (element) {
        element.innerHTML = comment;  // 不安全的类型转换和 DOM 操作
    }
}

// CWE-94: Code Injection
function executeCode(code: any): void {
    eval(code);  // 即使在 TypeScript 中也不安全
}

// CWE-502: 不安全的反序列化
function parseUserData(data: any): any {
    // 直接使用用户输入作为对象
    return Object.assign({}, JSON.parse(data));
}

// CWE-200: 信息泄露
function logSensitiveData(user: any): void {
    console.log(`User: ${user.name}, Password: ${user.password}`);
}

interface UserData {
    name: string;
    data: any;  // 类型过于宽泛，可能导致问题
}

const vulnerableUser: UserData = {
    name: 'test',
    data: '<script>alert("XSS")</script>'
};

displayComment(vulnerableUser.data);
