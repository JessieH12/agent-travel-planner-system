"""
并行执行器 —— 同时运行多个 Agent，等待全部完成后合并结果。

面试考点:
  - 为什么并行？ Flight/Hotel/Activity 三个 Agent 互不依赖，串行执行浪费时间
  - asyncio.gather vs ThreadPoolExecutor: 纯 IO 密集用 asyncio，CPU 密集用线程
  - 错误处理: 某个 Agent 失败不影响其他 Agent，用 return_exceptions=True
  - 超时控制: asyncio.wait_for 限制单个 Agent 最大执行时间
"""

from __future__ import annotations

import asyncio
from typing import Sequence

from loguru import logger

from agents.base_agent import BaseAgent
from config.settings import settings
from models.schemas import TravelPlanState


class ParallelExecutor:
    """并行执行一组 Agent，将各自输出合并到同一 state 对象。"""

    def __init__(self, agents: Sequence[BaseAgent], timeout: int | None = None):
        self.agents = list(agents)
        self.timeout = timeout or settings.PARALLEL_TIMEOUT

    async def run(self, state: TravelPlanState) -> TravelPlanState:
        logger.info(f"[ParallelExecutor] 启动 {len(self.agents)} 个 Agent 并行执行...")

        tasks = [
            asyncio.wait_for(agent.run(state), timeout=self.timeout)
            for agent in self.agents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for agent, result in zip(self.agents, results):
            if isinstance(result, Exception):
                err_msg = f"{agent.name} 并行执行失败: {result}"
                logger.error(err_msg)
                state.error_messages.append(err_msg)

        logger.info("[ParallelExecutor] 并行执行完成")
        return state
