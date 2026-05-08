"""文件协议引擎 —— 保证所有产出文件遵循统一命名与路径规范。

这是防幻觉的第一道防线：格式错误立即暴露，不会传递到下游。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Step(Enum):
    """管线七节点，按执行顺序排列"""

    CONSENSUS = 1        # 共识生成
    INTENT = 2           # 意图翻译
    INNOVATION = 3       # 创新策展
    ARCHITECT = 4        # 架构师
    CODER = 5            # 代码实现师
    ENGINEER = 6         # 工程落地师
    AUDITOR = 7          # 代码审计师

    @property
    def agent_name(self) -> str:
        """Agent 中文名，用于文件名生成"""
        _names = {
            Step.CONSENSUS: "共识生成",
            Step.INTENT: "意图翻译",
            Step.INNOVATION: "创新策展",
            Step.ARCHITECT: "架构师",
            Step.CODER: "代码实现师",
            Step.ENGINEER: "工程落地师",
            Step.AUDITOR: "代码审计师",
        }
        return _names[self]

    @property
    def step_prefix(self) -> str:
        """步骤编号前缀"""
        return f"{self.value:02d}"

    def next_step(self) -> Step | None:
        """返回下一个步骤，如果是最后一个则返回 None"""
        try:
            return Step(self.value + 1)
        except ValueError:
            return None

    def prev_step(self) -> Step | None:
        """返回上一个步骤，如果是第一个则返回 None"""
        try:
            return Step(self.value - 1)
        except ValueError:
            return None


@dataclass(frozen=True)
class OutputPath:
    """标准化输出路径结构"""

    project_id: str
    base_dir: Path

    @property
    def output_dir(self) -> Path:
        """项目专属输出目录"""
        return self.base_dir / ".codebuddy" / "outputs" / self.project_id

    def file_for(self, step: Step) -> Path:
        """生成符合规范的输出文件路径

        命名规范: {step}_{Agent名}_产出.md
        路径规范: .codebuddy/outputs/{project_id}/
        """
        filename = f"{step.step_prefix}_{step.agent_name}_产出.md"
        return self.output_dir / filename

    def ensure_dir(self) -> Path:
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir


class FileProtocol:
    """文件协议校验器

    职责：
    1. 校验输入文件是否存在且符合命名规范
    2. 确保输出目录结构正确
    3. 生成标准化文件路径
    """

    def __init__(self, project_id: str, workspace_root: str | Path | None = None):
        self.project_id = project_id
        self.workspace_root = Path(workspace_root or os.getcwd())
        self.output_path = OutputPath(
            project_id=project_id,
            base_dir=self.workspace_root,
        )

    def validate_input(self, step: Step) -> Path:
        """校验并返回当前步骤的输入文件路径

        规则：
        - 第一步 (CONSENSUS) 无上游输入，由调度器提供初始上下文
        - 后续步骤读取上一步的输出文件
        """
        if step == Step.CONSENSUS:
            return self.output_path.file_for(step)  # 用于写入

        prev = step.prev_step()
        if prev is None:
            raise ValueError(f"步骤 {step} 无法确定上游")

        input_file = self.output_path.file_for(prev)
        if not input_file.exists():
            raise FileNotFoundError(
                f"上游产出文件不存在: {input_file}\n"
                f"步骤 {prev.agent_name}（{prev.step_prefix}）尚未完成，"
                f"请先执行该步骤。"
            )
        return input_file

    def output_target(self, step: Step) -> Path:
        """返回当前步骤的输出文件路径"""
        self.output_path.ensure_dir()
        return self.output_path.file_for(step)

    def list_all_outputs(self) -> list[Path]:
        """列出该项目的所有产出文件"""
        pattern = self.output_path.output_dir.glob("*_产出.md")
        return sorted(pattern)
