import asyncio
import json
import time
from typing import AsyncGenerator
from agno.agent import Agent
from agno.models.openai import OpenAIChat


class ChatDispatchService:
    TIMEOUT_SECONDS = 30

    async def dispatch(self, agent: Agent, message: str,
                        session_id: str | None = None) -> AsyncGenerator[dict, None]:
        start_time = time.time()
        try:
            first_token = False
            response = agent.run(message, stream=True)
            for event in response:
                elapsed = time.time() - start_time
                if not first_token and elapsed > self.TIMEOUT_SECONDS:
                    yield {"type": "error", "content": "响应超时，请重试"}
                    return
                if hasattr(event, 'content') and event.content:
                    first_token = True
                    yield {"type": "token", "content": event.content}
            elapsed_ms = int((time.time() - start_time) * 1000)
            yield {"type": "done", "latency_ms": elapsed_ms}
        except Exception as e:
            yield {"type": "error", "content": f"对话出错: {str(e)}"}
