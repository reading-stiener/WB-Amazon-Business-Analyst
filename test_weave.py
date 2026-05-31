"""Smoke test: claude-agent-sdk call traced by W&B Weave."""

import asyncio
import os

import weave
from claude_agent_sdk import AssistantMessage, TextBlock, query
from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ.get("WANDB_PROJECT", "amazon-ads-analyst")
ENTITY = os.environ.get("WANDB_ENTITY")
WEAVE_PROJECT = f"{ENTITY}/{PROJECT}" if ENTITY else PROJECT


@weave.op()
async def ask_claude(prompt: str) -> str:
    chunks: list[str] = []
    async for message in query(prompt=prompt):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks)


async def main() -> None:
    weave.init(WEAVE_PROJECT)
    answer = await ask_claude(
        "Reply with exactly: weave trace ok. Nothing else."
    )
    print("Claude:", answer)


if __name__ == "__main__":
    asyncio.run(main())
