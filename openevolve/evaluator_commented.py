import importlib.util
import json
import logging
import multiprocessing
import os
import signal
import sys
import tempfile
import time
import traceback
import types
from typing import Any, Dict, List, Optional, Tuple, Union

from .config import Config
from .evaluation_result import EvaluationResult

# 设置日志记录器
logger = logging.getLogger(__name__)

class Evaluator:
    """
    负责运行和评估生成的代码程序。
    
    主要功能：
    1. 在隔离的进程中运行代码（防止崩溃影响主程序）
    2. 监控运行时间，处理超时（防止死循环）
    3. 捕获运行结果和错误信息
    4. 计算综合得分
    """

    def __init__(self, config: Config, evaluator_path: str):
        """
        初始化评估器。

        Args:
            config: 全局配置对象
            evaluator_path: 用户提供的评估脚本路径（包含 evaluate() 函数的文件）
        """
        self.config = config
        self.evaluator_path = evaluator_path
        self.evaluator_module = self._load_module_from_path("user_evaluator", evaluator_path)
        
        # 验证用户脚本里有没有 evaluate 函数
        if not hasattr(self.evaluator_module, "evaluate"):
            raise ValueError(f"Evaluator script {evaluator_path} must define an 'evaluate' function")
            
        logger.info(f"Initialized evaluator with {evaluator_path}")

    def evaluate_program(self, program_code: str, program_id: str) -> EvaluationResult:
        """
        [核心入口] 评估一段生成的代码。

        Args:
            program_code: 要评估的 Python 代码字符串
            program_id: 代码的唯一 ID（用于日志和文件名）

        Returns:
            EvaluationResult 对象，包含分数、指标和错误信息
        """
        # 1. 如果代码为空，直接返回失败
        if not program_code or not program_code.strip():
            return EvaluationResult(
                score=float('-inf'), 
                metrics={"runs_successfully": 0.0},
                error="Empty program code"
            )

        # 2. 将代码写入临时文件
        # 我们不直接 exec 字符串，而是写文件，这样方便 import 和 traceback 报错定位
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(program_code)
            program_path = f.name

        try:
            # 3. 准备进程间通信 (Queue)
            # 用于子进程把评估结果传回给父进程
            result_queue = multiprocessing.Queue()
            
            # 4. 启动子进程进行评估 (沙箱隔离核心)
            # target=_run_evaluation_process 是真正干活的函数
            p = multiprocessing.Process(
                target=self._run_evaluation_process,
                args=(self.evaluator_path, program_path, result_queue, self.config.evaluator.timeout)
            )
            p.start()
            
            # 5. 等待子进程结束（带超时控制）
            # timeout 取自 config.yaml，比如 60秒
            p.join(timeout=self.config.evaluator.timeout)
            
            # 6. 如果超时了，强制杀掉子进程
            if p.is_alive():
                logger.warning(f"Evaluation timed out for program {program_id}")
                p.terminate()
                p.join() # 确保彻底清理
                return EvaluationResult(
                    score=float('-inf'),
                    metrics={"runs_successfully": 0.0},
                    error="Evaluation timed out"
                )
                
            # 7. 获取结果
            if result_queue.empty():
                # 队列空说明子进程崩溃了，没来得及发结果
                return EvaluationResult(
                    score=float('-inf'),
                    metrics={"runs_successfully": 0.0},
                    error="Evaluation process crashed or returned no result"
                )
            
            # 拿到原始结果字典
            raw_result = result_queue.get()
            
            # 8. 处理错误
            if "error" in raw_result and raw_result["error"]:
                return EvaluationResult(
                    score=float('-inf'),
                    metrics={"runs_successfully": 0.0},
                    error=raw_result["error"],
                    traceback=raw_result.get("traceback")
                )
                
            # 9. 成功！封装并返回结果
            metrics = raw_result.get("metrics", {})
            metrics["runs_successfully"] = 1.0 # 标记为运行成功
            
            # 计算综合得分 (Combined Score)
            combined_score = self._calculate_combined_score(metrics)
            
            return EvaluationResult(
                score=combined_score,
                metrics=metrics,
                artifacts=raw_result.get("artifacts", {})
            )

        except Exception as e:
            # 捕获评估器自身的 bug
            logger.error(f"Error during evaluation execution: {e}")
            return EvaluationResult(
                score=float('-inf'),
                metrics={"runs_successfully": 0.0},
                error=str(e),
                traceback=traceback.format_exc()
            )
        finally:
            # 清理临时文件
            if os.path.exists(program_path):
                try:
                    os.unlink(program_path)
                except:
                    pass

    @staticmethod
    def _run_evaluation_process(evaluator_path: str, program_path: str, queue: multiprocessing.Queue, timeout: int):
        """
        [子进程逻辑] 在隔离环境中运行用户代码。
        注意：这个函数是在全新的进程里跑的。
        """
        try:
            # 设置一些资源限制或环境变量（如果有的话）
            # ...

            # 1. 动态加载用户的 evaluator 脚本
            spec = importlib.util.spec_from_file_location("user_evaluator", evaluator_path)
            user_evaluator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(user_evaluator)
            
            # 2. 动态加载待测试的程序 (program_path)
            # 把它作为一个模块加载进来
            prog_spec = importlib.util.spec_from_file_location("candidate_program", program_path)
            candidate_program = importlib.util.module_from_spec(prog_spec)
            prog_spec.loader.exec_module(candidate_program)
            
            # 3. 运行评估！
            # 调用用户写的 evaluate() 函数，把候选程序模块传进去
            # 用户在 evaluate(model) 里会调用 model.run_algo() 之类的
            result = user_evaluator.evaluate(candidate_program)
            
            # 4. 规范化返回值
            # 用户可能只返回了一个数字，或者返回了一个字典
            output = {}
            if isinstance(result, (int, float)):
                output = {"metrics": {"score": float(result)}}
            elif isinstance(result, dict):
                output = {"metrics": result}
            elif hasattr(result, "metrics"): # 如果返回的是 EvaluationResult 对象
                output = {"metrics": result.metrics, "artifacts": result.artifacts}
            else:
                raise ValueError(f"Invalid return type from evaluate(): {type(result)}")
                
            # 5. 发送结果回主进程
            queue.put(output)

        except Exception as e:
            # 捕获运行时的所有错误（语法错误、运行时异常等）
            queue.put({
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    def _load_module_from_path(self, module_name: str, file_path: str) -> types.ModuleType:
        """辅助函数：从文件路径加载 Python 模块"""
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _calculate_combined_score(self, metrics: Dict[str, Any]) -> float:
        """
        计算综合得分。
        如果 evaluator 配置里指定了权重，就加权；否则默认取平均或取名为 'score' 的字段。
        """
        # 如果 metrics 里直接有 combined_score，就信它
        if "combined_score" in metrics:
            return float(metrics["combined_score"])
            
        # 如果有 score，就信它
        if "score" in metrics:
            return float(metrics["score"])
            
        # 否则，把所有是数字的指标取个平均值
        numeric_values = [v for k, v in metrics.items() if isinstance(v, (int, float)) and k != "runs_successfully"]
        if not numeric_values:
            return 0.0
            
        return sum(numeric_values) / len(numeric_values)
