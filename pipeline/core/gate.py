"""人工闸门 —— 三道固定断点，阻断幻觉级联传播。

三道闸门位置：
- 闸门一：共识生成完成后（确认目标锁定）
- 闸门二：意图翻译完成后（确认需求 Spec）
- 闸门三：创新策展完成后（确认技术方案）
"""

from __future__ import annotations

from enum import Enum

from pipeline.core.file_protocol import Step


class GatePosition(Enum):
    """闸门在管线中的位置"""

    AFTER_CONSENSUS = 1   # 共识生成 → 闸门一
    AFTER_INTENT = 2      # 意图翻译 → 闸门二
    AFTER_INNOVATION = 3  # 创新策展 → 闸门三


GATE_LABELS = {
    GatePosition.AFTER_CONSENSUS: "闸门一：目标锁定确认",
    GatePosition.AFTER_INTENT: "闸门二：需求 Spec 确认",
    GatePosition.AFTER_INNOVATION: "闸门三：技术方案确认",
}

GATE_PROMPTS = {
    GatePosition.AFTER_CONSENSUS: (
        "请确认《目标锁定文档》内容是否与您的意图一致。\n"
        "确认后将继续推进至意图翻译阶段。\n"
        "输入 'y' 或 'yes' 确认，输入 'n' 或 'no' 回退修改："
    ),
    GatePosition.AFTER_INTENT: (
        "请确认《确定性需求 Spec》内容是否准确完整。\n"
        "确认后将继续推进至创新策展阶段。\n"
        "输入 'y' 或 'yes' 确认，输入 'n' 或 'no' 回退修改："
    ),
    GatePosition.AFTER_INNOVATION: (
        "请确认《方案对比表》中选定的技术路径是否符合预期。\n"
        "确认后将继续推进至架构设计阶段。\n"
        "输入 'y' 或 'yes' 确认，输入 'n' 或 'no' 回退修改："
    ),
}

GATE_STEP_MAP = {
    Step.CONSENSUS: GatePosition.AFTER_CONSENSUS,
    Step.INTENT: GatePosition.AFTER_INTENT,
    Step.INNOVATION: GatePosition.AFTER_INNOVATION,
}


class GateResult:
    """闸门确认结果"""

    def __init__(self, approved: bool, reason: str = ""):
        self.approved = approved
        self.reason = reason


class Gate:
    """人工闸门控制器

    职责：
    1. 在三个关键节点暂停管线执行
    2. 展示当前产出摘要供人工审核
    3. 根据人工确认结果决定继续或回退

    设计原则：
    - 闸门是同步阻断器，不做任何自动决策
    - 只有明确的人类输入 'y'/'yes' 才能通过
    - 任何非确认输入视为拒绝
    """

    def __init__(self, interactive: bool = True, auto_approve: bool = False):
        """
        Args:
            interactive: 是否交互式等待用户输入
            auto_approve: 是否自动通过（仅用于测试/批处理，生产环境严禁开启）
        """
        self.interactive = interactive
        self.auto_approve = auto_approve

    def should_gate(self, step: Step) -> bool:
        """判断当前步骤完成后是否需要经过闸门"""
        return step in GATE_STEP_MAP

    def get_gate_position(self, step: Step) -> GatePosition | None:
        """获取当前步骤对应的闸门位置"""
        return GATE_STEP_MAP.get(step)

    def check(self, step: Step, output_file: str) -> GateResult:
        """在步骤完成后执行闸门检查

        Args:
            step: 当前步骤
            output_file: 当前步骤的产出文件路径

        Returns:
            GateResult: 确认结果
        """
        gate_pos = self.get_gate_position(step)
        if gate_pos is None:
            return GateResult(approved=True, reason="无需闸门检查")

        if self.auto_approve:
            return GateResult(approved=True, reason="自动通过")

        if not self.interactive:
            return GateResult(
                approved=False,
                reason=f"非交互模式无法通过 {GATE_LABELS[gate_pos]}",
            )

        # 展示产出文件摘要
        print(f"\n{'=' * 60}")
        print(f"  [闸门] {GATE_LABELS[gate_pos]}")
        print(f"{'=' * 60}")
        print(f"  产出文件: {output_file}")

        # 尝试展示文件前 10 行作为预览
        try:
            from pathlib import Path
            content = Path(output_file).read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            preview_lines = lines[:15]
            print(f"  文件预览 (前{len(preview_lines)}行):")
            print(f"  {'-' * 50}")
            for line in preview_lines:
                print(f"  | {line[:80]}")
            if len(lines) > 15:
                print(f"  | ... (共 {len(lines)} 行)")
            print(f"  {'-' * 50}")
        except Exception:
            print("  (无法读取文件预览)")

        print()
        result = self._prompt(GATE_PROMPTS[gate_pos])
        return result

    def _prompt(self, message: str) -> GateResult:
        """交互式确认提示"""
        while True:
            response = input(message).strip().lower()
            if response in ("y", "yes"):
                return GateResult(approved=True, reason="人工确认通过")
            elif response in ("n", "no"):
                return GateResult(approved=False, reason="人工拒绝")
            else:
                print("请输入 y/yes 确认 或 n/no 拒绝。")
