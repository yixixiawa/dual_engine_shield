/**
 * 统一的文件处理工具库
 * 集中管理所有文件操作、验证和处理逻辑
 */

/**
 * 文件验证工具
 */
export class FileValidator {
  /**
   * 验证单个文件
   */
  static validateFile(file: File, options: FileValidationOptions = {}): ValidationResult {
    const {
      maxSize = 100 * 1024 * 1024, // 默认100MB
      allowedExtensions = [],
      allowedMimeTypes = [],
      minSize = 0,
    } = options;

    // 检查文件大小
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `文件过大，最大限制 ${this.formatFileSize(maxSize)}`,
      };
    }

    if (file.size < minSize) {
      return {
        valid: false,
        error: `文件过小，最小限制 ${this.formatFileSize(minSize)}`,
      };
    }

    // 检查文件扩展名
    if (allowedExtensions.length > 0) {
      const extension = this.getFileExtension(file.name);
      if (!allowedExtensions.includes(extension)) {
        return {
          valid: false,
          error: `不支持的文件类型: ${extension}，允许类型: ${allowedExtensions.join(', ')}`,
        };
      }
    }

    // 检查MIME类型
    if (allowedMimeTypes.length > 0) {
      if (!allowedMimeTypes.includes(file.type)) {
        return {
          valid: false,
          error: `不支持的MIME类型: ${file.type}`,
        };
      }
    }

    return { valid: true };
  }

  /**
   * 验证多个文件
   */
  static validateFiles(
    files: File[],
    options: FileValidationOptions = {}
  ): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const result = this.validateFile(files[i], options);
      if (!result.valid) {
        errors.push(`${files[i].name}: ${result.error}`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * 获取文件扩展名
   */
  static getFileExtension(filename: string): string {
    const lastDot = filename.lastIndexOf('.');
    return lastDot === -1 ? '' : filename.substring(lastDot).toLowerCase();
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * 检查是否为代码文件
   */
  static isCodeFile(filename: string): boolean {
    const codeExtensions = [
      '.js', '.ts', '.tsx', '.jsx', '.py', '.java', '.cpp', '.c',
      '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.kt',
      '.swift', '.m', '.mm', '.html', '.css', '.scss', '.sass',
      '.sql', '.xml', '.json', '.yaml', '.yml', '.sh', '.bash',
      '.vue', '.jsx', '.tsx',
    ];
    const ext = this.getFileExtension(filename);
    return codeExtensions.includes(ext);
  }

  /**
   * 检查是否为压缩文件
   */
  static isCompressedFile(filename: string): boolean {
    const compressedExtensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'];
    const ext = this.getFileExtension(filename);
    return compressedExtensions.includes(ext);
  }
}

/**
 * 文件读取工具
 */
export class FileReader {
  /**
   * 读取文件内容为字符串
   */
  static readAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new window.FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(new Error('无法读取文件'));
      reader.readAsText(file);
    });
  }

  /**
   * 读取文件内容为Base64
   */
  static readAsBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new window.FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(',')[1]); // 移除 data:xxx;base64, 前缀
      };
      reader.onerror = () => reject(new Error('无法读取文件'));
      reader.readAsDataURL(file);
    });
  }

  /**
   * 读取文件内容为ArrayBuffer
   */
  static readAsArrayBuffer(file: File): Promise<ArrayBuffer> {
    return new Promise((resolve, reject) => {
      const reader = new window.FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.onerror = () => reject(new Error('无法读取文件'));
      reader.readAsArrayBuffer(file);
    });
  }

  /**
   * 批量读取文件
   */
  static readMultipleFiles(files: File[], format: 'text' | 'base64' = 'text'): Promise<FileContent[]> {
    const promises = files.map(async (file) => {
      const content = format === 'base64' ? await this.readAsBase64(file) : await this.readAsText(file);
      return { file, content };
    });
    return Promise.all(promises);
  }
}

/**
 * 文件上传工具
 */
