#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 漏洞测试 - SQL 注入
"""

import sqlite3

def get_user_by_id(user_id):
    """
    危险：SQL 注入漏洞
    """
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # CWE-89: SQL Injection
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result


def execute_system_command(cmd):
    """
    危险：命令注入漏洞
    """
    import os
    
    # CWE-78: OS Command Injection
    user_input = input("Enter command: ")
    os.system("ls " + user_input)


def unsafe_eval(code):
    """
    危险：eval 执行用户输入
    """
    # CWE-95: Eval Injection
    user_code = input("Enter code: ")
    eval(user_code)


def unsafe_pickle(data):
    """
    危险：反序列化不信任的数据
    """
    import pickle
    
    # CWE-502: Deserialization of Untrusted Data
    user_data = input("Enter data: ").encode()
    obj = pickle.loads(user_data)
    return obj


if __name__ == '__main__':
    get_user_by_id("1")
