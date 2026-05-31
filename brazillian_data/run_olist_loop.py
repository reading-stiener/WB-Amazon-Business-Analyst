"""Run Olist SKILL.md agents in order, traced as a Weave call tree.

Each SKILL.md is loaded as the agent's system prompt and Claude is invoked
via claude-agent-sdk with file/bash tools so it can read the CSVs and write
the per-round output CSVs. Each agent invocation becomes a Weave op span
under a parent `olist.run_loop` trace.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

import weave
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent
AGENTS_DIR = REPO_ROOT / "agents"

DEFAULT_AGENTS: list[str] = [
    "olist-data-feature-agent",
    "olist-forecasting-agent",
]

AGENT_TASKS: dict[str, str] = {
    "olist-data-feature-agent": (
        "Build the monthly feature layer for round {round_id}. Read the Olist "
        "CSVs in the current directory ({cwd}). Write the required "
        "`monthly_sales_actuals.csv` to `outputs/runs/{round_id}/`. Use pandas "
        "via the Bash tool (python -c '...' or a small temp script). Follow "
        "your SKILL.md spec exactly for columns, grain, and quality checks. "
        "When finished, print a short JSON summary with output path, row counts "
        "per grain, and any caveats."
    ),
    "olist-forecasting-agent": (
        "Forecast monthly sales for round {round_id}. Read "
        "`outputs/runs/{round_id}/monthly_sales_actuals.csv`. Produce "
        "`outputs/runs/{round_id}/monthly_forecasts.csv` and "
        "`outputs/runs/{round_id}/forecast_backtest_results.csv` per your "
        "SKILL.md. Use trailing-average and seasonal-naive baselines. Use "
        "pandas via the Bash tool. When finished, print a short JSON summary "
        "with output paths, forecast horizons, WAPE/MAPE/bias, and confidence."
    ),
}


def load_skill(agent_name: str) -> str:
    path = AGENTS_DIR / agent_name / "SKILL.md"
    return path.read_text(encoding="utf-8")


@weave.op(name="olist.run_agent")
async def run_agent(agent_name: str, round_id: str, cwd: Path) -> dict:
    system_prompt = load_skill(agent_name)
    task = AGENT_TASKS[agent_name].format(round_id=round_id, cwd=str(cwd))

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        cwd=str(cwd),
        max_turns=40,
        model="claude-opus-4-7",
    )

    text_chunks: list[str] = []
    result_info: dict = {}
    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    text_chunks.append(block.text)
        elif isinstance(message, ResultMessage):
            result_info = {
                "duration_ms": getattr(message, "duration_ms", None),
                "num_turns": getattr(message, "num_turns", None),
                "total_cost_usd": getattr(message, "total_cost_usd", None),
                "is_error": getattr(message, "is_error", None),
            }

    return {
        "agent": agent_name,
        "round_id": round_id,
        "output": "".join(text_chunks),
        **result_info,
    }


@weave.op(name="olist.run_loop")
async def run_loop(agents: list[str], round_id: str, cwd: Path) -> list[dict]:
    results: list[dict] = []
    for agent_name in agents:
        print(f"\n>>> {agent_name} (round {round_id})", flush=True)
        result = await run_agent(agent_name, round_id, cwd)
        print(
            f"<<< {agent_name} done — turns={result.get('num_turns')} "
            f"cost=${result.get('total_cost_usd')}",
            flush=True,
        )
        results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Olist SKILL.md agents traced by Weave.")
    parser.add_argument("--round-id", default=None, help="Round identifier (default: timestamp).")
    parser.add_argument("--agents", nargs="+", default=DEFAULT_AGENTS, help="Agents to run in order.")
    parser.add_argument(
        "--weave-project",
        default=os.environ.get("WANDB_PROJECT", "amazon-ads-analyst"),
        help="Weave project (entity inferred from WANDB_ENTITY if set).",
    )
    args = parser.parse_args()

    round_id = args.round_id or datetime.now(timezone.utc).strftime("round-%Y%m%dT%H%M%SZ")
    entity = os.environ.get("WANDB_ENTITY")
    project = f"{entity}/{args.weave_project}" if entity else args.weave_project
    weave.init(project)

    results = asyncio.run(run_loop(args.agents, round_id, REPO_ROOT))
    out_dir = REPO_ROOT / "outputs" / "runs" / round_id
    print(f"\nAll done. Round outputs expected under: {out_dir}")
    for r in results:
        print(f" - {r['agent']}: {r.get('num_turns')} turns, ${r.get('total_cost_usd')}")


if __name__ == "__main__":
    main()