export class FileUploadHelper {
  /**
   * 上传单个文件
   */
  static async uploadFile(
    file: File,
    url: string,
    options: UploadOptions = {}
  ): Promise<UploadResponse> {
    const {
      onProgress,
      headers = {},
      method = 'POST',
      timeout = 30000,
    } = options;

    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // 进度回调
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const percentComplete = (event.loaded / event.total) * 100;
            onProgress(percentComplete);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            resolve({ success: true, data: xhr.responseText });
          }
        } else {
          reject(new Error(`上传失败: ${xhr.status} ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('网络错误'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('上传已取消'));
      });

      // 设置超时
      xhr.timeout = timeout;
      xhr.ontimeout = () => {
        reject(new Error('上传超时'));
      };

      xhr.open(method, url);

      // 添加自定义headers
      Object.entries(headers).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });

      xhr.send(formData);
    });
  }

  /**
   * 批量上传文件
   */
  static async uploadMultipleFiles(
    files: File[],
    url: string,
    options: UploadOptions = {}
  ): Promise<UploadResponse[]> {
    const results: UploadResponse[] = [];
    const total = files.length;

    for (let i = 0; i < total; i++) {
      try {
        const result = await this.uploadFile(files[i], url, {
          ...options,
          onProgress: (progress) => {
            const overallProgress = ((i + progress / 100) / total) * 100;
            options.onProgress?.(overallProgress);
          },
        });
        results.push(result);
      } catch (error) {
        results.push({
          success: false,
          error: (error as Error).message,
          file: files[i].name,
        });
      }
    }

    return results;
  }

  /**
   * 创建下载链接并触发下载
   */
  static downloadFile(data: Blob, filename: string): void {
    const url = window.URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * 生成临时文件URL
   */
  static createObjectURL(blob: Blob): string {
    return window.URL.createObjectURL(blob);
  }

  /**
   * 释放临时文件URL
   */
  static revokeObjectURL(url: string): void {
    window.URL.revokeObjectURL(url);
  }
}

/**
 * 文件夹扫描工具
 */
export class FolderScanner {
  /**
   * 从 DataTransfer 中提取文件列表
   */
  static async extractFilesFromDataTransfer(dataTransfer: DataTransfer): Promise<File[]> {
    const files: File[] = [];

    const entries = Array.from(dataTransfer.items).map((item) => item.webkitGetAsEntry());

    for (const entry of entries) {
      if (entry?.isFile) {
        files.push(await (entry as any).file());
      } else if (entry?.isDirectory) {
        const dirFiles = await this.readDirectory(entry as any);
        files.push(...dirFiles);
      }
    }

    return files;
  }

  /**
   * 递归读取文件夹
   */
  private static async readDirectory(dirEntry: any): Promise<File[]> {
    const files: File[] = [];
    const reader = dirEntry.createReader();

    return new Promise((resolve) => {
      const readEntries = () => {
        reader.readEntries(
          async (entries: any[]) => {
            if (entries.length === 0) {
              resolve(files);
              return;
            }

            for (const entry of entries) {
              if (entry.isFile) {
                files.push(await new Promise((res) => entry.file(res)));
              } else if (entry.isDirectory) {
                const subFiles = await this.readDirectory(entry);
                files.push(...subFiles);
              }
            }

            readEntries();
          },
          () => {
            resolve(files);
          }
        );
      };

      readEntries();
    });
  }
}

/**
 * 类型定义
 */
export interface FileValidationOptions {
  maxSize?: number;
  minSize?: number;
  allowedExtensions?: string[];
  allowedMimeTypes?: string[];
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export interface FileContent {
  file: File;
  content: string;
}

export interface UploadOptions {
  onProgress?: (progress: number) => void;
  headers?: Record<string, string>;
  method?: string;
  timeout?: number;
}

export interface UploadResponse {
  success: boolean;
  data?: any;
  error?: string;
  file?: string;
}
