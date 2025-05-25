#!/usr/bin/env python3
"""
自动将print语句迁移到集中式日志记录器的工具。
这个脚本扫描整个项目，将print语句转换为使用集中式日志记录器。
"""

import os
import re
import argparse
from pathlib import Path

def should_skip_file(file_path):
    """判断是否应跳过处理该文件"""
    # 跳过迁移脚本本身
    if "migrate_prints_to_logger.py" in str(file_path):
        return True
        
    # 跳过特定目录
    skip_dirs = ['.git', '.venv', '__pycache__', 'logs', 'data', '.pytest_cache']
    for skip_dir in skip_dirs:
        if skip_dir in str(file_path):
            return True
            
    # 只处理Python文件
    if not str(file_path).endswith('.py'):
        return True
        
    return False

def replace_prints(file_content):
    """替换文件中的print语句为logger调用"""
    # 添加导入语句
    if 'from common import' in file_content:
        # 如果已经导入common，但没有导入print_log
        if 'print_log' not in file_content:
            # 找到现有import语句并增强它
            file_content = re.sub(
                r'from common import ([^\n]+)',
                r'from common import \1, print_log',
                file_content
            )
    else:
        # 添加新的导入语句
        file_content = re.sub(
            r'(""".+?"""|\'\'\'.*?\'\'\'|\n|^)',
            r'\1from common import print_log\n',
            file_content,
            count=1
        )
    
    # 替换错误相关的print语句
    file_content = re.sub(
        r'print\(f?"❌\s*(.+?)"\)',
        r'print_log(f"\1", level="error")',
        file_content
    )
    
    # 替换成功相关的print语句
    file_content = re.sub(
        r'print\(f?"✅\s*(.+?)"\)',
        r'print_log(f"\1", level="info")',
        file_content
    )
    
    # 替换警告相关的print语句
    file_content = re.sub(
        r'print\(f?"⚠️\s*(.+?)"\)',
        r'print_log(f"\1", level="warning")',
        file_content
    )
    
    # 替换一般的print语句
    file_content = re.sub(
        r'print\((f?".+?")\)',
        r'print_log(\1)',
        file_content
    )
    
    return file_content

def process_file(file_path, dry_run=False):
    """处理单个文件，替换print语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查文件是否包含print语句
        if 'print(' not in content:
            return 0
            
        new_content = replace_prints(content)
        
        # 如果内容变化了，写回文件
        if new_content != content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            print(f"{'[DRY RUN] ' if dry_run else ''}修改了文件: {file_path}")
            return 1
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
    return 0

def process_directory(directory, dry_run=False):
    """递归处理目录中的所有Python文件"""
    modified_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            
            if should_skip_file(file_path):
                continue
                
            modified_count += process_file(file_path, dry_run)
    
    return modified_count

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将print语句迁移到使用logger')
    parser.add_argument('--directory', '-d', default='.', help='要处理的目录')
    parser.add_argument('--dry-run', action='store_true', help='不实际修改文件，只显示会被修改的内容')
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists() or not directory.is_dir():
        print(f"错误: {directory} 不是有效目录")
        return 1
    
    print(f"开始处理目录: {directory}")
    modified_count = process_directory(directory, args.dry_run)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}处理完成，修改了 {modified_count} 个文件")
    
    return 0

if __name__ == "__main__":
    exit(main()) 