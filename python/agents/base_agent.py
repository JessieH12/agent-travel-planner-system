"""
Agent 基类 —— 所有 Agent 继承此类，统一接口与生命周期。

设计思路 (面试考点):
  - 模板方法模式: run() 定义骨架流程，子类只需实现 execute()
  - 统一日志与错误处理
  - 支持 mock / 真实 LLM 两种模式
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from loguru import logger

from config.settings import settings
from models.schemas import TravelPlanState


class BaseAgent(ABC):
    """所有 Agent 的抽象基类。"""

    name: str = "BaseAgent"

    def __init__(self) -> None:
        self._llm_provider = settings.LLM_PROVIDER

    # ── 模板方法: 子类不要覆盖 ──────────────────────

    async def run(self, state: TravelPlanState) -> TravelPlanState:
        """执行 Agent 的完整生命周期: 校验 → 执行 → 日志。"""
        logger.info(f"[{self.name}] 开始执行...")
        try:
            state = await self.execute(state)
            logger.info(f"[{self.name}] 执行完成")
        except Exception as exc:
            logger.error(f"[{self.name}] 执行失败: {exc}")
            state.error_messages.append(f"{self.name}: {str(exc)}")
        return state

    # ── 子类必须实现 ────────────────────────────

    @abstractmethod
    async def execute(self, state: TravelPlanState) -> TravelPlanState:
        """核心业务逻辑，子类实现。"""
        ...

    # ── LLM 调用辅助 ─────────────────────────────

    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """调用 LLM，支持 mock 和真实两种模式。"""
        if self._llm_provider == "mock":
            return self._mock_llm(prompt)
        return await self._real_llm(prompt, system_prompt)

    def _mock_llm(self, prompt: str) -> str:
        """Mock LLM，返回固定结构化响应，用于零成本演示。"""
        return json.dumps({"response": f"[MOCK] {self.name} processed the request."})

    async def _real_llm(self, prompt: str, system_prompt: str = "") -> str:
        """调用真实 LLM API（MiniMax M2.7 / OpenAI 兼容接口）。"""
        import httpx

        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
        payload["messages"].append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.LLM_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
