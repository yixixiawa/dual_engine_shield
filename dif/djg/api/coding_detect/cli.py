#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR 漏洞检测工具 - CLI命令行接口
"""

import argparse
import sys
import logging
from pathlib import Path

from .scanner import VulnScanner
from .config import VULNLMMR_MODEL_PATH, get_supported_languages

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """配置日志"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='vulnscan',
        description='VR 多语言漏洞检测工具 - 基于UCSB-SURFI_VR-7B模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 扫描整个项目
  python -m vulnscan_tool.cli scan ./my_project --output ./results

  # 扫描单个文件
  python -m vulnscan_tool.cli file ./src/vulnerable.c

  # 检测代码片段
  python -m vulnscan_tool.cli code "strcpy(buf, user_input)" --lang c

  # 只检测特定CWE
  python -m vulnscan_tool.cli scan ./project --cwe CWE-787 CWE-120

  # 只扫描Python和C代码
  python -m vulnscan_tool.cli scan ./project --lang python c
        """
    )
    
    # 全局参数
    parser.add_argument(
        '--model-path',
        type=str,
        default=VULNLMMR_MODEL_PATH,
        help=f'模型路径 (默认: {VULNLMMR_MODEL_PATH})'
    )
    parser.add_argument(
        '--no-quantization',
        action='store_true',
        help='禁用4-bit量化（需要更多显存）'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 1. scan命令 - 扫描目录
    scan_parser = subparsers.add_parser('scan', help='扫描整个项目目录')
    scan_parser.add_argument('target', type=str, help='目标目录路径')
    scan_parser.add_argument(
        '--output', '-o',
        type=str,
        default='./vulnscan_output',
        help='输出目录 (默认: ./vulnscan_output)'
    )
    scan_parser.add_argument(
        '--lang', '-l',
        type=str,
        nargs='+',
        choices=get_supported_languages(),
        help=f'指定要扫描的语言 (默认: 全部支持的语言)'
    )
    scan_parser.add_argument(
        '--cwe',
        type=str,
        nargs='+',
        help='指定要检测的CWE ID列表'
    )
    scan_parser.add_argument(
        '--skip-safe',
        action='store_true',
        help='跳过安全代码的输出'
    )
    
    # 2. file命令 - 扫描单个文件
    file_parser = subparsers.add_parser('file', help='扫描单个代码文件')
    file_parser.add_argument('file', type=str, help='目标文件路径')
    file_parser.add_argument(
        '--cwe',
        type=str,
        nargs='+',
        help='指定要检测的CWE ID列表'
    )
    file_parser.add_argument(
        '--output', '-o',
        type=str,
        help='保存结果到JSON文件'
    )
    
    # 3. code命令 - 检测代码片段
    code_parser = subparsers.add_parser('code', help='检测代码片段')
    code_parser.add_argument('code', type=str, help='代码片段（用引号包裹）')
    code_parser.add_argument(
        '--lang', '-l',
        type=str,
        required=True,
        choices=get_supported_languages(),
        help='编程语言'
    )
    code_parser.add_argument(
        '--cwe',
        type=str,
        nargs='+',
        help='指定要检测的CWE ID列表'
    )
    
    return parser


def cmd_scan(args, scanner: VulnScanner):
    """执行scan命令"""
    logger.info(f"扫描目录: {args.target}")
    
    report = scanner.scan_directory(
        target_dir=args.target,
        languages=args.lang,
        cwe_ids=args.cwe,
        output_dir=args.output
    )
    
    # 输出JSON报告
    if args.output:
        logger.info(f"✅ 报告已保存到: {args.output}")
    
    return 0 if report.vulnerabilities_found == 0 else 1


def cmd_file(args, scanner: VulnScanner):
    """执行file命令"""
    logger.info(f"扫描文件: {args.file}")
    
    results = scanner.scan_file(
        file_path=args.file,
        cwe_ids=args.cwe
    )
    
    # 打印结果
    for i, result in enumerate(results, 1):
        status = "🚨 漏洞" if result.is_vulnerable else "✅ 安全"
        print(f"\n[{i}/{len(results)}] {result.code.location.function_name or 'Unknown'}")
        print(f"  状态: {status}")
        print(f"  置信度: {result.confidence:.2f}")
        if result.is_vulnerable:
            print(f"  CWE: {result.cwe_id} - {result.cwe_name}")
            print(f"  严重程度: {result.severity.value}")
            print(f"  修复建议: {result.fix_suggestion}")
    
    # 保存JSON
    if args.output:
        import json
        output_data = {
            'file': args.file,
            'total_functions': len(results),
            'vulnerable': sum(1 for r in results if r.is_vulnerable),
            'results': [
                {
                    'function': r.code.location.function_name,
                    'is_vulnerable': r.is_vulnerable,
                    'confidence': r.confidence,
                    'cwe_id': r.cwe_id,
                    'cwe_name': r.cwe_name,
                    'severity': r.severity.value,
                    'fix_suggestion': r.fix_suggestion,
                }
                for r in results
            ]
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"结果已保存到: {args.output}")
    
    return 0


def cmd_code(args, scanner: VulnScanner):
    """执行code命令"""
    logger.info(f"检测{args.lang}代码片段")
    
    result = scanner.scan_code_snippet(
        code=args.code,
        language=args.lang,
        cwe_ids=args.cwe
    )
    
    # 打印结果
    status = "🚨 漏洞" if result.is_vulnerable else "✅ 安全"
    print(f"\n检测结果: {status}")
    print(f"置信度: {result.confidence:.2f}")
    
    if result.is_vulnerable:
        print(f"CWE: {result.cwe_id} - {result.cwe_name}")
        print(f"严重程度: {result.severity.value}")
        print(f"\n修复建议:\n{result.fix_suggestion}")
    
    print(f"\n模型分析:\n{result.reasoning_chain[:500]}...")
    
    return 0 if not result.is_vulnerable else 1


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 检查是否提供了命令
    if not args.command:
        parser.print_help()
        return 1
    
    # 设置日志
    setup_logging(args.verbose)
    
    try:
        # 创建扫描器
        scanner = VulnScanner(
            model_path=args.model_path,
            use_quantization=not args.no_quantization
        )
        
        # 执行对应命令
        if args.command == 'scan':
            exit_code = cmd_scan(args, scanner)
        elif args.command == 'file':
            exit_code = cmd_file(args, scanner)
        elif args.command == 'code':
            exit_code = cmd_code(args, scanner)
        else:
            parser.print_help()
            exit_code = 1
        
        # 清理资源
        scanner.cleanup()
        
        return exit_code
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
        return 130
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
