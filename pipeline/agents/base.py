"""Agent 基类与七个标准节点定义。

设计原则：
- 每个 Agent 只负责一个步骤
- 输入：上游产出文件路径
- 输出：产出内容字符串
- 禁止：读取非上游文件、访问其他节点状态、跨步回溯
"""

from __future__ import annotations

import abc
from pathlib import Path

from pipeline.core.file_protocol import Step


class BaseAgent(abc.ABC):
    """Agent 抽象基类

    子类只需：
    1. 设置 step 类属性
    2. 实现 _execute 方法（核心逻辑）
    3. 在 _execute 中调用 self._read_input(input_file) 读取上游内容
    """

    step: Step

    @property
    def agent_name(self) -> str:
        """Agent 中文名称"""
        return self.step.agent_name

    @property
    def step_index(self) -> int:
        """步骤编号 (1-7)"""
        return self.step.value

    def run(self, input_file: Path | None, output_file: Path, **kwargs) -> str:
        """标准执行入口

        Args:
            input_file: 上游产出文件路径 (第一步为 None)
            output_file: 输出文件路径 (用于记录，实际写入由调度器完成)

        Returns:
            产出内容字符串
        """
        upstream_content = self._read_input(input_file) if input_file else ""
        return self._execute(upstream_content, output_file, **kwargs)

    @abc.abstractmethod
    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        """子类实现核心逻辑"""
        ...

    @staticmethod
    def _read_input(filepath: Path) -> str:
        """读取上游产出文件"""
        if not filepath.exists():
            raise FileNotFoundError(f"上游文件不存在: {filepath}")
        return filepath.read_text(encoding="utf-8")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(step={self.step.value}, name={self.agent_name})>"


# ─── 七个标准 Agent ───────────────────────────────────────────


class ConsensusAgent(BaseAgent):
    """Agent 1: 共识生成

    职责：与用户深度交流，产出《目标锁定文档》
    输入：初始上下文（调度器传入）
    输出：目标锁定文档
    """

    step = Step.CONSENSUS

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="目标锁定文档",
            description="对用户需求进行深度澄清，消除歧义，锁定目标范围与边界条件。",
        )


class IntentTranslateAgent(BaseAgent):
    """Agent 2: 意图翻译

    职责：将目标锁定文档转化为无歧义的确定性需求 Spec
    输入：《目标锁定文档》
    输出：确定性需求 Spec
    """

    step = Step.INTENT

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="确定性需求 Spec",
            description="将用户模糊意图转化为可执行的、无歧义的需求规格说明。",
        )


class InnovationAgent(BaseAgent):
    """Agent 3: 创新策展

    职责：提供三种创新技术路径对比 + 最优推荐
    输入：《确定性需求 Spec》
    输出：方案对比表 + 推荐路径
    """

    step = Step.INNOVATION

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="方案对比表",
            description="提供多种创新实现路径，对比优劣，给出最优推荐。",
        )


class ArchitectAgent(BaseAgent):
    """Agent 4: 架构师

    职责：生成技术蓝图，含模块设计、接口定义、技术栈选型
    输入：方案对比表（选定方案）
    输出：工程蓝图
    """

    step = Step.ARCHITECT

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="工程蓝图",
            description="模块设计、接口定义、技术栈选型、数据流图。",
        )


class CoderAgent(BaseAgent):
    """Agent 5: 代码实现师

    职责：按照蓝图编写项目核心代码
    输入：工程蓝图
    输出：核心代码
    """

    step = Step.CODER

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="核心代码",
            description="严格按照工程蓝图落地产出核心代码文件。",
        )


class EngineerAgent(BaseAgent):
    """Agent 6: 工程落地师

    职责：代码规范化、项目配置、部署落地
    输入：核心代码
    输出：工程化项目
    """

    step = Step.ENGINEER

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="工程化项目",
            description="规范化整理、配置管理、部署文档。",
        )


class AuditorAgent(BaseAgent):
    """Agent 7: 代码审计师

    职责：语法/逻辑/结构审计（不查需求合规）
    输入：工程化项目
    输出：审计报告

    注意：审计范围严格限定于代码本身，不对照原始需求文档。
    需求合规由架构师→代码实现师间校验 + 人工闸门共同保证。
    """

    step = Step.AUDITOR

    def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
        return _agent_placeholder(
            agent_name=self.agent_name,
            step_index=self.step_index,
            upstream=upstream,
            output="审计报告",
            description="代码语法、逻辑、结构审查，不查需求合规。",
        )


# ─── 占位符生成 (框架用户替换为实际 LLM 调用逻辑) ──────────


def _agent_placeholder(
    agent_name: str,
    step_index: int,
    upstream: str,
    output: str,
    description: str,
) -> str:
    """生成标准占位内容

    框架用户将此函数替换为实际的 LLM API 调用。
    本框架不绑定任何特定 LLM 后端，保持后端无关性。
    """
    upstream_preview = upstream[:500] if upstream else "(无上游输入)"
    if len(upstream) > 500:
        upstream_preview += f"\n... (共 {len(upstream)} 字符，已截断预览)"

    return f"""# {output}

> 管线步骤: {step_index}/7 — {agent_name}
> 生成时间: 占位符 (请替换为实际 LLM 调用)

## 执行说明

{description}

## 上游输入摘要

{upstream_preview}

---

⚠️ **这是占位产出**。请在 BaseAgent._execute 中替换为实际 LLM API 调用逻辑。

```python
# 示例：替换 _execute 方法
def _execute(self, upstream: str, output_file: Path, **kwargs) -> str:
    response = your_llm_client.chat(
        system_prompt="你是一个{agent_name}...",
        user_input=upstream,
    )
    return response
```
"""
