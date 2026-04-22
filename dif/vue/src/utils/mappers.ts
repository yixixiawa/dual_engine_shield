/**
 * 统一的数据映射工具库
 * 集中管理所有类型的映射函数，避免重复代码
 */

/**
 * 漏洞类型映射
 */
export const VulnerabilityTypeMappers = {
  /**
   * 映射漏洞类型为显示文本
   */
  mapVulnType(type: string): string {
    const typeMap: { [key: string]: string } = {
      'SQL_INJECTION': 'SQL 注入',
      'XSS': '跨站脚本',
      'COMMAND_INJECTION': '命令注入',
      'PATH_TRAVERSAL': '路径遍历',
      'BUFFER_OVERFLOW': '缓冲区溢出',
      'CODE_INJECTION': '代码注入',
      'DESERIAL_INJECTION': '反序列化漏洞',
      'AUTHENTICATION_BYPASS': '认证绕过',
      'AUTHORIZATION_BYPASS': '权限绕过',
      'RACE_CONDITION': '竞态条件',
      'INFORMATION_DISCLOSURE': '信息泄露',
      'CRYPTOGRAPHIC_WEAKNESS': '密码学弱点',
      'USE_OF_INSECURE_FUNCTION': '不安全函数使用',
      'IMPROPER_INPUT_VALIDATION': '不适当的输入验证',
      'IMPROPER_OUTPUT_ENCODING': '不适当的输出编码',
      'UNRESTRICTED_FILE_UPLOAD': '不受限制的文件上传',
      'XXEJECTION': 'XXE 注入',
      'LDAP_INJECTION': 'LDAP 注入',
      'XPATH_INJECTION': 'XPath 注入',
      'OS_COMMAND_INJECTION': '操作系统命令注入',
      'TEMPLATE_INJECTION': '模板注入',
      'REMOTE_CODE_EXECUTION': '远程代码执行',
      'OPEN_REDIRECT': '开放重定向',
      'INSECURE_DIRECT_OBJECT_REFERENCE': '不安全的直接对象引用',
      'BROKEN_AUTHENTICATION': '认证破坏',
      'BROKEN_ACCESS_CONTROL': '访问控制破坏',
      'SENSITIVE_DATA_EXPOSURE': '敏感数据泄露',
      'XML_EXTERNAL_ENTITY': 'XML 外部实体',
      'BROKEN_FUNCTION_LEVEL_ACCESS_CONTROL': '函数级别访问控制破坏',
    };
    return typeMap[type] || type;
  },

  /**
   * 映射漏洞严重等级
   */
  mapSeverity(severity: string): { label: string; color: string; number: number } {
    const severityMap: { [key: string]: { label: string; color: string; number: number } } = {
      'CRITICAL': { label: '严重', color: '#ff4d4f', number: 4 },
      'HIGH': { label: '高', color: '#ff7a45', number: 3 },
      'MEDIUM': { label: '中', color: '#faad14', number: 2 },
      'LOW': { label: '低', color: '#52c41a', number: 1 },
    };
    return severityMap[severity?.toUpperCase()] || severityMap['LOW'];
  },

  /**
   * 映射CWE ID 为漏洞名称
   */
  mapCweId(cweId: string): string {
    const cweMap: { [key: string]: string } = {
      'CWE-89': 'SQL 注入',
      'CWE-79': '跨站脚本 (XSS)',
      'CWE-78': 'OS 命令注入',
      'CWE-22': '路径遍历',
      'CWE-120': '缓冲区溢出',
      'CWE-95': '代码注入',
      'CWE-502': '不信任数据的反序列化',
      'CWE-287': '不当的认证',
      'CWE-639': '授权机制的不当实现',
      'CWE-362': '竞态条件',
      'CWE-200': '信息泄露',
      'CWE-326': '密码学强度不足',
      'CWE-327': '使用破坏的或有危险的密码算法',
      'CWE-434': '不受限制的上传危险文件类型',
      'CWE-611': 'XML 外部实体引用',
    };
    return cweMap[cweId] || cweId;
  },
};

/**
 * 钓鱼检测映射
 */
export const PhishingTypeMappers = {
  /**
   * 映射钓鱼检测结果
   */
  mapPhishingResult(result: boolean | string): { label: string; color: string } {
    const resultMap: { [key: string]: { label: string; color: string } } = {
      'true': { label: '恶意', color: '#ff4d4f' },
      'false': { label: '正常', color: '#52c41a' },
      'PHISHING': { label: '钓鱼网站', color: '#ff4d4f' },
      'LEGITIMATE': { label: '正常网站', color: '#52c41a' },
      'SUSPICIOUS': { label: '可疑', color: '#faad14' },
    };
    const key = String(result).toUpperCase();
    return resultMap[key] || { label: String(result), color: '#1890ff' };
  },

  /**
   * 映射钓鱼检测引擎名称
   */
  mapEngineName(engine: string): string {
    const engineMap: { [key: string]: string } = {
      'URL_REPUTATION': 'URL 信誉',
      'DOMAIN_REPUTATION': '域名信誉',
      'PHISH_TANK': 'PhishTank',
      'GOOGLE_SAFE_BROWSING': 'Google 安全浏览',
      'URLHAUS': 'URLhaus',
      'OPENPHISH': 'OpenPhish',
      'SIMILAR_DOMAIN': '相似域名检测',
      'CERTIFICATE': '证书分析',
      'DNS_RECORDS': 'DNS 记录分析',
      'WHOIS': 'WHOIS 信息',
      'IP_REPUTATION': 'IP 信誉',
      'MACHINE_LEARNING': '机器学习',
      'CONTENT_ANALYSIS': '内容分析',
      'VISUAL_SIMILARITY': '视觉相似度',
    };
    return engineMap[engine] || engine;
  },

  /**
   * 映射检测方法
   */
  mapDetectionMethod(method: string): string {
    const methodMap: { [key: string]: string } = {
      'BLACKLIST': '黑名单检测',
      'WHITELIST': '白名单检测',
      'REPUTATION': '信誉评分',
      'MACHINE_LEARNING': '机器学习',
      'HEURISTIC': '启发式',
      'SIGNATURE': '签名检测',
    };
    return methodMap[method] || method;
  },
};

