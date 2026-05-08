"""CLI 入口 —— 灵宝 AHP 命令行工具"""

from __future__ import annotations

import sys
from pathlib import Path

import click

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pipeline import __version__
from pipeline.agents.base import (
    ConsensusAgent,
    IntentTranslateAgent,
    InnovationAgent,
    ArchitectAgent,
    CoderAgent,
    EngineerAgent,
    AuditorAgent,
)
from pipeline.core.file_protocol import Step
from pipeline.core.gate import Gate
from pipeline.core.scheduler import Scheduler


def _build_scheduler(project_id: str, interactive: bool, auto: bool) -> Scheduler:
    """构建调度器实例"""
    gate = Gate(interactive=interactive, auto_approve=auto)
    scheduler = Scheduler(project_id=project_id, gate=gate)
    # 注册全部 7 个 Agent
    scheduler.register_all([
        ConsensusAgent(),
        IntentTranslateAgent(),
        InnovationAgent(),
        ArchitectAgent(),
        CoderAgent(),
        EngineerAgent(),
        AuditorAgent(),
    ])
    return scheduler


@click.group()
@click.version_option(version=__version__, prog_name="lingbao-ahp")
def main():
    """lingbao-ahp — 灵宝 AHP 反幻觉管线

    7 节点分布式接力管线，每节点只读上游产出，
    三道人工闸门阻断幻觉传播。
    """
    pass


@main.command()
@click.argument("project_id")
@click.option("--start-from", "-s", type=int, default=1, help="从指定步骤开始 (1-7)")
@click.option("--stop-at", "-e", type=int, default=7, help="执行到指定步骤 (1-7)")
@click.option("--auto", "-a", is_flag=True, help="自动通过所有闸门 (仅测试用)")
def run(project_id: str, start_from: int, stop_at: int, auto: bool):
    """运行完整管线 (或指定步骤范围)

    PROJECT_ID: 项目标识符，输出将写入 .codebuddy/outputs/{PROJECT_ID}/
    """
    if not (1 <= start_from <= 7) or not (1 <= stop_at <= 7):
        click.echo("错误: 步骤范围必须在 1-7 之间。", err=True)
        sys.exit(1)
    if start_from > stop_at:
        click.echo("错误: 起始步骤不能大于结束步骤。", err=True)
        sys.exit(1)

    scheduler = _build_scheduler(project_id, interactive=not auto, auto=auto)
    start_step = Step(start_from)
    stop_step = Step(stop_at)
    success = scheduler.run(start_from=start_step, stop_at=stop_step)
    sys.exit(0 if success else 1)


@main.command()
@click.argument("project_id")
def status(project_id: str):
    """查看管线运行状态"""
    scheduler = _build_scheduler(project_id, interactive=False, auto=True)
    info = scheduler.status()
    click.echo(f"\n项目: {info['project_id']}")
    click.echo(f"输出目录: {info['output_dir']}")
    click.echo(f"已完成步骤: {info['completed_steps'] or '无'}")
    click.echo(f"最后步骤: {info['last_step'] or '无'}")
    click.echo(f"是否中止: {info['aborted']}")

    if info["files"]:
        click.echo("\n产出文件:")
        for step_num, filepath in sorted(info["files"].items()):
            step = Step(step_num)
            size = Path(filepath).stat().st_size
            click.echo(f"  [{step_num}] {step.agent_name}: {filepath} ({size}B)")


@main.command()
@click.argument("project_id")
@click.option("--step", "-s", "step_num", type=int, required=True, help="步骤编号 (1-7)")
def resume(project_id: str, step_num: int):
    """从指定步骤恢复执行 (跳过已完成的步骤)"""
    if not (1 <= step_num <= 7):
        click.echo("错误: 步骤范围必须在 1-7 之间。", err=True)
        sys.exit(1)

    scheduler = _build_scheduler(project_id, interactive=True, auto=False)
    start_step = Step(step_num)
    success = scheduler.run(start_from=start_step)
    sys.exit(0 if success else 1)


@main.command()
def steps():
    """列出全部 7 个管线步骤"""
    click.echo("\n灵宝 AHP 反幻觉管线 — 7 步骤总览:\n")
    for step in Step:
        gate_mark = " [闸门]" if step in [Step.CONSENSUS, Step.INTENT, Step.INNOVATION] else ""
        upstream = step.prev_step()
        upstream_name = upstream.agent_name if upstream else "初始上下文"
        click.echo(f"  [{step.value}] {step.agent_name}{gate_mark}")
        click.echo(f"      输入: {upstream_name} -> 产出: {step.agent_name}文档")
    click.echo("\n  [闸门] = 人工闸门确认点\n")


if __name__ == "__main__":
    main()
