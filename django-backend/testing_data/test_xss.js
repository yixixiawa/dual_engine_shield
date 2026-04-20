// JavaScript 漏洞测试 - XSS

// CWE-79: Cross-site Scripting (XSS)
function displayUserComment(comment) {
    document.getElementById('comments').innerHTML = comment;  // 不安全的 DOM 操作
}

// CWE-94: Code Injection
function executeUserCode(code) {
    eval(code);  // 执行用户输入的代码
}

// CWE-601: Open Redirect
function redirect(url) {
    window.location.href = url;  // 不安全的重定向
}

// CWE-352: CSRF - 缺少 CSRF 令牌
async function updateUserProfile(userData) {
    const response = await fetch('/api/profile', {
        method: 'POST',
        body: JSON.stringify(userData),
        headers: { 'Content-Type': 'application/json' }
        // 缺少 CSRF 令牌验证
    });
    return response.json();
}

// 测试
displayUserComment('<img src=x onerror="alert(\'XSS\')" />');
executeUserCode('alert("Injected code")');
