// Rust 漏洞测试

use std::process::Command;
use std::fs::File;
use std::io::Read;

// CWE-78: OS Command Injection (可能的风险，尽管 Rust 提供了较好的安全保证)
fn execute_command(user_input: &str) {
    let output = Command::new("sh")
        .arg("-c")
        .arg(format!("ls {}", user_input))  // 可能的命令注入
        .output();
}

// CWE-22: Path Traversal
fn read_file(filename: &str) -> Result<String, std::io::Error> {
    let filepath = format!("/var/www/files/{}", filename);
    let mut file = File::open(&filepath)?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

// CWE-200: 信息泄露
fn process_request(user_id: &str) -> String {
    match validate_user(user_id) {
        Ok(_) => "OK".to_string(),
        Err(e) => format!("Error details: {:?}", e),  // 泄露内部错误细节
    }
}

fn validate_user(user_id: &str) -> Result<(), String> {
    // 模拟验证
    if user_id.is_empty() {
        Err("Database connection failed at 192.168.1.100:5432".to_string())
    } else {
        Ok(())
    }
}

// CWE-476: Null Pointer Dereference (Rust 中通常用 Option 或 Result 处理)
fn unsafe_dereference(ptr: Option<&str>) -> &str {
    match ptr {
        Some(s) => s,
        None => {
            // 虽然 Rust 会在编译时捕获大多数此类问题
            // 但在 unsafe 代码块中可能出现
            unsafe {
                let raw_ptr = std::ptr::null::<str>();
                &*raw_ptr  // 不安全操作
            }
        }
    }
}

fn main() {
    execute_command("test");
    let contents = read_file("../../etc/passwd");
    println!("{:?}", contents);
}
