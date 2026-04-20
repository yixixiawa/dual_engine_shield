#!/usr/bin/env ruby
# -*- coding: utf-8 -*-
# Ruby 漏洞测试

require 'sinatra'
require 'sqlite3'

# CWE-89: SQL Injection
def get_user_by_id(user_id)
  db = SQLite3.Database.new ':memory:'
  query = "SELECT * FROM users WHERE id = #{user_id}"  # SQL 注入
  db.execute(query)
end

# CWE-78: OS Command Injection
def backup_directory(dirname)
  system("tar -czf /backups/#{dirname}.tar.gz /data")  # 命令注入
end

# CWE-22: Path Traversal
def read_file(filename)
  File.read("/var/www/files/#{filename}")  # 路径遍历
end

# CWE-79: XSS - 在 Web 框架中
get '/comment' do
  comment = params[:comment]
  "<div>#{comment}</div>"  # 不转义用户输入
end

# CWE-79: ERB 模板注入
get '/user/:id' do
  user_id = params[:id]
  erb :user, locals: { id: user_id }
  # 如果 user.erb 中直接使用 <%= id %>，存在 XSS 风险
end

# CWE-798: 硬编码凭证
class Database
  API_KEY = "sk-1234567890abcdef"  # 硬编码 API 密钥
  DB_PASSWORD = "admin123"
end

# CWE-200: 信息泄露
get '/error' do
  begin
    raise "Database error: connection refused at 192.168.1.100:5432"
  rescue => e
    "Error: #{e.message}"  # 泄露错误信息
  end
end

# CWE-502: 不安全的反序列化
def load_user_data(serialized_data)
  Marshal.load(serialized_data)  # 不安全的反序列化
end

# CWE-95: Eval 注入
def execute_rule(rule)
  eval(rule)  # 执行用户提供的代码
end

# 使用示例
user_id = ARGV[0]
get_user_by_id(user_id)

backup_directory("important_data/../../../etc")
read_file(user_id)

execute_rule(params[:rule])
