#!/usr/bin/env python3
"""
OpenEvolve Python包装器
自动在输入文件夹下运行演化，并将结果保存在openevolve_output目录中
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_required_files(input_dir: Path) -> bool:
    """检查必要的文件是否存在"""
    required_files = ["initial_program.py", "evaluator.py"]

    for file in required_files:
        if not (input_dir / file).exists():
            print(f"错误: 找不到 {file}")
            return False

    # 检查配置文件
    config_files = ["config.yaml", "config_default.yaml"]
    config_found = any((input_dir / cfg).exists() for cfg in config_files)

    if not config_found:
        print("错误: 找不到任何配置文件 (config.yaml 或 config_default.yaml)")
        return False

    return True


def get_config_file(input_dir: Path) -> str:
    """获取配置文件路径"""
    config_files = ["config.yaml", "config_default.yaml"]

    for cfg in config_files:
        cfg_path = input_dir / cfg
        if cfg_path.exists():
            return str(cfg_path)

    return ""


def run_evolution(input_dir: str, iterations: int, output_dir: str = None):
    """运行OpenEvolve演化过程"""
    input_path = Path(input_dir).absolute()

    # 检查文件
    if not check_required_files(input_path):
        sys.exit(1)

    # 获取配置文件
    config_file = get_config_file(input_path)

    # 设置输出目录
    if output_dir:
        output_path = output_dir
    else:
        output_path = str(input_path / "openevolve_output")

    # 检查API密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        print('例如: export DEEPSEEK_API_KEY="your-api-key"')
        sys.exit(1)

    print("=" * 50)
    print("OpenEvolve 函数最小化演化")
    print("=" * 50)
    print(f"输入文件夹: {input_path}")
    print(f"初始程序: {input_path / 'initial_program.py'}")
    print(f"评估器: {input_path / 'evaluator.py'}")
    print(f"配置文件: {config_file}")
    print(f"迭代次数: {iterations}")
    print(f"输出目录: {output_path}")
    print("=" * 50)

    # 构建OpenEvolve命令
    openevolve_path = Path(__file__).parent.parent.parent / "openevolve-run.py"

    cmd = [
        sys.executable,
        str(openevolve_path),
        str(input_path / "initial_program.py"),
        str(input_path / "evaluator.py"),
        "--config",
        config_file,
        "--iterations",
        str(iterations),
        "--output",
        output_path,
    ]

    print(f"运行命令: {' '.join(cmd)}")
    print("开始演化过程...")

    # 运行OpenEvolve
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)

        if result.stderr:
            print("标准错误输出:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"演化过程失败，退出码: {e.returncode}")
        print(f"标准输出: {e.stdout}")
        print(f"标准错误: {e.stderr}")
        sys.exit(1)

    print("=" * 50)
    print("演化完成!")
    print(f"结果保存在: {output_path}/")
    print()
    print("查看最佳程序:")
    print(f"  cat {output_path}/best/best_program_info.json")
    print()
    print("运行最佳程序:")
    print(f"  python {output_path}/best/best_program.py")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="OpenEvolve自动化运行脚本")
    parser.add_argument(
        "input_dir",
        nargs="?",
        default=".",
        help="输入文件夹路径（包含initial_program.py和evaluator.py）",
    )
    parser.add_argument(
        "--iterations", "-i", type=int, default=10, help="迭代次数（默认: 10）"
    )
    parser.add_argument(
        "--output", "-o", help="输出目录（默认: 输入文件夹下的openevolve_output）"
    )

    args = parser.parse_args()

    run_evolution(args.input_dir, args.iterations, args.output)


if __name__ == "__main__":
    main()
