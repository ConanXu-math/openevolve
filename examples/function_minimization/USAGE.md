# OpenEvolve 函数最小化示例使用说明

## 文件夹结构要求

```
function_minimization/
├── initial_program.py    # 初始程序（必须）
├── evaluator.py          # 评估器（必须）
├── config.yaml           # 配置文件（可选）
└── README.md             # 说明文档（可选）
```

## 运行方式

### 方式1：使用默认配置（推荐）

```bash
# 在输入文件夹中运行
cd /path/to/function_minimization
python ../../openevolve-run.py initial_program.py evaluator.py

# 结果将保存在：
# function_minimization/openevolve_output/
```

### 方式2：指定配置文件

```bash
python ../../openevolve-run.py initial_program.py evaluator.py --config config.yaml
```

### 方式3：自定义输出目录

```bash
# 将结果保存在指定目录
python ../../openevolve-run.py initial_program.py evaluator.py --output ./my_results

# 结果将保存在：
# function_minimization/my_results/
```

## 结果输出结构

```
openevolve_output/                    # 默认输出目录
├── best/                            # 最佳程序
│   ├── best_program.py             # 演化出的最佳算法
│   └── best_program_info.json      # 性能指标和元数据
├── logs/                           # 运行日志
│   └── openevolve_YYYYMMDD_HHMMSS.log
└── checkpoints/                    # 检查点（如果配置了）
    ├── checkpoint_5/
    ├── checkpoint_10/
    └── ...
```

## 环境变量设置

```bash
# 设置DeepSeek API密钥
export DEEPSEEK_API_KEY="your-api-key-here"

# 运行OpenEvolve
python ../../openevolve-run.py initial_program.py evaluator.py
```

## 快速测试

```bash
# 只运行3次迭代进行快速测试
python ../../openevolve-run.py initial_program.py evaluator.py --iterations 3

# 查看结果
cat openevolve_output/best/best_program_info.json
```

## 恢复演化

```bash
# 从检查点恢复
python ../../openevolve-run.py initial_program.py evaluator.py \
       --checkpoint openevolve_output/checkpoints/checkpoint_5
```

## 最佳实践

1. **保持输入文件夹整洁**：结果自动保存在`openevolve_output`子目录
2. **使用版本控制**：将初始程序、评估器和配置提交到Git
3. **记录实验**：每次运行后记录参数和结果
4. **定期备份检查点**：长期运行时定期保存检查点
