"""文档模型 —— 标准化产出数据结构"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pipeline.core.file_protocol import Step


@dataclass
class PipelineDocument:
    """管线产出文档标准模型"""

    step: Step
    project_id: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Path | None = None

    @property
    def agent_name(self) -> str:
        return self.step.agent_name

    @property
    def step_index(self) -> int:
        return self.step.value

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def line_count(self) -> int:
        return self.content.count("\n") + 1

    def save(self, output_dir: Path) -> Path:
        """保存到标准路径"""
        from pipeline.core.file_protocol import OutputPath
        op = OutputPath(project_id=self.project_id, base_dir=output_dir)
        filepath = op.file_for(self.step)
        op.ensure_dir()
        filepath.write_text(self.content, encoding="utf-8")
        self.file_path = filepath
        return filepath

    @classmethod
    def load(cls, filepath: Path, project_id: str, step: Step) -> PipelineDocument:
        """从文件加载"""
        content = filepath.read_text(encoding="utf-8")
        return cls(step=step, project_id=project_id, content=content, file_path=filepath)

    def __repr__(self) -> str:
        return (
            f"<PipelineDocument(step={self.step.value}, "
            f"agent={self.agent_name}, "
            f"chars={self.char_count})>"
        )


@dataclass
class PipelineRun:
    """一次完整的管线运行记录"""

    project_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    completed_steps: list[Step] = field(default_factory=list)
    failed_step: Step | None = None
    error_message: str = ""

    @property
    def is_complete(self) -> bool:
        return self.failed_step is None and len(self.completed_steps) == 7

    @property
    def duration_seconds(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
