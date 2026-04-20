package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os/exec"

	_ "github.com/lib/pq"
)

// Go 漏洞测试

// CWE-89: SQL Injection
func getUserByID(db *sql.DB, userID string) {
	// 不安全：SQL 注入
	query := "SELECT * FROM users WHERE id = " + userID
	rows, _ := db.Query(query)
	defer rows.Close()
}

// CWE-78: OS Command Injection
func executeCommand(cmd string) {
	// 不安全：命令注入
	exec.Command("bash", "-c", "ls "+cmd).Run()
}

// CWE-416: Use After Free (Go 中不常见，但可能在 cgo 中出现)
// Go 的内存管理通常会防止这类问题

// CWE-200: 信息泄露
func handleRequest(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("id")
	fmt.Fprintf(w, "Processing user: %s\n", userID)

	// 泄露系统信息
	fmt.Fprintf(w, "Error: %s\n", "sensitive error info")
}

// CWE-611: XXE (XML External Entity)
func parseXML(xmlData string) {
	// 需要解析 XML，可能存在 XXE 风险
	// 此处省略具体实现
}

func main() {
	// 不安全的 HTTP 处理
	http.HandleFunc("/user", handleRequest)

	// 不验证重定向 URL
	http.HandleFunc("/redirect", func(w http.ResponseWriter, r *http.Request) {
		redirectURL := r.URL.Query().Get("url")
		http.Redirect(w, r, redirectURL, http.StatusFound) // 不安全重定向
	})

	http.ListenAndServe(":8080", nil)
}
