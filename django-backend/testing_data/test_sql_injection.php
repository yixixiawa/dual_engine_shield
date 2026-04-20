<?php
// PHP 漏洞测试

// CWE-89: SQL Injection
function getUserById($userId) {
    global $pdo;
    $query = "SELECT * FROM users WHERE id = " . $userId;  // SQL 注入
    return $pdo->query($query)->fetch();
}

// CWE-78: OS Command Injection
function executeBackup($filename) {
    $cmd = "tar -czf /backups/" . $filename . ".tar.gz /data";
    shell_exec($cmd);  // 命令注入
}

// CWE-79: XSS 漏洞
function displayComment($comment) {
    echo "<div>" . $comment . "</div>";  // 不转义用户输入
}

// CWE-22: Path Traversal
function readFile($filename) {
    $filepath = "/var/www/files/" . $filename;
    return file_get_contents($filepath);  // 路径遍历漏洞
}

// CWE-798: 硬编码凭证
$DATABASE_PASSWORD = "admin123";  // 硬编码密码
$API_KEY = "sk-1234567890abcdef";  // 硬编码 API 密钥

// CWE-200: 信息泄露
if ($error) {
    die("Database error: " . $mysqli->error);  // 泄露错误信息
}

// 获取用户输入并直接使用
$userId = $_GET['id'];
$user = getUserById($userId);

$comment = $_POST['comment'];
displayComment($comment);

// 不安全的文件操作
$uploadFile = $_FILES['file']['tmp_name'];
$targetFile = "/uploads/" . $_FILES['file']['name'];
move_uploaded_file($uploadFile, $targetFile);  // 没有验证文件类型
?>
