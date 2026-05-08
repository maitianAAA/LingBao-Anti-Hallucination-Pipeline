"""主调度器 —— 极简管道：读文件 → 调 Agent → 写文件 → 查闸门"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol

from pipeline.core.file_protocol import FileProtocol, Step
from pipeline.core.gate import Gate

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class AgentInterface(Protocol):
    """Agent 最小接口协议

    每个 Agent 只需实现 run 方法：
    - 输入: 上游产出文件路径
    - 输出: 产出内容字符串
    - 不感知管线、不读取其他文件、不修改全局状态
    """

    @property
    def step(self) -> Step: ...

    def run(self, input_file: Path | None, output_file: Path, **kwargs) -> str: ...


class Scheduler:
    """7 节点接力管线调度器

    职责（仅三件事）：
    1. 读取上一节点的产出文件
    2. 调用当前 Agent 执行
    3. 将产出写入当前节点文件

    不做的：
    - 不解释 Agent 的输出
    - 不跨节点传递额外信息
    - 不回溯修改历史产出
    """

    def __init__(
        self,
        project_id: str,
        workspace_root: str | Path | None = None,
        gate: Gate | None = None,
    ):
        self.protocol = FileProtocol(project_id, workspace_root)
        self.gate = gate or Gate(interactive=True)
        self._agents: dict[Step, AgentInterface] = {}
        self._last_step: Step | None = None
        self._aborted = False

    @property
    def project_id(self) -> str:
        return self.protocol.project_id

    @property
    def output_dir(self) -> Path:
        return self.protocol.output_path.output_dir

    def register(self, agent: AgentInterface) -> None:
        """注册一个 Agent 到管线"""
        self._agents[agent.step] = agent

    def register_all(self, agents: list[AgentInterface]) -> None:
        """批量注册 Agent"""
        for agent in agents:
            self.register(agent)

    def run(self, *, start_from: Step | None = None, stop_at: Step | None = None) -> bool:
        """执行完整管线（或指定范围）

        Args:
            start_from: 从指定步骤开始（默认从第一步）
            stop_at: 执行到指定步骤停止（默认到最后一步）

        Returns:
            bool: 管线是否完整成功执行
        """
        start = start_from or Step.CONSENSUS
        stop = stop_at or Step.AUDITOR

        self.protocol.output_path.ensure_dir()

        steps = [s for s in Step if start.value <= s.value <= stop.value]
        if not steps:
            print("错误: 指定的步骤范围无效。")
            return False

        print(f"\n{'#' * 60}")
        print(f"#  防幻觉纵深防御管线 - 项目: {self.project_id}")
        print(f"#  执行范围: {start.agent_name}({start.value}) → {stop.agent_name}({stop.value})")
        print(f"#  输出目录: {self.output_dir}")
        print(f"{'#' * 60}\n")

        for step in steps:
            if self._aborted:
                print(f"\n⛔ 管线已中止，跳过步骤 {step.agent_name}")
                return False

            success = self._run_step(step)
            if not success:
                return False

        print(f"\n{'=' * 60}")
        print(f"  ✅ 管线执行完成")
        print(f"  产出目录: {self.output_dir}")
        print(f"{'=' * 60}\n")
        return True

    def _run_step(self, step: Step) -> bool:
        """执行单个步骤"""
        agent = self._agents.get(step)
        if agent is None:
            print(f"❌ 步骤 {step.agent_name}: 未注册 Agent，跳过。")
            return False

        # 1. 确定输入文件
        if step == Step.CONSENSUS:
            input_file = None
        else:
            try:
                input_file = self.protocol.validate_input(step)
            except FileNotFoundError as e:
                print(f"❌ 步骤 {step.agent_name}: {e}")
                return False

        # 2. 确定输出文件
        output_file = self.protocol.output_target(step)

        # 3. 执行
        print(f"\n▶ 步骤 {step.value}/7: {step.agent_name}")
        print(f"  输入: {input_file or '(初始上下文)'}")
        print(f"  输出: {output_file}")

        try:
            content = agent.run(
                input_file=input_file,
                output_file=output_file,
            )
        except Exception as e:
            print(f"❌ 步骤 {step.agent_name} 执行失败: {e}")
            self._aborted = True
            return False

        # 4. 写入产出文件
        output_file.write_text(content, encoding="utf-8")
        self._last_step = step
        print(f"  ✓ 产出已写入 ({len(content)} 字符)")

        # 5. 闸门检查
        if self.gate.should_gate(step):
            result = self.gate.check(step, str(output_file))
            if not result.approved:
                print(f"\n⛔ {result.reason}，管线暂停。")
                print(f"  当前产出文件: {output_file}")
                print(f"  修改后可通过 --start-from {step.value} 从此步骤恢复。")
                self._aborted = True
                return False
            print(f"  ✓ {result.reason}")

        return True

    def status(self) -> dict:
        """查询当前管线状态"""
        outputs = self.protocol.list_all_outputs()
        completed = {int(p.stem.split("_")[0]): p for p in outputs}
        return {
            "project_id": self.project_id,
            "output_dir": str(self.output_dir),
            "completed_steps": list(completed.keys()),
            "last_step": self._last_step.value if self._last_step else None,
            "aborted": self._aborted,
            "files": {s: str(p) for s, p in completed.items()},
        }