/**
 * 任务状态映射
 */
export const TaskStatusMappers = {
  /**
   * 映射任务状态
   */
  mapTaskStatus(status: string): { label: string; color: string } {
    const statusMap: { [key: string]: { label: string; color: string } } = {
      'PENDING': { label: '待处理', color: '#d9d9d9' },
      'RUNNING': { label: '运行中', color: '#1890ff' },
      'SUCCESS': { label: '成功', color: '#52c41a' },
      'FAILED': { label: '失败', color: '#ff4d4f' },
      'CANCELLED': { label: '已取消', color: '#faad14' },
      'TIMEOUT': { label: '超时', color: '#ff7a45' },
    };
    return statusMap[status?.toUpperCase()] || statusMap['PENDING'];
  },

  /**
   * 映射任务类型
   */
  mapTaskType(type: string): string {
    const typeMap: { [key: string]: string } = {
      'CODE_DETECTION': '代码检测',
      'PHISHING_DETECTION': '钓鱼检测',
      'IP_ANALYSIS': 'IP 分析',
      'BATCH_DETECTION': '批量检测',
      'CUSTOM_SCAN': '自定义扫描',
    };
    return typeMap[type] || type;
  },
};

/**
 * 语言映射
 */
export const LanguageMappers = {
  /**
   * 映射编程语言显示名称
   */
  mapLanguage(lang: string): string {
    const languageMap: { [key: string]: string } = {
      'python': 'Python',
      'javascript': 'JavaScript',
      'typescript': 'TypeScript',
      'java': 'Java',
      'csharp': 'C#',
      'cpp': 'C++',
      'c': 'C',
      'go': 'Go',
      'rust': 'Rust',
      'php': 'PHP',
      'ruby': 'Ruby',
      'kotlin': 'Kotlin',
      'swift': 'Swift',
      'objective-c': 'Objective-C',
      'sql': 'SQL',
      'html': 'HTML',
      'css': 'CSS',
      'jsx': 'JSX',
      'tsx': 'TSX',
      'vue': 'Vue',
    };
    return languageMap[lang?.toLowerCase()] || lang;
  },

  /**
   * 映射语言到文件扩展名
   */
  mapLanguageToExtension(lang: string): string[] {
    const extensionMap: { [key: string]: string[] } = {
      'python': ['.py', '.pyw', '.pyi'],
      'javascript': ['.js', '.mjs'],
      'typescript': ['.ts', '.tsx'],
      'java': ['.java'],
      'csharp': ['.cs'],
      'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
      'c': ['.c', '.h'],
      'go': ['.go'],
      'rust': ['.rs'],
      'php': ['.php', '.php3', '.php4', '.php5'],
      'ruby': ['.rb', '.rbw'],
      'kotlin': ['.kt', '.kts'],
      'swift': ['.swift'],
      'objective-c': ['.m', '.mm', '.h'],
      'sql': ['.sql'],
      'html': ['.html', '.htm'],
      'css': ['.css', '.scss', '.sass', '.less'],
    };
    return extensionMap[lang?.toLowerCase()] || [];
  },

  /**
   * 映射MIME类型到语言
   */
  mapMimeToLanguage(mimeType: string): string {
    const mimeMap: { [key: string]: string } = {
      'application/x-python': 'python',
      'application/javascript': 'javascript',
      'application/typescript': 'typescript',
      'text/javascript': 'javascript',
      'text/typescript': 'typescript',
      'text/x-java': 'java',
      'text/x-csharp': 'csharp',
      'text/x-c++src': 'cpp',
      'text/x-csrc': 'c',
      'text/x-go': 'go',
      'text/x-rust': 'rust',
      'application/x-php': 'php',
      'text/x-ruby': 'ruby',
      'text/x-sql': 'sql',
      'text/html': 'html',
      'text/css': 'css',
    };
    return mimeMap[mimeType?.toLowerCase()] || 'text/plain';
  },
};

/**
 * 导出所有映射器
 */
export const AllMappers = {
  vulnerability: VulnerabilityTypeMappers,
  phishing: PhishingTypeMappers,
  taskStatus: TaskStatusMappers,
  language: LanguageMappers,
};
