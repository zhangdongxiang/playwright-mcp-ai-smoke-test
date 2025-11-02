#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查并安装项目依赖
"""
import subprocess
import sys
from pathlib import Path


def check_package(package_line):
    """
    检查单个包是否已安装
    
    Args:
        package_line: requirements.txt 中的一行，如 "playwright==1.40.0"
    
    Returns:
        (package_name, is_installed)
    """
    # 提取包名（去掉版本号约束）
    package_name = package_line.strip().split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
    
    if not package_name or package_name.startswith('#'):
        return None, False
    
    # 包名到模块名的映射（处理特殊情况）
    package_module_map = {
        'python-dotenv': 'dotenv',
        'Pillow': 'PIL',
        'pydantic': 'pydantic',
        'playwright': 'playwright',
        'openai': 'openai',
        'matplotlib': 'matplotlib',
        'mcp': 'mcp',
    }
    
    # 获取对应的模块名
    if package_name in package_module_map:
        module_name = package_module_map[package_name]
    else:
        # 默认转换规则：将连字符替换为下划线
        module_name = package_name.replace('-', '_')
    
    # 尝试导入模块
    try:
        __import__(module_name)
        return package_name, True
    except ImportError:
        # 如果主要模块名失败，尝试其他可能的模块名
        # 例如：python-dotenv 也可能尝试 dotenv
        if package_name == 'python-dotenv':
            try:
                import dotenv
                return package_name, True
            except ImportError:
                pass
        elif package_name == 'Pillow':
            try:
                import PIL
                return package_name, True
            except ImportError:
                pass
        
        return package_name, False


def main():
    """主函数"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("[警告] 未找到 requirements.txt 文件")
        return 1
    
    print("[1/3] 检查项目依赖...")
    print("正在检查依赖包...")
    
    missing_packages = []
    installed_packages = []
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            package_name, is_installed = check_package(line)
            if package_name is None:
                continue
            
            if is_installed:
                print(f"    [已安装] {package_name}")
                installed_packages.append(package_name)
            else:
                print(f"    [缺失] {line}")
                missing_packages.append(line)
    
    if missing_packages:
        print(f"\n[提示] 检测到 {len(missing_packages)} 个缺失的依赖包，正在自动安装...")
        print(f"缺失的包: {', '.join([pkg.split('==')[0].split('>=')[0].split('<=')[0].strip() for pkg in missing_packages])}")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print("[成功] 依赖安装完成")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"[错误] 依赖安装失败: {e}")
            print(f"错误输出: {e.stderr}")
            print("\n请手动运行以下命令安装依赖:")
            print(f"    pip install -r {requirements_file}")
            return 1
    else:
        print(f"\n[成功] 所有依赖已安装 (共 {len(installed_packages)} 个包)")
        return 0


if __name__ == "__main__":
    sys.exit(main())

